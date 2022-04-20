"""
Django settings for privaterelay project.

Generated by 'django-admin startproject' using Django 2.2.2.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import ipaddress
import os, sys
from datetime import datetime

from decouple import config
import markus
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import ignore_logger
from hashlib import sha512
import base64

from django.conf import settings

import dj_database_url

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# defaulting to blank to be production-broken by default
SECRET_KEY = config('SECRET_KEY', None, cast=str)

ON_HEROKU = config('ON_HEROKU', False, cast=bool)
DEBUG = config('DEBUG', False, cast=bool)
if DEBUG:
    INTERNAL_IPS = config(
        'DJANGO_INTERNAL_IPS', default=[]
    )

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_HOST = config('DJANGO_SECURE_SSL_HOST', None)
SECURE_SSL_REDIRECT = config('DJANGO_SECURE_SSL_REDIRECT', False)
SECURE_REDIRECT_EXEMPT = [
    r'^__version__',
    r'^__heartbeat__',
    r'^__lbheartbeat__',
]
SECURE_HSTS_SECONDS = config('DJANGO_SECURE_HSTS_SECONDS', None)
SECURE_CONTENT_TYPE_NOSNIFF = config('DJANGO_SECURE_CONTENT_TYPE_NOSNIFF',
                                     True)
SECURE_BROWSER_XSS_FILTER = config('DJANGO_SECURE_BROWSER_XSS_FILTER', True)
SESSION_COOKIE_SECURE = config(
    'DJANGO_SESSION_COOKIE_SECURE', False, cast=bool
)
# maps fxa profile hosts to respective avatar hosts for CSP
AVATAR_IMG_SRC_MAP = {
    'https://profile.stage.mozaws.net/v1':      [
        'mozillausercontent.com',
        'https://profile.stage.mozaws.net',
    ],
    'https://profile.accounts.firefox.com/v1':  [
        'firefoxusercontent.com',
        'https://profile.accounts.firefox.com',
    ],
}
AVATAR_IMG_SRC = AVATAR_IMG_SRC_MAP[config(
    'FXA_PROFILE_ENDPOINT', 'https://profile.accounts.firefox.com/v1'
)]
CSP_CONNECT_SRC = (
    "'self'",
    'https://www.google-analytics.com/',
    'https://accounts.firefox.com',
    'https://location.services.mozilla.com',
)
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = (
    "'self'",
    'https://www.google-analytics.com/',
)
# TODO: Add with silk
# if settings.DEBUG:
#     CSP_SCRIPT_SRC += ("'unsafe-inline'",)

csp_style_values = ["'self'"]
# Next.js dynamically inserts the relevant styles when switching pages,
# by injecting them as inline styles. We need to explicitly allow those styles
# in our Content Security Policy.
if (DEBUG):
    # When running locally, styles might get refreshed while the server is
    # running, so their hashes would get oudated. Hence, we just allow all of
    # them.
    csp_style_values.append("'unsafe-inline'")
else:
    # When running in production, we want to disallow inline styles that are
    # not set by us, so we use an explicit allowlist with the hashes of the
    # styles generated by Next.js.
    for root, dirs, files in os.walk("frontend/out/_next/static/css/"):
        for name in files:
            file_name = (os.path.join(root, name))
            hasher = sha512()
            with open(str(file_name), 'rb') as f:
                while True:
                    data = f.read()
                    if not data:
                        break
                    hasher.update(data)
            hash = base64.b64encode(hasher.digest()).decode('utf-8')
            csp_style_values.append("'sha512-%s'" % hash)

CSP_STYLE_SRC = tuple(csp_style_values)
# TODO: Add with silk
# if settings.DEBUG:
#     CSP_STYLE_SRC += ("'unsafe-inline'",)

CSP_IMG_SRC = ["'self'"] + AVATAR_IMG_SRC
REFERRER_POLICY = 'strict-origin-when-cross-origin'

ALLOWED_HOSTS = []
DJANGO_ALLOWED_HOST = config('DJANGO_ALLOWED_HOST', None)
if DJANGO_ALLOWED_HOST:
    ALLOWED_HOSTS += DJANGO_ALLOWED_HOST.split(',')
DJANGO_ALLOWED_SUBNET = config('DJANGO_ALLOWED_SUBNET', None)
if DJANGO_ALLOWED_SUBNET:
    ALLOWED_HOSTS += [
        str(ip) for ip in ipaddress.IPv4Network(DJANGO_ALLOWED_SUBNET)
    ]


# Get our backing resource configs to check if we should install the app
ADMIN_ENABLED = config('ADMIN_ENABLED', False, cast=bool)


AWS_REGION = config('AWS_REGION', None)
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID', None)
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY', None)
AWS_SNS_TOPIC = config('AWS_SNS_TOPIC', None)
AWS_SNS_KEY_CACHE = config('AWS_SNS_KEY_CACHE', 'default')
AWS_SES_CONFIGSET = config('AWS_SES_CONFIGSET', None)
AWS_SQS_EMAIL_QUEUE_URL = config('AWS_SQS_EMAIL_QUEUE_URL', None)
AWS_SQS_EMAIL_DLQ_URL = config('AWS_SQS_EMAIL_DLQ_URL', None)

# Dead-Letter Queue (DLQ) for SNS push subscription
AWS_SQS_QUEUE_URL = config('AWS_SQS_QUEUE_URL', None)

RELAY_FROM_ADDRESS = config('RELAY_FROM_ADDRESS', None)
SITE_ORIGIN = config('SITE_ORIGIN', None)
GOOGLE_ANALYTICS_ID = config('GOOGLE_ANALYTICS_ID', None)
INCLUDE_VPN_BANNER = config('INCLUDE_VPN_BANNER', False, cast=bool)
RECRUITMENT_BANNER_LINK = config('RECRUITMENT_BANNER_LINK', None)
RECRUITMENT_BANNER_TEXT = config('RECRUITMENT_BANNER_TEXT', None)
RECRUITMENT_EMAIL_BANNER_TEXT = config('RECRUITMENT_EMAIL_BANNER_TEXT', None)
RECRUITMENT_EMAIL_BANNER_LINK = config('RECRUITMENT_EMAIL_BANNER_LINK', None)
SERVE_REACT = config('SERVE_REACT', False, cast=bool)

TWILIO_ACCOUNT_SID = config('TWILIO_ACCOUNT_SID', None)
TWILIO_AUTH_TOKEN = config('TWILIO_AUTH_TOKEN', None)

STATSD_ENABLED = config('DJANGO_STATSD_ENABLED', False, cast=bool)
STATSD_HOST = config('DJANGO_STATSD_HOST', '127.0.0.1')
STATSD_PORT = config('DJANGO_STATSD_PORT', '8125')
STATSD_PREFIX = config('DJANGO_STATSD_PREFIX', 'fx-private-relay')

SERVE_ADDON = config('SERVE_ADDON', None)

# Application definition
INSTALLED_APPS = [
    'whitenoise.runserver_nostatic',
    'django_gulp',
    'django.contrib.staticfiles',

    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.sites',

    'django_filters',
    'django_ftl.apps.DjangoFtlConfig',

    'dockerflow.django',

    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.fxa',

    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',

    'waffle',

    'privaterelay.apps.PrivateRelayConfig',
]

if DEBUG:
    INSTALLED_APPS += [
        'debug_toolbar',
        'drf_yasg',
#        'silk',
    ]

if ADMIN_ENABLED:
    INSTALLED_APPS += [
        'django.contrib.admin',
    ]

if AWS_SES_CONFIGSET and AWS_SNS_TOPIC:
    INSTALLED_APPS += [
        'emails.apps.EmailsConfig',
    ]

if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    INSTALLED_APPS += [
        'phones.apps.PhonesConfig',
    ]


# statsd middleware has to be first to catch errors in everything else
def _get_initial_middleware():
    if STATSD_ENABLED:
        return [
            'privaterelay.middleware.ResponseMetrics',
        ]
    return []

MIDDLEWARE = _get_initial_middleware()

if DEBUG:
    MIDDLEWARE += [
#        'silk.middleware.SilkyMiddleware',
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    ]

MIDDLEWARE += [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'privaterelay.middleware.RedirectRootIfLoggedIn',
    'csp.middleware.CSPMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    "django.middleware.locale.LocaleMiddleware",
    "django_ftl.middleware.activate_from_request_language_code",

    'django_referrer_policy.middleware.ReferrerPolicyMiddleware',
    'dockerflow.django.middleware.DockerflowMiddleware',

    'waffle.middleware.WaffleMiddleware',

    'privaterelay.middleware.FxAToRequest',
    'privaterelay.middleware.AddDetectedCountryToResponseHeaders',
    'privaterelay.middleware.StoreFirstVisit',
]

ROOT_URLCONF = 'privaterelay.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'privaterelay', 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',

                'emails.context_processors.relay_from_domain',
                'privaterelay.context_processors.django_settings',
                'privaterelay.context_processors.common',
            ],
        },
    },
]

RELAY_FIREFOX_DOMAIN = config('RELAY_FIREFOX_DOMAIN', 'relay.firefox.com', cast=str)
MOZMAIL_DOMAIN = config('MOZMAIL_DOMAIN', 'mozmail.com', cast=str)
MAX_NUM_FREE_ALIASES = config('MAX_NUM_FREE_ALIASES', 5, cast=int)
PREMIUM_PROD_ID = config('PREMIUM_PROD_ID', '', cast=str)
PREMIUM_PRICE_ID_OVERRIDE = config('PREMIUM_PRICE_ID_OVERRIDE', '', cast=str)
PREMIUM_PLAN_ID_MATRIX = {
    "chf": {
        "de": {
            "id": "price_1JmRM0JNcmPzuWtRzCJ2LQHP",
            "price": "CHF 1.00",
        },
        "fr": {
            "id": "price_1JmRFrJNcmPzuWtROOs10fKh",
            "price": "CHF 1.00",
        },
        "it": {
            "id": "price_1JmREHJNcmPzuWtRxo7MoT58",
            "price": "CHF 1.00",
        },
    },
    "euro": {
        "at": {
            "id": "price_1JmRTDJNcmPzuWtRnJavIXXX",
            "price": "0,99 €",
        },
        "de": {
            "id": "price_1JmRTDJNcmPzuWtRnJavIXXX",
            "price": "0,99 €",
        },
        "en": {
            "id": "price_1JmRCQJNcmPzuWtRprMnmtax",
            "price": "0,99 €",
        },
        "es": {
            "id": "price_1JmRPSJNcmPzuWtRVvkEkVbS",
            "price": "0,99 €",
        },
        "fr": {
            "id": "price_1JmRU4JNcmPzuWtRRhu1FhiQ",
            "price": "0,99 €",
        },
        "it": {
            "id": "price_1JmRQLJNcmPzuWtRGs76IkUY",
            "price": "0,99 €",
        },
        "nl": {
            "id": "price_1JmROfJNcmPzuWtR6od8OfDW",
            "price": "0,99 €",
        },
        "ie": {
            "id": "price_1JmRCQJNcmPzuWtRprMnmtax",
            "price": "0,99 €",
        },
        "sv": {
            "id": "price_1KQc1PJNcmPzuWtRsEfb6inB",
            "price": "0,99 €",
        },
        "fi": {
            "id": "price_1KQcA7JNcmPzuWtRPKNacfdn",
            "price": "0,99 €",
        },
    },
    "usd": {
        "en": {
            "id": "price_1JmRSRJNcmPzuWtRN9MG5cBy",
            "price": "$0.99"
        }
    }
}
PREMIUM_PLAN_COUNTRY_LANG_MAPPING = {
    # Austria
    "at": {
        "de": PREMIUM_PLAN_ID_MATRIX["euro"]["de"]
    },
    # Belgium
    "be": {
        "fr": PREMIUM_PLAN_ID_MATRIX["euro"]["fr"],
        "de": PREMIUM_PLAN_ID_MATRIX["euro"]["de"],
        "nl": PREMIUM_PLAN_ID_MATRIX["euro"]["nl"],
    },
    # Switzerland
    "ch": {
        "fr": PREMIUM_PLAN_ID_MATRIX["chf"]["fr"],
        "de": PREMIUM_PLAN_ID_MATRIX["chf"]["de"],
        "it": PREMIUM_PLAN_ID_MATRIX["chf"]["it"],
    },
    # Germany
    "de": {
        "de": PREMIUM_PLAN_ID_MATRIX["euro"]["de"],
    },
    # Spain
    "es": {
        "es": PREMIUM_PLAN_ID_MATRIX["euro"]["es"],
    },
    # France
    "fr": {
        "fr": PREMIUM_PLAN_ID_MATRIX["euro"]["fr"],
    },
    # Ireland
    "ie": {
        "en": PREMIUM_PLAN_ID_MATRIX["euro"]["en"],
    },
    # Italy
    "it": {
        "it": PREMIUM_PLAN_ID_MATRIX["euro"]["it"],
    },
    # Netherlands
    "nl": {
        "nl": PREMIUM_PLAN_ID_MATRIX["euro"]["nl"],
    },
    # Sweden
    "se": {
        "sv": PREMIUM_PLAN_ID_MATRIX["euro"]["sv"],
    },
    # Finland
    "fi": {
        "fi": PREMIUM_PLAN_ID_MATRIX["euro"]["fi"],
    },
    "us": {
        "en": PREMIUM_PLAN_ID_MATRIX["usd"]["en"],
    },
    "gb": {
        "en": PREMIUM_PLAN_ID_MATRIX["usd"]["en"],
    },
    "ca": {
        "en": PREMIUM_PLAN_ID_MATRIX["usd"]["en"],
    },
    "nz": {
        "en": PREMIUM_PLAN_ID_MATRIX["usd"]["en"],
    },
    "my": {
        "en": PREMIUM_PLAN_ID_MATRIX["usd"]["en"],
    },
    "sg": {
        "en": PREMIUM_PLAN_ID_MATRIX["usd"]["en"],
    },
}

SUBSCRIPTIONS_WITH_UNLIMITED = config(
    'SUBSCRIPTIONS_WITH_UNLIMITED', default=''
)
PREMIUM_RELEASE_DATE = config('PREMIUM_RELEASE_DATE', '2021-10-27 17:00:00+00:00', cast=str)
PREMIUM_RELEASE_DATE = datetime.fromisoformat(PREMIUM_RELEASE_DATE)

DOMAIN_REGISTRATION_MODAL = config('DOMAIN_REGISTRATION_MODAL', False, cast=bool)
MAX_ONBOARDING_AVAILABLE = config('MAX_ONBOARDING_AVAILABLE', 0, cast=int)

MAX_ADDRESS_CREATION_PER_DAY = config('MAX_ADDRESS_CREATION_PER_DAY', 100, cast=int)
MAX_REPLIES_PER_DAY = config('MAX_REPLIES_PER_DAY', 100, cast=int)
PREMIUM_FEATURE_PAUSED_DAYS = config('ACCOUNT_PREMIUM_FEATURE_PAUSED_DAYS', 1, cast=int)

SOFT_BOUNCE_ALLOWED_DAYS = config('SOFT_BOUNCE_ALLOWED_DAYS', 1, cast=int)
HARD_BOUNCE_ALLOWED_DAYS = config('HARD_BOUNCE_ALLOWED_DAYS', 30, cast=int)

WSGI_APPLICATION = 'privaterelay.wsgi.application'

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    'default': dj_database_url.config(
        default="sqlite:///%s" % os.path.join(BASE_DIR, 'db.sqlite3')
    )
}

REDIS_URL = config('REDIS_URL', '', cast=str)
if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            }
        }
    }
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    SESSION_CACHE_ALIAS = 'default'

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators
# only needed when admin UI is enabled
if ADMIN_ENABLED:
    AUTH_PASSWORD_VALIDATORS = [
        {
            'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
        },
    ]


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en'

# Mozilla l10n directories use lang-locale language codes,
# so we need to add those to LANGUAGES so Django's LocaleMiddleware
# can find them.
LANGUAGES = settings.LANGUAGES + [
    ('zh-tw', 'Chinese'),
    ('zh-cn', 'Chinese'),
]

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'frontend/out'),
    os.path.join(BASE_DIR, 'static'),
]
if SERVE_REACT:
    # Static files (the front-end in /frontend/)
    # https://whitenoise.evans.io/en/stable/django.html#using-whitenoise-with-webpack-browserify-latest-js-thing
    STATIC_URL = '/'
    if settings.DEBUG:
        # In production, we run collectstatic to index all static files.
        # However, when running locally, we want to automatically pick up
        # all files spewed out by `npm run watch` in /frontend/out,
        # and we're fine with the performance impact of that.
        WHITENOISE_ROOT = os.path.join(BASE_DIR, 'frontend/out')
else:
    STATIC_URL = '/static/'

WHITENOISE_INDEX_FILE = True

# for dev statics, we use django-gulp during runserver.
# for stage/prod statics, we run "gulp build" in docker.
# so, squelch django-gulp in prod so it doesn't run gulp during collectstatic:
if not ON_HEROKU:
    GULP_PRODUCTION_COMMAND = ''

SITE_ID = 1

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

SOCIALACCOUNT_PROVIDERS = {
    'fxa': {
        # Note: to request "profile" scope, must be a trusted Mozilla client
        'SCOPE': ['profile'],
        'AUTH_PARAMS': {'access_type': 'offline'},
        'OAUTH_ENDPOINT': config('FXA_OAUTH_ENDPOINT', 'https://oauth.accounts.firefox.com/v1'),
        'PROFILE_ENDPOINT': config('FXA_PROFILE_ENDPOINT', 'https://profile.accounts.firefox.com/v1'),
    }
}

SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_USERNAME_REQUIRED=False
ACCOUNT_PRESERVE_USERNAME_CASING=False
SOCIALACCOUNT_AUTO_SIGNUP=True

FXA_BASE_ORIGIN = config('FXA_BASE_ORIGIN', 'https://accounts.firefox.com')
FXA_SETTINGS_URL = config('FXA_SETTINGS_URL', f'{FXA_BASE_ORIGIN}/settings')
FXA_SUBSCRIPTIONS_URL = config('FXA_SUBSCRIPTIONS_URL', f'{FXA_BASE_ORIGIN}/subscriptions')
FXA_SUPPORT_URL = config('FXA_SUPPORT_URL', f'{FXA_BASE_ORIGIN}/support/')

LOGGING = {
    'version': 1,
    'formatters': {
        'json': {
            '()': 'dockerflow.logging.JsonLogFormatter',
            'logger_name': 'fx-private-relay'
        }
    },
    'handlers': {
        'console_out': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'json'
        },
        'console_err': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'json'
        },
    },
    'loggers': {
        'request.summary': {
            'handlers': ['console_out'],
            'level': 'DEBUG',
        },
        'events': {
            'handlers': ['console_err'],
            'level': 'ERROR',
        },
        'eventsinfo': {
            'handlers': ['console_out'],
            'level': 'INFO',
        },
        'abusemetrics': {
            'handlers': ['console_out'],
            'level': 'INFO'
        },
        'studymetrics': {
            'handlers': ['console_out'],
            'level': 'INFO'
        }
    }
}

if DEBUG:
    DRF_RENDERERS = (
        'rest_framework.renderers.BrowsableAPIRenderer',
        'rest_framework.renderers.JSONRenderer',
    )
else:
    DRF_RENDERERS = (
        'rest_framework.renderers.JSONRenderer',
    )

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'api.authentication.FxaTokenAuthentication',
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated'
    ],
    'DEFAULT_RENDERER_CLASSES': DRF_RENDERERS,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend'
    ]
}

# Turn on logging out on GET in development.
# This allows `/mock/logout/` in the front-end to clear the
# session cookie. Without this, after switching accounts in dev mode,
# then logging out again, API requests continue succeeding even without
# an auth token:
ACCOUNT_LOGOUT_ON_GET = DEBUG

CORS_ALLOWED_ORIGINS = []
CSRF_TRUSTED_ORIGINS = []
if DEBUG:
    # In local development, the React UI can be served up from a different server
    # that needs to be allowed to make requests.
    # In production, the frontend is served by Django, is therefore on the same
    # origin and thus has access to the same cookies.
    CORS_ALLOW_CREDENTIALS = True
    SESSION_COOKIE_SAMESITE = None
    CORS_ALLOWED_ORIGINS += [
        'http://localhost:3000',
        'http://0.0.0.0:3000',
    ]
    CSRF_TRUSTED_ORIGINS += [
        'http://localhost:3000',
        'http://0.0.0.0:3000',
    ]

SENTRY_RELEASE = config("SENTRY_RELEASE", "")
CIRCLE_SHA1 = config("CIRCLE_SHA1", "")
CIRCLE_TAG = config("CIRCLE_TAG", "")
CIRCLE_BRANCH = config("CIRCLE_BRANCH", "")

if SENTRY_RELEASE:
    sentry_release = SENTRY_RELEASE
elif CIRCLE_TAG and CIRCLE_TAG != "unknown":
    sentry_release = CIRCLE_TAG
elif CIRCLE_SHA1 and CIRCLE_SHA1 != "unknown" and CIRCLE_BRANCH and CIRCLE_BRANCH != "unknown":
    sentry_release = f"{CIRCLE_BRANCH}:{CIRCLE_SHA1}"
else:
    sentry_release = None

sentry_sdk.init(
    dsn=config('SENTRY_DSN', None),
    integrations=[DjangoIntegration()],
    debug=DEBUG,
    with_locals=DEBUG,
    release=sentry_release,
)
# Duplicates events for unhandled exceptions, but without useful tracebacks
ignore_logger("request.summary")
# Security scanner attempts, no action required
# Can be re-enabled when hostname allow list implemented at the load balancer
ignore_logger("django.security.DisallowedHost")

markus.configure(
    backends=[
        {
            'class': 'markus.backends.datadog.DatadogMetrics',
            'options': {
                'statsd_host': STATSD_HOST,
                'statsd_port': STATSD_PORT,
                'statsd_prefix': STATSD_PREFIX,
            }
        }
    ]
)
