"""
Base settings for TDx Website (Django)

Rule:
- No environment-specific logic here
- No DEBUG / PROD branching here
- Only shared configuration
"""

from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

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
    "whitenoise.middleware.WhiteNoiseMiddleware",
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

LOGIN_MAX_ATTEMPTS = 5
LOGIN_LOCKOUT_MINUTES = 15


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

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# --- File storage (Django >= 5.1 uses the STORAGES dict; the old
# DEFAULT_FILE_STORAGE / STATICFILES_STORAGE settings are ignored) ---------
#
# All user uploads (logos, hero images, news covers, program covers, gallery
# photos, team photos, favicons — every ImageField/FileField) go to a MinIO
# bucket through core.storage.MinioMediaStorage, a custom backend built on
# the official MinIO Python SDK (the previous django-storages + boto3 stack
# has been removed). Set MEDIA_STORAGE=local in .env only for offline
# development without a MinIO instance.

MEDIA_STORAGE = config("MEDIA_STORAGE", default="minio")

if MEDIA_STORAGE == "minio":
    _minio_endpoint = config("MINIO_ENDPOINT_URL")            # e.g. http://srv-captain--minio:9000
    # Scheme-less endpoints are assumed to be https (the backend parses the
    # scheme into the SDK's `secure` flag).
    if not _minio_endpoint.startswith(("http://", "https://")):
        _minio_endpoint = f"https://{_minio_endpoint}"

    _minio_options = {
        "endpoint_url": _minio_endpoint,
        "access_key": config("MINIO_ACCESS_KEY"),
        "secret_key": config("MINIO_SECRET_KEY"),
        "bucket_name": config("MINIO_BUCKET", default="tdx-media"),
        "region_name": config("MINIO_REGION", default="us-east-1"),
        # True (default): media URLs are time-limited presigned URLs, so the
        # bucket can stay fully private. Set False only together with
        # MINIO_CUSTOM_DOMAIN (or a public-read bucket policy).
        "querystring_auth": config("MINIO_QUERYSTRING_AUTH", default=True, cast=bool),
        # Lifetime of presigned URLs (only used when querystring_auth=True).
        "url_expiry_seconds": config("MINIO_URL_EXPIRY", default=3600, cast=int),
        # Create the bucket on first upload if it doesn't exist — handy in
        # dev, usually left off in prod where the bucket is provisioned.
        "auto_create_bucket": config("MINIO_AUTO_CREATE_BUCKET", default=False, cast=bool),
    }
    # Public host for browser-facing URLs (e.g. minio.example.com/tdx-media —
    # include the bucket for path-style access). When set, URLs use this
    # domain instead of the (possibly internal) endpoint above.
    _minio_custom_domain = config("MINIO_CUSTOM_DOMAIN", default="")
    _minio_url_protocol = config("MINIO_URL_PROTOCOL", default="https:")
    if _minio_custom_domain:
        _minio_options["custom_domain"] = _minio_custom_domain
        _minio_options["url_protocol"] = _minio_url_protocol

    _default_storage = {
        "BACKEND": "core.storage.MinioMediaStorage",
        "OPTIONS": _minio_options,
    }

    # Origin the browser loads media from — appended to the CSP img-src by
    # core.middleware.SecurityHeadersMiddleware so uploaded images render.
    if _minio_custom_domain:
        MEDIA_CSP_ORIGIN = f"{_minio_url_protocol}//{_minio_custom_domain.split('/')[0]}"
    else:
        MEDIA_CSP_ORIGIN = _minio_options["endpoint_url"].rstrip("/")
else:
    _default_storage = {"BACKEND": "django.core.files.storage.FileSystemStorage"}
    MEDIA_CSP_ORIGIN = ""  # local /media/ is already covered by img-src 'self'

STORAGES = {
    "default": _default_storage,
    # WhiteNoise compressed+hashed static files (previously configured via
    # the removed STATICFILES_STORAGE setting, so it was silently inactive
    # on Django >= 5.1 — now restored).
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

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