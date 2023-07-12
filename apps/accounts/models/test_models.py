import pytest

from apps.accounts.models.choices import ModelType
from apps.accounts import models as ac_models
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.core.files import base as dj_files

# TODO these hit the database, when they probably don't need to, and
#  this will make tests slow. If we can test that these objects are
#  valid another way we should - maybe checking at the field level,
#  or form level.

from django.contrib.auth import get_user_model

User = get_user_model()


class TestDatacenter:
    @pytest.mark.parametrize(
        "accounting_model",
        (
            "groeneenergie",
            "mixed",
            "compensatie",
        ),
    )
    def test_accepted_ways_to_model(self, hosting_provider, db, accounting_model):
        val, *_ = [
            choice for choice in ModelType.choices if choice[0] == accounting_model
        ]

        # if we don't have an allowed value this should throw an error
        hosting_provider.model = accounting_model
        hosting_provider.save()

        assert hosting_provider.model == accounting_model


class TestHostingProvider:
    @pytest.mark.parametrize(
        "accounting_model",
        (
            "groeneenergie",
            "mixed",
            "compensatie",
        ),
    )
    @pytest.mark.django_db
    def test_accepted_ways_to_model(
        self, datacenter, sample_hoster_user, accounting_model, hosting_provider
    ):
        hosting_provider.save()
        sample_hoster_user.hostingprovider = hosting_provider
        sample_hoster_user.save()

        val, *_ = [
            choice for choice in ModelType.choices if choice[0] == accounting_model
        ]

        # if we don't have an allowed value this should throw an error
        datacenter.model = accounting_model
        datacenter.save()

        assert datacenter.model == accounting_model


class TestHostingProviderEvidence:
    """
    Tests to check that we save files with scaleway
    """

    @pytest.mark.smoke_test
    def test_upload_hosting_evidence(self, db, sample_hoster_user, hosting_provider):
        """
        This exercises the API, so we can check that working with files
        when we use the object storage for file attachments instead of the
        server file system behaves as expected
        """

        now = timezone.now()
        one_year_from_now = now + relativedelta(years=1)

        evidence = ac_models.HostingProviderSupportingDocument(
            valid_from=now,
            valid_to=one_year_from_now,
            description="some description",
            title="Title",
            public=True,
        )
        evidence.save()
        hosting_provider.save()
        hosting_provider.hostingprovider_evidence.add(evidence)

        attachment_contents = b"text-content"
        evidence.attachment.save(
            "django_test.txt", dj_files.ContentFile(attachment_contents)
        )

        # can we read the file again?
        assert evidence.attachment.read() == attachment_contents


class TestUser:
    def test_create_user_has_password_and_legacy_password_set(
        self, db, hosting_provider
    ):
        """
        Test that when we create a user, we set both passwords, so we
        don't cause an unfortunate integrity error.

        NOTE: Once we stop using the old admin, this might no be needed
        """
        hosting_provider.save()

        new_user = User(
            username="keen_user",
            password="topSekrit",
            email="email@example.com",
            hostingprovider=hosting_provider,
        )

        new_user.save()
        # check that we have the correct columns updated

        # is the password set?
        assert new_user.legacy_password
        # and is it the same as the actual password we use
        # for logging in via django?
        assert new_user.legacy_password == new_user.password
