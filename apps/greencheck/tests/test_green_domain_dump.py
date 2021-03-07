import pathlib
from datetime import date
from io import StringIO

import pytest
import boto3  # noqa

from django.core.management import call_command
from django.utils import timezone
from sqlite_utils import Database

from ..models import Hostingprovider
from ..legacy_workers import SiteCheck
from ..management.commands.dump_green_domains import GreenDomainExporter
from ..models import GreencheckIp

from . import create_greendomain


def greencheck_sitecheck(
    domain, hosting_provider: Hostingprovider, green_ip: GreencheckIp
):
    return SiteCheck(
        url=domain,
        ip="192.30.252.153",
        data=True,
        green=True,
        hosting_provider_id=hosting_provider.id,
        checked_at=timezone.now(),
        match_type="ip",
        match_ip_range=green_ip.id,
        cached=True,
    )


@pytest.fixture
def cleared_test_bucket(object_storage_bucket):
    """
    Clears the test bucket. Adds a sanity check in case
    we're not using a bucket with test in the name
    (better than nothing)
    """
    assert "test" in object_storage_bucket.name
    [obj.delete() for obj in object_storage_bucket.objects.all() if obj]
    return object_storage_bucket


@pytest.fixture
def object_storage_bucket(settings):
    session = boto3.Session(region_name=settings.OBJECT_STORAGE_REGION)
    object_storage = session.resource(
        "s3",
        endpoint_url=settings.OBJECT_STORAGE_ENDPOINT,
        aws_access_key_id=settings.OBJECT_STORAGE_ACCESS_KEY_ID,
        aws_secret_access_key=settings.OBJECT_STORAGE_SECRET_ACCESS_KEY,
    )
    return object_storage.Bucket(settings.DOMAIN_SNAPSHOT_BUCKET)


@pytest.mark.only
class TestGreenDomainExporter:
    @pytest.mark.django_db(transaction=True)
    def test_dump_green_domains(self, hosting_provider, green_ip, settings):
        """
        Test that we can export to sqlite for use in other systems. By default pytest
        cases happen inside a transaction for speed, but for this we want to remove
        commit the transaction so the external commands in `db-to-sqlite` can see the
        test data.
        """
        # arrange
        exporter = GreenDomainExporter()

        sitecheck = greencheck_sitecheck("example.com", hosting_provider, green_ip)
        create_greendomain(hosting_provider, sitecheck)

        root = pathlib.Path(settings.ROOT)
        today = date.today()
        db_name = f"green_urls_{today}.db"
        conn_string = exporter.get_conn_string()

        # act
        exporter.export_to_sqlite(conn_string, db_name)
        sqlite_db = Database(db_name)

        # do we have our generated db?
        pathlib.Path.exists(root / db_name)

        # is the table there?
        assert "greendomain" in [table.name for table in sqlite_db.tables]

    def test_delete_files(self) -> None:
        exporter = GreenDomainExporter()

        # Deletion of missing files shouldn't error.
        assert exporter.delete_files("/tmp/non-existing.file") is None

        fpaths = []
        for fname in ("a.txt", "b.txt"):
            fpath = f"/tmp/{fname}"
            with open(fpath, "w") as fd:
                fd.write(fname)
            fpaths.append(fpath)

        assert exporter.delete_files(*fpaths) is None

        # The files must not exist after deletion.
        for fpath in fpaths:
            assert not pathlib.Path(fpath).exists(), fpath

        with pytest.raises(RuntimeError) as error:
            exporter.delete_files("/tmp")
        assert f'Failed to remove these files: "/tmp".' in str(error)


@pytest.mark.django_db
class TestDumpGreenDomainCommand:
    """

    """

    def test_handle(self):
        out = StringIO()
        err = StringIO()
        call_command("dump_green_domains", stdout=out, stderr=err)

        # silence is golden.
        assert not out.getvalue()
        assert not err.getvalue()

    @pytest.mark.object_storage
    @pytest.mark.smoke_test
    def test_handle_with_update(self, cleared_test_bucket, settings):
        """
        Check that this really has uploaded to the bucket we expect it to.
        """

        out = StringIO()
        call_command("dump_green_domains", upload=True, stdout=out)

        today = date.today()
        compressed_db_name = f"green_urls_{today}.db.gz"

        uploaded_files = [obj.key for obj in cleared_test_bucket.objects.all()]
        assert compressed_db_name in uploaded_files
