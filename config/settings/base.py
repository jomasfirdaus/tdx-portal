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
# bucket via the S3 API. Set MEDIA_STORAGE=local in .env only for offline
# development without a MinIO instance.

MEDIA_STORAGE = config("MEDIA_STORAGE", default="minio")

if MEDIA_STORAGE == "minio":
    # boto3 >= 1.36 defaults to streaming uploads with trailing checksums
    # (aws-chunked encoding). Reverse proxies in front of MinIO (Cloudflare,
    # nginx/CapRover) often re-buffer the body, which breaks that format and
    # yields "XAmzContentSHA256Mismatch" on every upload. These env vars tell
    # botocore to only add checksums when the operation requires them —
    # plain, proxy-safe PUTs.
    os.environ.setdefault("AWS_REQUEST_CHECKSUM_CALCULATION", "when_required")
    os.environ.setdefault("AWS_RESPONSE_CHECKSUM_VALIDATION", "when_required")

    _minio_endpoint = config("MINIO_ENDPOINT_URL")            # e.g. http://srv-captain--minio:9000
    if not _minio_endpoint.startswith(("http://", "https://")):
        # boto3 raises "Invalid endpoint" for scheme-less URLs — assume https.
        _minio_endpoint = f"https://{_minio_endpoint}"

    _minio_options = {
        "endpoint_url": _minio_endpoint,
        "access_key": config("MINIO_ACCESS_KEY"),
        "secret_key": config("MINIO_SECRET_KEY"),
        "bucket_name": config("MINIO_BUCKET", default="tdx-media"),
        "region_name": config("MINIO_REGION", default="us-east-1"),
        # MinIO requires path-style addressing (bucket in the path, not the
        # hostname) and Signature V4.
        "addressing_style": "path",
        "signature_version": "s3v4",
        # Never overwrite an existing object with the same name — mirrors
        # FileSystemStorage behaviour (a suffix is appended on collision).
        "file_overwrite": False,
        "default_acl": None,
        # True (default): media URLs are time-limited signed URLs, so the
        # bucket can stay fully private. Set False only together with
        # MINIO_CUSTOM_DOMAIN and a public-read bucket policy.
        "querystring_auth": config("MINIO_QUERYSTRING_AUTH", default=True, cast=bool),
    }
    # Public host for browser-facing URLs (e.g. minio.example.com/tdx-media).
    # When set, URLs use this domain instead of the (possibly internal)
    # endpoint above.
    _minio_custom_domain = config("MINIO_CUSTOM_DOMAIN", default="")
    if _minio_custom_domain:
        _minio_options["custom_domain"] = _minio_custom_domain
        _minio_options["url_protocol"] = config("MINIO_URL_PROTOCOL", default="https:")

    _default_storage = {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": _minio_options,
    }

    # Origin the browser loads media from — appended to the CSP img-src by
    # core.middleware.SecurityHeadersMiddleware so uploaded images render.
    if _minio_custom_domain:
        MEDIA_CSP_ORIGIN = f"{_minio_options['url_protocol']}//{_minio_custom_domain.split('/')[0]}"
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