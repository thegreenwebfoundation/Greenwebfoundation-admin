from .common import * # noqa
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration


ANYMAIL = {
    'MAILGUN_API_KEY': env('MAILGUN_API_KEY'),
    'MAILGUN_SENDER_DOMAIN': 'mg.thegreenwebfoundation.org',
    'MAILGUN_API_URL': 'https://api.eu.mailgun.net/v3'
}
EMAIL_BACKEND = 'anymail.backends.mailgun.EmailBackend'

ALLOWED_HOSTS = [
    'localhost',
    'thegreenwebfoundation.org',
    'admin.thegreenwebfoundation.org',
    'newadmin.thegreenwebfoundation.org',
    'staging-admin.thegreenwebfoundation.org',
]

# bucket name in GCP
PRESENTING_BUCKET = 'presenting_bucket_production'

# report when things asplode
sentry_dsn = os.environ.get("SENTRY_DSN", False)
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[DjangoIntegration()],

        # We assume that is a user is logged in, we want to be able
        # to see who is having a bad day, so we can contact them and
        # at least apologise about the broken site
        send_default_pii=True
    )
