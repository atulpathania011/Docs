"""Calculus settings.

Storage:
  credentials.sqlite3  usernames + password hashes only (local development)
  users.sqlite3        companies, user profiles, and permissions
  invoices.sqlite3     sales invoices + customers
  purchases.sqlite3    purchase bills + suppliers

Production can use Neon PostgreSQL with either:
  - One DATABASE_URL shared across all four database aliases, or
  - Separate URLs for each database alias.
"""

import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent


# --------------------------------------------------
# DATA DIRECTORY
# --------------------------------------------------
# Use CALCULUS_DATA_DIR when explicitly configured.
# Without a Render persistent disk, use a writable
# temporary directory rather than /var/data.
if os.environ.get("CALCULUS_DATA_DIR"):
    DATA_DIR = Path(os.environ["CALCULUS_DATA_DIR"])
elif os.environ.get("RENDER"):
    DATA_DIR = Path("/tmp/calculus-data")
else:
    DATA_DIR = BASE_DIR / "data"

DATA_DIR.mkdir(parents=True, exist_ok=True)


def env_list(name, default=""):
    return [
        item.strip()
        for item in os.environ.get(name, default).split(",")
        if item.strip()
    ]


# --------------------------------------------------
# SECURITY
# --------------------------------------------------
SECRET_KEY = os.environ.get(
    "CALCULUS_SECRET_KEY",
    "change-this-secret-before-going-live",
)

DEBUG = os.environ.get("CALCULUS_DEBUG") == "1"

ALLOWED_HOSTS = env_list(
    "CALCULUS_ALLOWED_HOSTS",
    "docs-v4mh.onrender.com,127.0.0.1,localhost",
)

CSRF_TRUSTED_ORIGINS = env_list(
    "CALCULUS_CSRF_ORIGINS",
    "https://docs-v4mh.onrender.com",
)


# --------------------------------------------------
# APPLICATIONS
# --------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
    "accounts",
    "directory",
    "sales",
    "purchases",
    "statements",
    "reports",
]


# --------------------------------------------------
# MIDDLEWARE
# --------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "core.middleware.CurrentUserMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# --------------------------------------------------
# URLS AND WSGI
# --------------------------------------------------
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"


# --------------------------------------------------
# TEMPLATES
# --------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
                "core.context.globals",
            ],
        },
    },
]


# --------------------------------------------------
# DATABASE CONFIGURATION
# --------------------------------------------------
def sqlite(name):
    return {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DATA_DIR / name,
        "OPTIONS": {"timeout": 20},
    }


# Each alias can use its own PostgreSQL URL.
# If a specific URL is not provided, DATABASE_URL
# is used as the fallback for that alias.
DATABASE_ENV_VARS = {
    "default": "USERS_DATABASE_URL",
    "credentials": "CREDENTIALS_DATABASE_URL",
    "invoices": "INVOICES_DATABASE_URL",
    "purchases": "PURCHASES_DATABASE_URL",
}

COMMON_DATABASE_URL = os.environ.get("DATABASE_URL")

POSTGRES_CONFIGURED = bool(
    COMMON_DATABASE_URL
    or any(
        os.environ.get(env_name)
        for env_name in DATABASE_ENV_VARS.values()
    )
)

if POSTGRES_CONFIGURED:
    DATABASES = {}

    for alias, env_name in DATABASE_ENV_VARS.items():
        database_url = os.environ.get(env_name) or COMMON_DATABASE_URL

        if not database_url:
            raise ValueError(
                f"Database URL missing for '{alias}'. "
                f"Set {env_name} or DATABASE_URL."
            )

        DATABASES[alias] = dj_database_url.parse(
            database_url,
            conn_max_age=600,
            ssl_require=True,
        )
else:
    # Local development: preserve the four SQLite files.
    DATABASES = {
        "default": sqlite("users.sqlite3"),
        "credentials": sqlite("credentials.sqlite3"),
        "invoices": sqlite("invoices.sqlite3"),
        "purchases": sqlite("purchases.sqlite3"),
    }


DATABASE_ROUTERS = ["core.routers.AppRouter"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --------------------------------------------------
# SESSIONS
# --------------------------------------------------
# Signed-cookie sessions do not require a session table.
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
SESSION_COOKIE_AGE = 8 * 60 * 60
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"


# --------------------------------------------------
# CSRF AND HTTPS
# --------------------------------------------------
CSRF_FAILURE_VIEW = "core.views.errors.csrf_failure"

if os.environ.get("CALCULUS_HTTPS") == "1":
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


# --------------------------------------------------
# INTERNATIONALIZATION
# --------------------------------------------------
LANGUAGE_CODE = "en-in"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True


# --------------------------------------------------
# STATIC FILES
# --------------------------------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

WHITENOISE_USE_FINDERS = True


# --------------------------------------------------
# LOGGING
# --------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}

