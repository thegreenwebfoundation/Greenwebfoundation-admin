import waffle
from waffle.mixins import WaffleFlagMixin
from enum import Enum
from dal import autocomplete
from django.core.files.storage import DefaultStorage
from django.contrib import messages
from django.contrib.auth.models import Group
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sites.shortcuts import get_current_site
from django.db.models.query import QuerySet
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.encoding import force_text
from django.views.generic import UpdateView, DetailView, ListView
from django.views.generic.base import TemplateView
from django.shortcuts import redirect

from django_registration import signals
from django_registration.backends.activation.views import (
    ActivationView,
    RegistrationView,
)
from django_registration.exceptions import ActivationError
from django_registration.forms import (
    RegistrationFormCaseInsensitive,
    RegistrationFormUniqueEmail,
)
from django_registration import validators
from formtools.wizard.views import SessionWizardView

from .forms import (
    UserUpdateForm,
    OrgDetailsForm,
    LocationStepForm,
    ServicesForm,
    GreenEvidenceForm,
    NetworkFootprintForm,
    ConsentForm,
    PreviewForm,
)
from .models import User, ProviderRequest, ProviderRequestStatus, Hostingprovider
from .utils import send_email

import logging

logger = logging.getLogger(__name__)


class DashboardView(TemplateView):
    template_name = "dashboard.html"

    def get(self, request, *args, **kwargs):
        if waffle.flag_is_active(request, "dashboard"):
            return super().get(request, args, kwargs)
        else:
            return HttpResponseRedirect(reverse("provider_portal_home"))


