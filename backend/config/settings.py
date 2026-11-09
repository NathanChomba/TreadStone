"""
Django settings for the Treadstone backend.

Secrets and machine-specific values are read from backend/.env (never committed).
"""

import os
from decimal import Decimal
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env(name, default=None):
    return os.getenv(name, default)


def env_bool(name, default=False):
    return env(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


SECRET_KEY = env("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("DJANGO_SECRET_KEY is missing from backend/.env")

DEBUG = env_bool("DJANGO_DEBUG", False)
ALLOWED_HOSTS = [h.strip() for h in env("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third party
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    "django_q",
    # Treadstone
    "members",
    "savings",
    "loans",
    "metals",
    "payouts",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME", "treadstone"),
        "USER": env("DB_USER", "postgres"),
        "PASSWORD": env("DB_PASSWORD", ""),
        "HOST": env("DB_HOST", "localhost"),
        "PORT": env("DB_PORT", "5432"),
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "members.Member"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Lusaka"
USE_I18N = True
USE_TZ = True


# Static files

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]


# Email

MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.console.EmailBackend",
    },
}


# Django REST Framework

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    # Keep money exact on the wire: Decimals serialise as strings.
    "COERCE_DECIMAL_TO_STRING": True,
    "EXCEPTION_HANDLER": "config.errors.api_exception_handler",
}


# CORS (the Vite dev server proxies /api, but allow direct calls in dev too)

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# The admin is also reachable through the Vite proxy on :5173, so trust that origin for CSRF.
CSRF_TRUSTED_ORIGINS = list(CORS_ALLOWED_ORIGINS)

if DEBUG:
    # In development, also trust this PC's own network addresses so a phone on the same
    # Wi-Fi can use the admin through http://<pc-ip>:5173.
    import socket

    try:
        _ips = {ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")}
    except OSError:
        _ips = set()
    CSRF_TRUSTED_ORIGINS += [f"http://{ip}:5173" for ip in sorted(_ips)]


# Django-Q2 with the PostgreSQL (ORM) broker - no Redis

Q_CLUSTER = {
    "name": "treadstone",
    "orm": "default",
    "workers": 2,
    "timeout": 60,
    "retry": 120,
    "queue_limit": 50,
    "catch_up": False,
}


# Treadstone business settings

METAL_PRICE_PROVIDER = env("METAL_PRICE_PROVIDER", "simulated")
GOLDAPI_KEY = env("GOLDAPI_KEY", "")
USD_ZMW_RATE = Decimal(env("USD_ZMW_RATE", "26.50"))

CUSTODIAN_FEE_PERCENT = Decimal(env("CUSTODIAN_FEE_PERCENT", "1.0"))

MOBILE_MONEY_PROVIDER = env("MOBILE_MONEY_PROVIDER", "simulated")

AT_USERNAME = env("AT_USERNAME", "sandbox")
AT_API_KEY = env("AT_API_KEY", "")
AT_SENDER_ID = env("AT_SENDER_ID", "")

# Loans: a member may borrow up to this fraction of the ZMW value of their
# available metal, at a flat interest rate per loan.
LOAN_TO_VALUE = Decimal("0.50")
LOAN_INTEREST_PERCENT = Decimal("10.0")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {"treadstone": {"handlers": ["console"], "level": "INFO"}},
}
