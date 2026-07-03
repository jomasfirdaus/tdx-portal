"""
Injects site-wide context into every template: the active language, a `t()`
translation callable, and cached site profile / navigation data so templates
never need to query the database directly for chrome elements.
"""
from django.conf import settings

from core.models import SiteProfile


def site_context(request):
    lang = getattr(request, "LANGUAGE", "en")
    return {
        "LANGUAGE": lang,
        "SITE_LANGUAGES": settings.SITE_LANGUAGES,
        "site_profile": SiteProfile.get_solo(),
    }
