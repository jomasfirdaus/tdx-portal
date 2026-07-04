"""
Base settings for TDx Website (Django)

Rule:
- No environment-specific logic here
- No DEBUG / PROD branching here
- Only shared configuration
"""

from pathlib import Path
import os
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

print("DB USER:", config("DB_USER"))
print("DB HOST:", config("DB_HOST"))
print("DB PASSWORD:", config("DB_PASSWORD"))
print("DB PORT:", config("DB_PORT"))

# --------------------------------------------------------------------------
# CORE SECURITY
# --------------------------------------------------------------------------

SECRET_KEY = config("DJANGO_SECRET_KEY")


# --------------------------------------------------------------------------
# CUSTOM PROJECT SETTINGS
# --------------------------------------------------------------------------

DASHBOARD_URL_PREFIX = config("DASHBOARD_URL_PREFIX", default="dashboard")


# --------------------------------------------------------------------------
# APPS
# --------------------------------------------------------------------------

INSTALLED_APPS = [
    # Django core
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",

    # Local apps
    "core",
    "accounts",
    "structure",
    "programs",
    "news",
    "gallery",
    "contact",
    "dashboard",
]


# --------------------------------------------------------------------------
# MIDDLEWARE
# --------------------------------------------------------------------------

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",

    # custom middleware
    "core.middleware.LanguageMiddleware",
    "core.middleware.SecurityHeadersMiddleware",
    "core.middleware.AuditLogMiddleware",
]


ROOT_URLCONF = "config.urls"

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# --------------------------------------------------------------------------
# TEMPLATES
# --------------------------------------------------------------------------

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.site_context",
            ],
        },
    },
]


# --------------------------------------------------------------------------
# DATABASE (structure only, no credentials fallback)
# --------------------------------------------------------------------------



DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --------------------------------------------------------------------------
# AUTH
# --------------------------------------------------------------------------

AUTH_USER_MODEL = "accounts.AdminUser"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"
    },
    {
        "NAME": "accounts.validators.ComplexityValidator"
    },
]

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "dashboard:home"
LOGOUT_REDIRECT_URL = "core:home"


# --------------------------------------------------------------------------
# INTERNATIONALIZATION
# --------------------------------------------------------------------------

LANGUAGE_CODE = "en"

SITE_LANGUAGES = [
    ("en", "English"),
    ("tet", "Tetun"),
    ("pt", "Português"),
]

TIME_ZONE = "Asia/Dili"

USE_I18N = False
USE_TZ = True


# --------------------------------------------------------------------------
# STATIC / MEDIA
# --------------------------------------------------------------------------

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_STORAGE = (
    "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
)

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
DATA_UPLOAD_MAX_NUMBER_FIELDS = 200

ALLOWED_IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp"]
MAX_IMAGE_UPLOAD_MB = 5


# --------------------------------------------------------------------------
# SECURITY (BASE DEFAULT ONLY - NO ENV LOGIC)
# --------------------------------------------------------------------------

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "same-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

SECURE_SSL_REDIRECT = False
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


# --------------------------------------------------------------------------
# CACHE (default = locmem, override in prod/demo)
# --------------------------------------------------------------------------

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "tdx-cache",
        "TIMEOUT": 300,
    }
}


# --------------------------------------------------------------------------
# EMAIL (default safe)
# --------------------------------------------------------------------------

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


# --------------------------------------------------------------------------
# LOGGING (safe default)
# --------------------------------------------------------------------------

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}


# --------------------------------------------------------------------------
# SITE METADATA
# --------------------------------------------------------------------------

SITE_NAME = "TDx — Timor Diagnostics"

APPEND_SLASH = True