class ProviderAutocompleteView(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # if a user is not authenticated don't show anything
        if not self.request.user.is_admin:
            return Hostingprovider.objects.none()

        # we only want active hosting providers to allocate to
        qs = Hostingprovider.objects.exclude(archived=True)

        if self.q:
            qs = qs.filter(name__istartswith=self.q)

        return qs


class RegistrationForm(RegistrationFormCaseInsensitive, RegistrationFormUniqueEmail):
    def __init__(self, *args, **kwargs):
        # override error message for unique email validation
        validators.DUPLICATE_EMAIL = mark_safe(
            """This email address is already in use.
            If this is your email address, you can <a href="/accounts/login/">log in</a>
            or do a <a href="/accounts/password_reset/">password reset</a>"""
        )
        super().__init__(*args, **kwargs)

    class Meta(RegistrationFormCaseInsensitive.Meta):
        model = User


class UserRegistrationView(RegistrationView):
    form_class = RegistrationForm
    email_body_template = "emails/activation.html"
    email_subject_template = "emails/activation_subject.txt"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["site_header"] = "Register a new user"
        return context

    def create_inactive_user(self, form):
        new_user = super().create_inactive_user(form)
        groups = Group.objects.filter(name__in=["hostingprovider", "datacenter"])

        for group in groups:
            new_user.groups.add(group)
        new_user.save()
        return new_user

    def get_success_url(self, user=None):
        """
        Return the URL to redirect to after successful redirection.
        """
        # stay on the same page
        return reverse("registration")

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            messages.success(
                request,
                "We've sent you an email. You need to follow the link in the email to confirm your address to finish signing up.",
            )
        return super().post(request, *args, **kwargs)


class UserActivationView(ActivationView):
    def get_success_url(self, user=None):
        return reverse("login")

    def get(self, *args, **kwargs):
        """
        We override the get method here because we only want to use the admin
        page and show the user a message.
        """
        try:
            activated_user = self.activate(*args, **kwargs)
        except ActivationError as e:
            error_message = e.message
        else:
            signals.user_activated.send(
                sender=self.__class__, user=activated_user, request=self.request
            )
            message = "Thanks, we've confirmed your email address. Now you can login with your username and password."
            messages.success(self.request, message)
            return HttpResponseRedirect(
                force_text(self.get_success_url(activated_user))
            )

        messages.error(self.request, error_message)
        return HttpResponseRedirect(force_text(self.get_success_url()))


class UserUpdateView(UpdateView):
    """
    A view for allowing users to edit basic details, and control
    notification settings
    """

    model = User
    form_class = UserUpdateForm

    def get(self, request, *args, **kwargs):
        """Handle GET requests: instantiate a blank version of the form."""
        return super().get(request, args, kwargs)


class ProviderPortalHomeView(LoginRequiredMixin, WaffleFlagMixin, ListView):
    """
    Home page of the Provider Portal:
    - used by external (non-staff) users to access a list of requests they submitted,
    - renders the list of pending verification requests as well as hosting providers on a HTML template,
    - requires the flag `provider_request` enabled for the user (otherwise returns 404).
    """

    template_name = "provider_portal/home.html"
    waffle_flag = "provider_request"
    model = ProviderRequest

    def get_queryset(self) -> "dict[str, QuerySet[ProviderRequest]]":
        """
        Returns a dictionary with 2 querysets:
        - unapproved ProviderRequests created by the user,
        - all HostingProviders assigned to the user
        """
        return {
            "requests": ProviderRequest.objects.filter(
                created_by=self.request.user
            ).exclude(status=ProviderRequestStatus.APPROVED),
            # TODO: change this when a user can have multiple providers assigned
            "providers": Hostingprovider.objects.filter(
                id__in=[self.request.user.hostingprovider_id]
            ),
        }


class ProviderRequestDetailView(LoginRequiredMixin, WaffleFlagMixin, DetailView):
    """
    Detail view for ProviderRequests:
    - used by external (non-staff) users to view a summary of a single request they submitted,
    - renders a single provider request on a HTML template,
    - requires the flag `provider_request` enabled for the user (otherwise returns 404).
    """  # noqa

    template_name = "provider_portal/request_detail.html"
    waffle_flag = "provider_request"
    model = ProviderRequest

    def get_queryset(self) -> "QuerySet[ProviderRequest]":
        return ProviderRequest.objects.filter(created_by=self.request.user)


class ProviderRegistrationView(LoginRequiredMixin, WaffleFlagMixin, SessionWizardView):
    """
    Multi-step registration for providers.
    - uses `django-formtools` SessionWizardView to display
      the multi-step form over multiple screens,
    - requires the flag `provider_request` enabled to access the view,

    """

    waffle_flag = "provider_request"
    file_storage = DefaultStorage()

    class Steps(Enum):
        """
        Pre-defined list of WizardView steps.
        WizardView uses numbers from 0 up, encoded as strings,
        to refer to specific steps.

        This Enum structure provides human-readable names
        for these steps.
        """

        ORG_DETAILS = "0"
        LOCATIONS = "1"
        SERVICES = "2"
        GREEN_EVIDENCE = "3"
        NETWORK_FOOTPRINT = "4"
        CONSENT = "5"
        PREVIEW = "6"

    FORMS = [
        (Steps.ORG_DETAILS.value, OrgDetailsForm),
        (Steps.LOCATIONS.value, LocationStepForm),
        (Steps.SERVICES.value, ServicesForm),
        (Steps.GREEN_EVIDENCE.value, GreenEvidenceForm),
        (Steps.NETWORK_FOOTPRINT.value, NetworkFootprintForm),
        (Steps.CONSENT.value, ConsentForm),
        (Steps.PREVIEW.value, PreviewForm),
    ]

    TEMPLATES = {
        Steps.ORG_DETAILS.value: "provider_registration/about_org.html",
        Steps.LOCATIONS.value: "provider_registration/locations.html",
        Steps.SERVICES.value: "provider_registration/services.html",
        Steps.GREEN_EVIDENCE.value: "provider_registration/evidence.html",
        Steps.NETWORK_FOOTPRINT.value: "provider_registration/network_footprint.html",
        Steps.CONSENT.value: "provider_registration/consent.html",
        Steps.PREVIEW.value: "provider_registration/preview.html",
    }

    def done(self, form_list, form_dict, **kwargs):
        """
        This method is called when all the forms are validated and submitted.

        Here we create objects for ProviderRequest and related models,
        based on the validated data from all Forms
        (passed as `form_dict`, where keys are the names of the steps).

        Because this method is called via POST request,
        it must return a redirect to a DetailView
        of a created ProviderRequest instance.

        Reference: https://django-formtools.readthedocs.io/en/latest/wizard.html#formtools.wizard.views.WizardView.done
        """  # noqa
        steps = ProviderRegistrationView.Steps

        # process ORG_DETAILS form: extract ProviderRequest and Location
        org_details_form = form_dict[steps.ORG_DETAILS.value]
        pr = org_details_form.save(commit=False)

        # process LOCATIONS form: extract locations
        locations_formset = form_dict[steps.LOCATIONS.value].forms["locations"]
        for location_form in locations_formset:
            location = location_form.save(commit=False)
            location.request = pr
            location.save()

        # process LOCATION: check if a bulk location import is needed
        extra_location_form = form_dict[steps.LOCATIONS.value].forms["extra"]
        location_import_required = extra_location_form.cleaned_data[
            "location_import_required"
        ]

        if location_import_required:
            pr.location_import_required = location_import_required

        # process SERVICES form: assign services to ProviderRequest
        services_form = form_dict[steps.SERVICES.value]
        pr.set_services_from_slugs(services_form.cleaned_data["services"])
        pr.created_by = self.request.user
        pr.save()

        # process GREEN_EVIDENCE form: link evidence to ProviderRequest
        evidence_forms = form_dict[steps.GREEN_EVIDENCE.value].forms
        for evidence_form in evidence_forms:
            evidence = evidence_form.save(commit=False)
            evidence.request = pr
            evidence.save()

        # process NETWORK_FOOTPRINT form: retrieve IP ranges
        ip_range_forms = form_dict[steps.NETWORK_FOOTPRINT.value].forms["ips"]
        for ip_range_form in ip_range_forms:
            ip_range = ip_range_form.save(commit=False)
            ip_range.request = pr
            ip_range.save()

        # process NETWORK_FOOTPRINT form: retrieve ASNs
        asn_forms = form_dict[steps.NETWORK_FOOTPRINT.value].forms["asns"]
        for asn_form in asn_forms:
            asn = asn_form.save(commit=False)
            asn.request = pr
            asn.save()

        # process NETWORK_FOOTPRINT form: retrieve network explanation
        # if network data is missing
        extra_network_form = form_dict[steps.NETWORK_FOOTPRINT.value]["extra"]
        network_explanation = extra_network_form.cleaned_data.get(
            "missing_network_explanation"
        )
        if network_explanation:
            pr.missing_network_explanation = network_explanation
            pr.save()

        # process CONSENT form
        consent_form = form_dict[steps.CONSENT.value]
        consent = consent_form.save(commit=False)
        consent.request = pr
        consent.save()

        # send an email notification to the author and green web staff
        self._send_notification_email(pr)

        # display a notification on the next page
        messages.success(
            self.request,
            """
            Thank you!

            Your verification request was submitted successfully.
            We are now reviewing your request - we'll be in touch.
            """,
        )
        return redirect(pr)

    def get_template_names(self):
        """
        Configures a template for each step of the Wizard.

        Reference: https://docs.djangoproject.com/en/3.2/ref/class-based-views/mixins-simple/#django.views.generic.base.TemplateResponseMixin.get_template_names
        """  # noqa
        return [self.TEMPLATES[self.steps.current]]

    def _get_data_for_preview(self):
        """
        Gathers cleaned data from all the steps preceding the PREVIEW step,
        so that it can be rendered on a single page.

        Returns a dictionary with key-value pairs:
        - key: name of the step,
        - value: an unbound form from that step, with initial data populated.

        _______
        Gotchas:

        - The forms are not bound: `form.data` will return {}.
        The initial data should be accessed through iterating over bound fields:
        `field.value for field in form`.

        - In case of a formset instance, accessing `formset.forms`
        will include extra (empty) forms as defined per formset factory.
        Templates should use `formset.initial_forms` for rendering non-empty forms.
        """
        preview_forms = {}
        # iterate over all forms without the last one (PREVIEW)
        for step, form in self.FORMS[:-1]:
            cleaned_data = self.get_cleaned_data_for_step(step)
            preview_forms[step] = form(initial=cleaned_data)

        return preview_forms

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form, **kwargs)
        if self.steps.current == self.Steps.PREVIEW.value:
            # inject data from all previous steps for rendering
            context["preview_forms"] = self._get_data_for_preview()
        return context

    def _send_notification_email(self, provider_request: ProviderRequest):
        """
        Send notification to support staff, and the user to acknowledge their submission.
        """  # noqa

        current_site = get_current_site(self.request)
        connection_scheme = self.request.scheme
        user = self.request.user
        request_path = reverse("provider_request_detail", args=[provider_request.id])

        link_to_verification_request = (
            f"{connection_scheme}://{current_site.domain}{request_path}"
        )

        ctx = {
            "org_name": provider_request.name,
            "status": provider_request.status,
            "link_to_verification_request": link_to_verification_request,
        }
        send_email(
            address=user.email,
            subject="Your verification request for the Green Web Database",
            context=ctx,
            template_html="emails/verification-request-notify.html",
            template_txt="emails/verification-request-notify.txt",
        )
