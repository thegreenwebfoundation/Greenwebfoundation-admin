import json
import logging

from apps.accounts.models import Hostingprovider, Datacenter
from django.views.decorators.cache import cache_page
from django_countries import countries
from rest_framework import response
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import AllowAny
from rest_framework_jsonp.renderers import JSONPRenderer

from ..domain_check import GreenDomainChecker
from ..models import Greencheck, GreenDomain
from .legacy_image_view import legacy_greencheck_image
from ..serializers import GreenDomainSerializer

logger = logging.getLogger(__name__)

checker = GreenDomainChecker()


def augmented_greencheck(check):
    """
    Return an augmented greencheck with necessary information to
    """
    if check.green == "yes":
        hosting_provider = Hostingprovider.objects.get(pk=check.hostingprovider)
        return {
            "date": str(check.date),
            "url": check.url,
            "hostingProviderId": check.hostingprovider,
            "hostingProviderUrl": hosting_provider.website,
            "hostingProviderName": hosting_provider.name,
            "green": True,
        }
    else:
        return {
            "date": str(check.date),
            "url": check.url,
            "hostingProviderId": False,
            "hostingProviderUrl": False,
            "hostingProviderName": False,
            "green": False,
        }


@api_view()
@permission_classes([AllowAny])
@renderer_classes([JSONPRenderer])
def latest_greenchecks(request):
    checks = Greencheck.objects.all()[:10]
    payload = []
    for check in checks:
        updated_check = augmented_greencheck(check)
        payload.append(updated_check)

    json_payload = json.dumps(payload)
    return response.Response(json_payload)


def fetch_providers_for_country(country_code):
    """
    Return all the country providers that should be visible
    as a list, with partners listed first, then in
    alphetical order.
    """
    # we need to order by partner, then alphabetical
    # order. Because the django ORM doesn't natively support
    # group by, and because we have hundreds of hosters for each
    # country, at a maximum we can get away with doing it in memory

    # because historically we have had a mix of empty strings and null
    # values, we need to use multiple excludes
    partner_providers = (
        Hostingprovider.objects.filter(country=country_code, showonwebsite=True)
        .exclude(partner__in=["", "None", None])
        .order_by("name")
    )
    regular_providers = (
        Hostingprovider.objects.filter(country=country_code, showonwebsite=True)
        .filter(partner__in=["", "None", None])
        .order_by("name")
    )
    # destructure the providers to build a new list,
    # with partner providers first, then regular providers
    providers = [*partner_providers, *regular_providers]

    return [
        {
            "iso": str(provider.country),
            "id": str(provider.id),
            "naam": provider.name,
            "website": provider.website,
            "partner": provider.partner,
        }
        for provider in providers
    ]


@api_view()
@permission_classes([AllowAny])
@renderer_classes([JSONPRenderer])
@cache_page(60 * 15)
def directory(request):
    """
    Return a JSON object keyed by countrycode, listing the providers
    we have for each country:
    """
    country_list = {}

    for country in countries:

        country_obj = {
            "iso": country.code,
            "tld": f".{country.code.lower()}",
            "countryname": country.name.upper(),
        }

        providers = fetch_providers_for_country(country.code)
        if providers:
            country_obj["providers"] = providers

        country_list[country.code] = country_obj

    return response.Response(country_list)


@api_view()
@permission_classes([AllowAny])
def directory_provider(self, id):
    """
    Return a JSON object representing the provider,
    what they do, and evidence supporting their
    sustainability claims
    """
    provider = Hostingprovider.objects.get(pk=id)
    datacenters = [dc.legacy_representation() for dc in provider.datacenter.all() if dc]

    # basic case, no datacenters or certificates
    provider_dict = {
        "id": str(provider.id),
        "naam": provider.name,
        "website": provider.website,
        "countrydomain": str(provider.country),
        "model": provider.model,
        "certurl": None,
        "valid_from": None,
        "valid_to": None,
        "mainenergytype": None,
        "energyprovider": None,
        "partner": provider.partner,
        "datacenters": datacenters,
    }
    return response.Response([provider_dict])


def tiered_lookup(domain: str) -> GreenDomain:
    """
    Try a lookup against the Greendomains cache table, then
    fallback to doing a slower, full lookup, returning a
    "Greendomain" lookup.
    """
    if res := GreenDomain.objects.filter(url__in=domain):
        return res.first()

    if res := checker.perform_full_lookup(domain):
        return res


@api_view()
@permission_classes([AllowAny])
def greencheck_multi(request, url_list: str):
    """
    Return a JSON object for the multichecks, like the API
    """
    urls = None

    try:
        urls = json.loads(url_list)
    except Exception:
        urls = []

    # fallback if the url list is not usable
    if urls is None:
        urls = []

    green_matches = []

    for domain in urls:
        # fetch Greendomains entry for every domain, doing
        # a full lookup if need be
        # TODO this is likely a prime candidate for doing
        # in parallel with newer async/await features in
        # Django 4 onwards
        if res := tiered_lookup(domain):
            green_matches.append(res)

    grey_urls = checker.grey_urls_only(urls, green_matches)

    checked_domains = checker.build_green_greylist(grey_urls, green_matches)

    serialised_domains = GreenDomainSerializer(checked_domains, many=True)

    data = serialised_domains.data

    result_dict = {}
    for url in urls:
        result = [datum for datum in data if datum["url"] == url][0]
        if result:
            result_dict[url] = result

    return response.Response(result_dict)

