"""
Django settings for ksicht project.

Generated by 'django-admin startproject' using Django 2.2.7.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os

from django.contrib.messages import constants as messages
import dsnparse


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG", "0") == "1"

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("SECRET_KEY")

if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "no-secret-key"
    else:
        raise RuntimeError("Missing SECRET_KEY environment variable.")


ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")

if not ALLOWED_HOSTS == "" and DEBUG:
    ALLOWED_HOSTS = "*"


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.sites",
    "django.contrib.sitemaps",
    "django.contrib.flatpages",
    "django.contrib.staticfiles",
    "django.forms",
    "django_registration",
    "webpack_loader",
    "markdownx",  # A markdown editor
    "markdown_deux",  # Markdown rendering template tags
    "capture_tag",  # Re-use same block multiple times
    "crispy_forms",
    "cuser",
    "ksicht.core",
    "ksicht.bulma",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.contrib.flatpages.middleware.FlatpageFallbackMiddleware",
    "htmlmin.middleware.HtmlMinifyMiddleware",
    "htmlmin.middleware.MarkRequestMiddleware",
]

ROOT_URLCONF = "ksicht.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "ksicht", "templates"),],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "ksicht.context_processors.global_info",
            ],
        },
    },
]

WSGI_APPLICATION = "ksicht.wsgi.application"


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASE_DSN = os.environ.get("DATABASE_DSN", "postgresql://localhost:5432/ksicht")
db = dsnparse.parse(DATABASE_DSN)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": db.paths[0],
        "USER": db.username,
        "PASSWORD": db.password,
        "HOST": db.host,
        "PORT": db.port,
    }
}

# Caching
CACHES = {"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache",}}

# Mailing
EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = os.environ.get("EMAIL_HOST", None)
EMAIL_PORT = int(os.environ.get("EMAIL_PORT")) if "EMAIL_PORT" in os.environ else None
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", None)
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", None)
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "0") == "1"
EMAIL_USE_SSL = os.environ.get("EMAIL_USE_SSL", "0") == "1"

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_USER_MODEL = "core.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",},
]

LOGIN_REDIRECT_URL = "core:home"
LOGOUT_REDIRECT_URL = "core:home"


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = "cs-CZ"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATIC_URL = "/static/"
STATICFILES_DIRS = (os.path.join(BASE_DIR, "assets"),)


# Media files (user-uploaded files)
# https://docs.djangoproject.com/en/2.2/topics/files/

MEDIA_ROOT = os.environ.get("MEDIA_ROOT", os.path.join(BASE_DIR, "media"))
MEDIA_URL = os.environ.get("MEDIA_URL", "/media/")

# Logging
LOGGING = {
    "version": 1,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO" if DEBUG else "WARNING"}
    },
}

# Site
SITE_ID = 1

# Message custom tags.
MESSAGE_TAGS = {
    messages.DEBUG: "is-primary",
    messages.SUCCESS: "is-success",
    messages.INFO: "is-info",
    messages.WARNING: "is-warning",
    messages.ERROR: "is-danger",
}

# HTML minify
HTML_MINIFY = os.environ.get("MINIFY_HTML", DEBUG)

# Custom settings
# ---------------

SITEINFO = {
    "name": "KSICHT",
    "description": "KSICHT ~ Korespondenční Seminář Inspirovaný Chemickou Tématikou.",
    "keywords": (),
}

# Webpack-built assets

WEBPACK_LOADER = {
    "DEFAULT": {
        "CACHE": not DEBUG,
        "BUNDLE_DIR_NAME": "bundles/",  # must end with slash
        "STATS_FILE": os.path.join(BASE_DIR, "webpack-stats.json"),
        "POLL_INTERVAL": 0.1,
        "TIMEOUT": None,
        "IGNORE": [".+\.hot-update.js", ".+\.map"],
    }
}

# Markdown
MARKDOWNX_MARKDOWNIFY_FUNCTION = "ksicht.markdown.markdownify"

MARKDOWN_DEUX_STYLES = {
    "default": {
        "extras": {
            "code-friendly": None,
            "tables": None,
            "header-ids": None,
            "footnotes": None,
        },
        "safe_mode": False,
    },
    # "trusted": {
    #     "safe_mode": False,
    #     "extras": {
    #         "tables": None,
    #         "header-ids": None,
    #         "footnotes": None,
    #     },
    # },
    "target_blank": {"extras": {"target-blank-links": None,},},
}


# django-registration
ACCOUNT_ACTIVATION_DAYS = 7  # One-week activation window

# Crispy forms
CRISPY_FAIL_SILENTLY = not DEBUG

CRISPY_ALLOWED_TEMPLATE_PACKS = (
    "bootstrap",
    "uni_form",
    "bootstrap3",
    "bootstrap4",
    "bulma",
)

CRISPY_TEMPLATE_PACK = "bulma"
