"""
Custom middleware for TDx:

- LanguageMiddleware: resolves the active language from `?lang=`, session,
  or cookie (in that priority order) without pulling in Django's full
  gettext-based i18n machinery.
- SecurityHeadersMiddleware: adds a strict Content-Security-Policy and a few
  extra defensive headers on top of Django's built-in SecurityMiddleware.
- AuditLogMiddleware: writes a lightweight access record for requests into
  the staff dashboard, so suspicious activity is traceable after the fact.
"""
import logging

from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

from core.i18n import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES

security_logger = logging.getLogger("tdx.security")

LANGUAGE_SESSION_KEY = "tdx_language"
LANGUAGE_COOKIE_NAME = "tdx_lang"


class LanguageMiddleware(MiddlewareMixin):
    def process_request(self, request):
        lang = request.GET.get("lang")
        if lang not in SUPPORTED_LANGUAGES:
            lang = request.session.get(LANGUAGE_SESSION_KEY)
        if lang not in SUPPORTED_LANGUAGES:
            lang = request.COOKIES.get(LANGUAGE_COOKIE_NAME)
        if lang not in SUPPORTED_LANGUAGES:
            lang = DEFAULT_LANGUAGE

        request.LANGUAGE = lang
        if request.GET.get("lang") in SUPPORTED_LANGUAGES:
            request.session[LANGUAGE_SESSION_KEY] = lang

    def process_response(self, request, response):
        lang = getattr(request, "LANGUAGE", DEFAULT_LANGUAGE)
        response.set_cookie(
            LANGUAGE_COOKIE_NAME,
            lang,
            max_age=60 * 60 * 24 * 365,
            httponly=False,
            samesite="Lax",
            secure=not settings.DEBUG,
        )
        return response


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Adds a Content-Security-Policy and a couple of headers Django's
    SecurityMiddleware doesn't set out of the box. Kept intentionally strict:
    no inline scripts/styles beyond what the base template needs, and the
    only third-party origin is OpenStreetMap's tile servers (images only)
    for the Leaflet location maps — Leaflet's JS/CSS is vendored and served
    from 'self'.
    """

    def process_response(self, request, response):
        # Uploaded media (logos, covers, gallery photos) is served from the
        # MinIO origin configured in settings; it must be whitelisted in
        # img-src or the browser will refuse to render any uploaded image.
        media_origin = getattr(settings, "MEDIA_CSP_ORIGIN", "")
        img_src = "img-src 'self' data: https://*.tile.openstreetmap.org https://tile.openstreetmap.org"
        if media_origin:
            img_src += f" {media_origin}"
        response.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; "
            f"{img_src}; "
            "style-src 'self' 'unsafe-inline'; "
            "script-src 'self'; "
            "font-src 'self'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "frame-ancestors 'none';"
        )
        response.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.setdefault("X-Permitted-Cross-Domain-Policies", "none")
        return response


class AuditLogMiddleware(MiddlewareMixin):
    """Logs access to the staff dashboard for a basic audit trail."""

    def process_request(self, request):
        prefix = f"/{settings.DASHBOARD_URL_PREFIX}/"
        if request.path.startswith(prefix):
            user = getattr(request, "user", None)
            username = getattr(user, "username", "anonymous") if user and user.is_authenticated else "anonymous"
            ip = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", "unknown"))
            security_logger.info(
                "dashboard_access path=%s user=%s ip=%s method=%s",
                request.path, username, ip.split(",")[0].strip(), request.method,
            )
