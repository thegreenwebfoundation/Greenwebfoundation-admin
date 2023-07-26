from django.urls import reverse
from waffle.testutils import override_flag

import pytest


@pytest.mark.django_db
@override_flag("directory_listing", active=True)
def test_directory(client):
    """
    Confirm that the directory view is accessible when our flag is active
    """
    # when: the directory is accessed with an active flag
    res = client.get(reverse("directory-index"))

    # then: we see a successful response
    assert res.status_code == 200


@pytest.mark.django_db
@override_flag("directory_listing", active=True)
def test_ordering_of_providers_in_directory(client, hosting_provider_factory):
    """
    Check that providers are listed in order of the name of their
    country, to allow for grouping by country in templates
    """
    german_provider = hosting_provider_factory.create(country="DE", showonwebsite=True)
    danish_provider = hosting_provider_factory.create(country="DK", showonwebsite=True)

    # when: the directory is accessed with an active flag
    res = client.get(reverse("directory-index"))

    # then: we see a successful response
    assert res.status_code == 200

    # and: the providers are listed in order of their country name
    assert res.context["ordered_results"][0] == danish_provider
    assert res.context["ordered_results"][1] == german_provider
