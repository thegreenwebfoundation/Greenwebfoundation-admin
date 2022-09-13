import pytest
import logging

from apps.greencheck.microsoft_bucket_updater import MicrosoftBucketUpdater
from datetime import datetime

logger = logging.getLogger(__name__)


@pytest.mark.django_db
class TestMicrosoftBucketUpdater:
    def test_format_url_to_date(self):
        """
        Test formatting from url to date
        """
        updater = MicrosoftBucketUpdater()
        date = datetime.now().strftime("%Y%m%d")
        url = updater.url_prefix + date + updater.url_file_extension

        # Use formatting function
        updater_date = updater.format_url_to_date(url)

        assert date == updater_date

    def test_format_date_to_url(self):
        """
        Test formatting from date to url
        """
        updater = MicrosoftBucketUpdater()
        date = datetime.now()
        url = updater.url_prefix + date.strftime("%Y%m%d") + updater.url_file_extension

        # Use formatting function
        updater_url = updater.format_date_to_url(date)

        assert url == updater_url

    def test_search_dataset(self):
        """
        Test the searching function to track a active endpoint
        """
        updater = MicrosoftBucketUpdater()
        date = datetime.now()

        # Use dataset searcher from today
        dataset = updater.search_dataset(date)

        assert len(dataset) > 0

    # def test_update_bucket(self):
    # TODO: Implement this function
    # refresher = MicrosoftBucketUpdater()
    # refresher.update_bucket()
