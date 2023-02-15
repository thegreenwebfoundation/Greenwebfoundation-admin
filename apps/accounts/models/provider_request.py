from django.db import models, IntegrityError, transaction
from django.urls import reverse
from django.conf import settings
from django.core.exceptions import ValidationError

from django_countries.fields import CountryField
from taggit.managers import TaggableManager
from taggit.models import Tag
from datetime import date, timedelta

from apps.greencheck.models import IpAddressField, GreencheckASN, GreencheckIp
from apps.greencheck.validators import validate_ip_range
from model_utils.models import TimeStampedModel
from typing import Iterable, Tuple, List
from .hosting import Hostingprovider, HostingProviderSupportingDocument


class ProviderRequestStatus(models.TextChoices):
    """
    Status of the ProviderRequest, exposed to both: end users and staff.
    Some status change (PENDING_REVIEW -> ACCEPTED) will be later used to trigger
    automatic creation of the different resources in the system.

    Meaning of each value:
    - PENDING_REVIEW: GWF staff needs to verify the request
    - ACCEPTED: GWF staff accepted the request
    - REJECTED: GWF staff rejected the request (completely)
    - OPEN: GWF staff requested some changes from the provider
    """

    PENDING_REVIEW = "Pending review"
    ACCEPTED = "Accepted"
    REJECTED = "Rejected"
    OPEN = "Open"


class ProviderRequest(TimeStampedModel):
    """
    Model representing the input data
    as submitted by the provider to our system,
    when they want to include their information into our dataset.

    """

    name = models.CharField(max_length=255)
    website = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(choices=ProviderRequestStatus.choices, max_length=255)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True
    )
    authorised_by_org = models.BooleanField()
    services = TaggableManager(
        verbose_name="Services offered",
        help_text=(
            "Click the services that your organisation offers. These will be listed in"
            " the green web directory."
        ),
        blank=True,
    )

    def __str__(self) -> str:
        return f"{self.name}"

    def get_absolute_url(self) -> str:
        return reverse("provider_request_detail", args=[str(self.id)])

    @staticmethod
    def from_kwargs(**kwargs) -> "ProviderRequest":
        """
        Given arbitrary kwargs, construct a new ProviderRequest object.
        No validation is performed on the created object.
        """
        pr_keys = [
            "name",
            "website",
            "description",
            "status",
            "created_by",
            "authorised_by_org",
        ]
        pr_data = {key: value for (key, value) in kwargs.items() if key in pr_keys}
        pr_data.setdefault("status", ProviderRequestStatus.OPEN.value)
        return ProviderRequest.objects.create(**pr_data)

    def set_services_from_slugs(self, service_slugs: Iterable[str]) -> None:
        """
        Given list of service slugs (corresponding to Tag slugs)
        apply matching services to the ProviderRequest object
        """
        services = Tag.objects.filter(slug__in=service_slugs)
        self.services.set(services)

    @classmethod
    def get_service_choices(cls) -> List[Tuple[int, str]]:
        """
        Returns a list of available services (implemented in the Tag model)
        in a format expected by ChoiceField
        """
        return [(tag.slug, tag.name) for tag in Tag.objects.all()]

    @transaction.atomic
    def approve(self) -> Hostingprovider:
        """
        Create a new Hostingprovider and underlying objects.

        This is
        """
        # Fail when user is already attached to an existing Hostingprovider
        # TODO: change this once User can be attached to multiple Hostingproviders
        user = self.created_by
        if user.hostingprovider:
            raise ValueError(
                f"Failed to approve the request `{self}` because the user '{user}' "
                f"is already assigned to a hosting provider '{user.hostingprovider}'"
            )

        # Temporarily use only the first location
        # TODO: change this once Hostingprovider model has multiple locations attached
        first_location = self.providerrequestlocation_set.first()

        hp = Hostingprovider.objects.create(
            name=self.name,
            # set the first location from the list
            country=first_location.country,
            city=first_location.city,
            services=self.services,
            website=self.website,
        )
        # TODO: test whether user.hostingprovider needs to be manually reverted in case of a rollback
        user.hostingprovider = hp
        user.save()

        for asn in self.providerrequestasn_set.all():
            try:
                GreencheckASN.objects.create(active=True, asn=asn, hostingprovider=hp)
            except IntegrityError as e:
                raise ValueError(
                    f"Failed to approve the request `{self}` because the ASN '{asn}' already exists in the database"
                ) from e

        for ip_range in self.providerrequestiprange_set.all():
            GreencheckIp.objects.create(
                active=True,
                ip_start=ip_range.start,
                ip_end=ip_range.end,
                hostingprovider=hp,
            )

        for evidence in self.providerrequestevidence_set.all():
            HostingProviderSupportingDocument.objects.create(
                hostingprovider=hp,
                title=evidence.title,
                attachment=evidence.file,
                url=evidence.link,
                description=evidence.description,
                # evidence is valid for 1 year from the time the request is approved
                valid_from=date.today(),
                valid_to=date.today() + timedelta(days=365),
                public=evidence.public,
            )

        return hp


