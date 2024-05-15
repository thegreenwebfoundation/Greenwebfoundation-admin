"""
Django settings for Greenweb foundation project.

Generated by 'django-admin startproject' using Django.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""

import environ
import pathlib
from dramatiq import middleware as dramatiq_middleware

# Environ
ROOT = environ.Path(__file__) - 3
env = environ.Env(
    DEBUG=(bool, False),
    SECRET_KEY=(str, "some-key"),
    DJANGO_LOG_LEVEL=(str, "INFO"),
    # databases
    DATABASE_URL=(str, "sqlite:///db.sqlite3"),
    DATABASE_URL_READ_ONLY=(str, "sqlite:///db.sqlite3"),
    EXPLORER_TOKEN=(str, "some-token"),
    # object storage
    OBJECT_STORAGE_ENDPOINT=(str, "https://s3.nl-ams.scw.cloud"),
    OBJECT_STORAGE_REGION=(str, "nl-ams"),
    OBJECT_STORAGE_ACCESS_KEY_ID=(str, "xxxxxxxxxxxxxxxxxxxx"),
    OBJECT_STORAGE_SECRET_ACCESS_KEY=(
        str,
        "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    ),
    OBJECT_STORAGE_BUCKET_NAME=(str, "tgwf-green-domains-dev"),
    DOMAIN_SNAPSHOT_BUCKET=(str, "tgwf-green-domains-dev"),
    # basicauth for staging environments
    BASICAUTH_DISABLE=(bool, True),
    BASICAUTH_USER=(str, "staging_user"),
    BASICAUTH_PASSWORD=(str, "strong_password"),
    # Swagger API docs url
    API_URL=(str, "https://greenweb.localhost"),
    TRELLO_REGISTRATION_EMAIL_TO_BOARD_ADDRESS=(
        str,
        "mail-to-board@localhost",
    ),
    RABBITMQ_URL=(str, "amqp://USERNAME:PASSWORD@localhost:5672/"),
    # cloud providers updated on cronjobs
    # we use very high numbers to minimise chance of collision
    # with an actual provider id
    GOOGLE_PROVIDER_ID=(int, 10000001),
    GOOGLE_DATASET_ENDPOINT=(str, "https://www.gstatic.com/ipranges/cloud.json"),
    MICROSOFT_PROVIDER_ID=(int, 1000002),
    EQUINIX_PROVIDER_ID=(int, 1000003),
    EQUINIX_REMOTE_API_ENDPOINT=(str, "https://domain/link/to/file.txt"),
    AMAZON_PROVIDER_ID=(int, 1000004),
    AMAZON_REMOTE_API_ENDPOINT=(str, "https://domain/link/to/file.json"),
    MAXMIND_USER_ID=(str, "123456"),
    MAXMIND_LICENCE_KEY=(str, "xxxxxxxxxxxxxxxx"),
)

# in some cases we don't have a .env file to work from - the environment
# variables are provided via docker for example. So, we only try to load the
# .env file if it exists.
dotenv_file = pathlib.Path(ROOT) / ".env"
if dotenv_file.exists():
    environ.Env.read_env(".env")


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/dev/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ["thegreenwebfoundation.org"]


# Setting for django-registration
ACCOUNT_ACTIVATION_DAYS = 7  # One-week activation window

# Application definition
INSTALLED_APPS = [
    "django_dramatiq",
    # these need to go before django contrib, as described in the below docs
    # for DAL
    # https://django-autocomplete-light.readthedocs.io/en/master/install.html
    "dal",
    "dal_select2",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    # 3rd party
    "logentry_admin",
    "anymail",
    "django_extensions",
    "django_mysql",
    "django_registration",
    "rest_framework",
    "rest_framework.authtoken",
    "drf_yasg",
    "corsheaders",
    "taggit",
    "taggit_labels",
    "waffle",
    "django_filters",
    "django_admin_multiple_choice_list_filter",
    "formtools",
    "convenient_formsets",
    "file_resubmit",
    "django_countries",
    "guardian",
    # UI
    "tailwind",
    "crispy_forms",
    "crispy_tailwind",
    "widget_tweaks",
    # analysis
    "explorer",
    # tracking inbound API usage
    'drf_api_logger',
    # project specific
    "apps.theme",
    "apps.accounts",
    "apps.greencheck",
]

TAILWIND_APP_NAME = "apps.theme"
CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
CRISPY_TEMPLATE_PACK = "tailwind"


# Auth Mechanism
AUTH_USER_MODEL = "accounts.User"

LOGIN_REDIRECT_URL = "/provider-portal/"
LOGIN_URL = "/accounts/login"

# We need this to account for some providers that have numbers of IP
# ranges that are greater than the default limit in django.
# By setting this to None, we no longer check for the size of the form.
# This is not ideal, but it at least means some hosting providers can
# update their info while we rethink how people update IP range info.
# https://docs.djangoproject.com/en/4.0/ref/settings/#data-upload-max-number-fields
DATA_UPLOAD_MAX_NUMBER_FIELDS = None

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "waffle.middleware.WaffleMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    'drf_api_logger.middleware.api_logger_middleware.APILoggerMiddleware',
    # see the section below on BASICAUTH
    "basicauth.middleware.BasicAuthMiddleware",
]

DRF_API_LOGGER_DATABASE = True  # Default to False
legacy_api_views = ["legacy-greencheck-image", "legacy-greencheck-multi", "legacy-directory-detail"]
high_volume_views = ["green-domain-detail"]
debugger_api_views = ["djdt:history_sidebar"]
DRF_API_LOGGER_SKIP_URL_NAME = [ *legacy_api_views, *debugger_api_views, *high_volume_views]

# set up django-guardian as authentcation backend
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",  # this is a default value
    "guardian.backends.ObjectPermissionBackend",
]

# prevent django-guardian from patching the User model
# (recommended for custom User models)
GUARDIAN_MONKEY_PATCH = False

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    },
    "file_resubmit": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": "/tmp/file_resubmit/",
        "TIMEOUT": 600,  # 10 minutes
    },
}


# Basic auth for staging
# we include it, but leave it disabled,
# except on staging environments
# https://pypi.org/project/django-basicauth/
BASICAUTH_DISABLE = env("BASICAUTH_DISABLE")
BASICAUTH_USERS = {env("BASICAUTH_USER"): env("BASICAUTH_PASSWORD")}


ROOT_URLCONF = "greenweb.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": ["templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.theme.context_processors.sentry.sentry_info",
            ],
        },
    },
]

WSGI_APPLICATION = "greenweb.wsgi.application"


# Because our greencheck tables use TIMESTAMP, we can't use timezone aware dates
# https://docs.djangoproject.com/en/3.1/ref/databases/#timestamp-columns
USE_TZ = False

# Database
# https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {
    "default": env.db(),
    "read_only": env.db_url("DATABASE_URL_READ_ONLY"),
}
EXPLORER_CONNECTIONS = {"Default": "read_only"}
EXPLORER_DEFAULT_CONNECTION = "read_only"
EXPLORER_AUTORUN_QUERY_WITH_PARAMS = False
EXPLORER_PERMISSION_VIEW = lambda r: r.user.is_admin  # noqa
EXPLORER_PERMISSION_CHANGE = lambda r: r.user.is_admin  # noqa

DATABASES["default"]["OPTIONS"] = {
    # Tell MySQLdb to connect with 'utf8mb4' character set
    "charset": "utf8mb4",
}

DATABASES["read_only"]["OPTIONS"] = {
    # Tell MySQLdb to connect with 'utf8mb4' character set
    "charset": "utf8mb4",
}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
# only support API access with the sql explorer if we
# explicitly set the token
EXPLORER_TOKEN = env("EXPLORER_TOKEN")
if EXPLORER_TOKEN:
    EXPLORER_TOKEN_AUTH_ENABLED = True

# Geo IP database
GEOIP_PATH = pathlib.Path(ROOT) / "data" / "GeoLite2-City.mmdb"
GEOIP_PROVIDER_DOWNLOAD_URL = (
    "https://download.maxmind.com/geoip/databases/GeoLite2-City/download?suffix=tar.gz"
)
GEOIP_USER = env("MAXMIND_USER_ID")
GEOIP_PASSWORD = env("MAXMIND_LICENCE_KEY")

# Allow requests from any origin, but only make the API urls available
# CORS_URLS_REGEX = r"^/api/.*$"
CORS_ALLOW_ALL_ORIGINS = True


# Password validation
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-password-validators
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "apps.accounts.auth.LegacyBCrypt",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (  # noqa
            "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
        ),
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True

# Email settings
DEFAULT_FROM_EMAIL = "support@thegreenwebfoundation.org"

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
STATIC_URL = "/static/"

STATICFILES_DIRS = [
    "apps/theme/static",
]


# staticfiles it the name of the directory we collate files,
# so we can follow the convention of using static *inside django apps*
# for files we can to pick up with `collectstatic` commands.
STATIC_ROOT = ROOT("staticfiles")


# Media Files
MEDIA_ROOT = ROOT("media")
MEDIA_URL = "/media/"

# OBJECT STORAGE BUCKET
DOMAIN_SNAPSHOT_BUCKET = env("DOMAIN_SNAPSHOT_BUCKET")
OBJECT_STORAGE_ENDPOINT = env("OBJECT_STORAGE_ENDPOINT")
OBJECT_STORAGE_REGION = env("OBJECT_STORAGE_REGION")
OBJECT_STORAGE_ACCESS_KEY_ID = env("OBJECT_STORAGE_ACCESS_KEY_ID")
OBJECT_STORAGE_SECRET_ACCESS_KEY = env("OBJECT_STORAGE_SECRET_ACCESS_KEY")

# Importer variables
# Microsoft
MICROSOFT_PROVIDER_ID = env("MICROSOFT_PROVIDER_ID")

# Equinix
EQUINIX_PROVIDER_ID = env("EQUINIX_PROVIDER_ID")
EQUINIX_REMOTE_API_ENDPOINT = env("EQUINIX_REMOTE_API_ENDPOINT")

# Amazon
AMAZON_PROVIDER_ID = env("AMAZON_PROVIDER_ID")
AMAZON_REMOTE_API_ENDPOINT = env("AMAZON_REMOTE_API_ENDPOINT")

# Google
GOOGLE_PROVIDER_ID = env("GOOGLE_PROVIDER_ID")
GOOGLE_DATASET_ENDPOINT = env("GOOGLE_DATASET_ENDPOINT")


RABBITMQ_URL = env("RABBITMQ_URL")


REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.BasicAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
}

# Set the API URL, to force HTTPS when using the /api-docs API test
# https://drf-yasg.readthedocs.io/en/stable/openapi.html#custom-spec-base-url
API_URL = env("API_URL")


DRAMATIQ_BROKER = {
    "BROKER": "dramatiq.brokers.rabbitmq.RabbitmqBroker",
    "OPTIONS": {
        "url": RABBITMQ_URL,
    },  # noqa
    "MIDDLEWARE": [
        # remove until we are actually using it
        # "dramatiq.middleware.Prometheus"
        "dramatiq.middleware.AgeLimit",
        # use a longer timeout, as the default of 10 minutes means
        # that long running queries are aborted too early
        dramatiq_middleware.TimeLimit(time_limit=60 * 60 * 1000),
        "dramatiq.middleware.Callbacks",
        "dramatiq.middleware.Retries",
    ],
}

# For some jobs, we want workers dedicated to that queue only
# this is where we list them.
DRAMATIQ_EXTRA_QUEUES = {"stats": "stats"}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "root": {"handlers": ["console"], "level": "INFO"},
    "handlers": {
        "console": {
            "level": env("DJANGO_LOG_LEVEL"),
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "formatters": {
        "verbose": {
            "format": "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            "datefmt": "%d/%b/%Y %H:%M:%S",
        },
        "simple": {"format": "%(levelname)s %(message)s"},
    },
    "loggers": {
        "django.db.backends": {
            # uncomment to see all queries
            # 'level': 'DEBUG',
            "handlers": ["console"],
        }
    },
}

SITE_URL = "https://admin.thegreenwebfoundation.org"


TAGGIT_CASE_INSENSITIVE = True

TRELLO_REGISTRATION_EMAIL_TO_BOARD_ADDRESS = env(
    "TRELLO_REGISTRATION_EMAIL_TO_BOARD_ADDRESS"
)

INTERNAL_IPS = [
    "127.0.0.1",
]