class ProviderRequestLocation(models.Model):
    """
    Each ProviderRequest may be connected to many ProviderRequestLocations,
    in which the new provider offers services.
    """

    name = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255)
    country = CountryField()
    request = models.ForeignKey(ProviderRequest, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.request.name} | { self.name } {self.country.name}/{self.city}"


class ProviderRequestASN(models.Model):
    """
    ASN number that is operated by the provider.
    """

    asn = models.IntegerField()
    request = models.ForeignKey(ProviderRequest, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.asn}"


class ProviderRequestIPRange(models.Model):
    """
    IP range that is operated by the provider.
    """

    start = IpAddressField()
    end = IpAddressField()
    request = models.ForeignKey(ProviderRequest, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.start} - {self.end}"

    def clean(self) -> None:
        """
        Validates an IP range.

        Checking if values are not falsy is a workaround
        for a surprising ModelForm implementation detail:

        ModelForm connected to this Model executes Model.full_clean
        with "None" values in case the values were considered invalid
        according to the ModelForm validation logic.
        """
        if self.start and self.end:
            validate_ip_range(self.start, self.end)


class EvidenceType(models.TextChoices):
    """
    Type of the supporting evidence, that certifies that green energy is used
    """

    ANNUAL_REPORT = "Annual report"
    WEB_PAGE = "Web page"
    CERTIFICATE = "Certificate"
    OTHER = "Other"


class ProviderRequestEvidence(models.Model):
    """
    Document that certifies that green energy is used by the provider.
    A single evidence is either a web link or a file.
    """

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    link = models.URLField(null=True, blank=True)
    file = models.FileField(null=True, blank=True)
    type = models.CharField(choices=EvidenceType.choices, max_length=255)
    public = models.BooleanField(default=True)
    request = models.ForeignKey(ProviderRequest, on_delete=models.CASCADE)

    def __str__(self) -> str:
        name = self.link or self.file.name
        long_name = f"{name}: {self.title}"
        if self.public:
            return f"{long_name} (public)"
        return f"{long_name} (private)"

    def clean(self) -> None:
        reason = "Provide a link OR a file for this evidence"
        if self.link is None and not bool(self.file):
            raise ValidationError(f"{reason}, you haven't submitted either.")
        if self.link and bool(self.file):
            raise ValidationError(
                f"{reason}, you've attempted to submit both - we've removed the file"
                " for now."
            )


class ProviderRequestConsent(models.Model):
    """
    Set of agreements that the user consents to (or not) to by submitting the request.
    """

    data_processing_opt_in = models.BooleanField(default=False)
    newsletter_opt_in = models.BooleanField(default=False)
    request = models.ForeignKey(ProviderRequest, on_delete=models.CASCADE)

    def __str__(self) -> str:
        data_processing = f"Data processing: {self.data_processing_opt_in}"
        newsletter = f"Newsletter signup: {self.newsletter_opt_in}"
        return f"{data_processing}, {newsletter}"
