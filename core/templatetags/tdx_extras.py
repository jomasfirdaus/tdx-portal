from django import template
from django.utils.safestring import mark_safe

from core.i18n import t as translate
from core.models import PageHeader
from core.translation import tr as translate_field

register = template.Library()

# Breadcrumb label for each PageKey that renders through the shared
# {% page_header %} inclusion tag. This is routing/navigation structure
# (mirrors the labels already used in the navbar), not admin-editable
# content — only whether the breadcrumb is shown is a PageHeader field.
_PAGE_HEADER_BREADCRUMB_KEYS = {
    "profile": "nav.profile",
    "vision_mission": "nav.vision_mission",
    "programs": "nav.programs",
    "structure": "nav.structure",
    "news": "nav.news",
    "gallery": "nav.gallery",
    "contact": "nav.contact",
    "appointments": "nav.appointment",
}

# Small, hand-written icon set (simple geometric strokes) so the project has
# zero dependency on an external icon font/CDN — keeps the CSP locked to
# 'self' and avoids a third-party supply-chain dependency for something this
# small.
_ICONS = {
    "microscope": '<path d="M6 20h8"/><path d="M9 20v-4a3 3 0 1 1 6 0"/><path d="M12 16V8"/><path d="M9 8h6l-1-4H10z"/><circle cx="18" cy="20" r="1.4"/>',
    "shield": '<path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6z"/><path d="M9 12l2 2 4-4"/>',
    "clipboard": '<rect x="6" y="4" width="12" height="17" rx="2"/><rect x="9" y="2.5" width="6" height="3" rx="1"/><path d="M9 11h6M9 15h6"/>',
    "graduation": '<path d="M2 9l10-5 10 5-10 5z"/><path d="M6 11v5c0 1.5 2.7 3 6 3s6-1.5 6-3v-5"/><path d="M22 9v6"/>',
    "truck": '<rect x="2" y="7" width="12" height="9"/><path d="M14 10h4l4 4v2h-8z"/><circle cx="7" cy="18" r="1.6"/><circle cx="17" cy="18" r="1.6"/>',
    "heart": '<path d="M12 20s-7-4.4-9.5-9C.7 7.4 3 4 6.3 4 8.4 4 10.4 5.2 12 7c1.6-1.8 3.6-3 5.7-3 3.3 0 5.6 3.4 3.8 7-2.5 4.6-9.5 9-9.5 9z"/>',
    "heart-pulse": '<path d="M12 20s-7-4.4-9.5-9C.7 7.4 3 4 6.3 4 8.4 4 10.4 5.2 12 7c1.6-1.8 3.6-3 5.7-3 3.3 0 5.6 3.4 3.8 7-2.5 4.6-9.5 9-9.5 9z"/><path d="M4 12h3l2-4 3 7 2-4h4"/>',
    "stethoscope": '<path d="M5 3v6a4 4 0 0 0 8 0V3"/><path d="M9 13v2a6 6 0 0 0 12 0v-2"/><circle cx="21" cy="11" r="1.6"/>',
    "hands": '<path d="M8 13V6a2 2 0 1 1 4 0v6"/><path d="M12 12V4a2 2 0 1 1 4 0v9"/><path d="M4 13l2 1v4a3 3 0 0 0 3 3h6a4 4 0 0 0 4-4v-3l2-2"/>',
    "lightbulb": '<path d="M9 18h6"/><path d="M10 21h4"/><path d="M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.3 1 2.1h5c0-.8.4-1.6 1-2.1A6 6 0 0 0 12 3z"/>',
    "scale": '<path d="M12 3v18M7 21h10"/><path d="M5 7l-3 6a3.2 3.2 0 0 0 6 0z"/><path d="M19 7l-3 6a3.2 3.2 0 0 0 6 0z"/><path d="M4 7h16l-4-3H8z"/>',
    "layers": '<path d="M12 2 2 7l10 5 10-5z"/><path d="M2 12l10 5 10-5"/><path d="M2 17l10 5 10-5"/>',
    "grid": '<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/>',
    "columns": '<rect x="3" y="4" width="5" height="16"/><rect x="9.5" y="4" width="5" height="16"/><rect x="16" y="4" width="5" height="16"/>',
    "users": '<circle cx="9" cy="8" r="3.2"/><path d="M3 20c0-3.3 2.7-5.5 6-5.5s6 2.2 6 5.5"/><circle cx="17.5" cy="9" r="2.6"/><path d="M15.5 14.3c2.6.3 4.5 2.2 4.5 5.7"/>',
    "briefcase": '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><path d="M3 12h18"/>',
    "wallet": '<rect x="3" y="6" width="18" height="13" rx="2"/><path d="M3 10h18"/><circle cx="16" cy="14" r="1.2"/>',
    "settings": '<circle cx="12" cy="12" r="3"/><path d="M19 12a7 7 0 0 0-.2-1.6l2-1.6-2-3.4-2.3.9a7 7 0 0 0-2.7-1.6L13.4 2h-2.8l-.4 2.7a7 7 0 0 0-2.7 1.6l-2.3-.9-2 3.4 2 1.6a7 7 0 0 0 0 3.2l-2 1.6 2 3.4 2.3-.9a7 7 0 0 0 2.7 1.6l.4 2.7h2.8l.4-2.7a7 7 0 0 0 2.7-1.6l2.3.9 2-3.4-2-1.6c.1-.5.2-1 .2-1.6z"/>',
    "cpu": '<rect x="6" y="6" width="12" height="12" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M9 2v3M15 2v3M9 19v3M15 19v3M2 9h3M2 15h3M19 9h3M19 15h3"/>',
    "flask": '<path d="M9 3h6"/><path d="M10 3v6l-5.5 9.5A2 2 0 0 0 6.2 21h11.6a2 2 0 0 0 1.7-3L14 9V3"/><path d="M8 15h8"/>',
    "syringe": '<path d="M19 3l2 2"/><path d="M17 5l-9.5 9.5"/><path d="M14 8l2 2M12 10l2 2M10 12l2 2"/><path d="M3 21l3-1 3.5-3.5-2-2L4 18z"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>',
    "phone": '<path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2z"/>',
    "map-pin": '<path d="M12 21s7-6.5 7-12a7 7 0 1 0-14 0c0 5.5 7 12 7 12z"/><circle cx="12" cy="9" r="2.4"/>',
    "menu": '<path d="M3 6h18M3 12h18M3 18h18"/>',
    "close": '<path d="M6 6l12 12M18 6L6 18"/>',
    "chevron-right": '<path d="M9 6l6 6-6 6"/>',
    "arrow-right": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/>',
    "image": '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="8.5" cy="9.5" r="1.5"/><path d="M21 16l-5.5-5.5L3 21"/>',
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    "facebook": '<path d="M15 3h-2a5 5 0 0 0-5 5v2H6v4h2v7h4v-7h3l1-4h-4V8a1 1 0 0 1 1-1h3z"/>',
    "instagram": '<rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.2" cy="6.8" r="1"/>',
    "linkedin": '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M7 10v7M7 7v.01M11 17v-4.5a2.5 2.5 0 0 1 5 0V17M11 10v7"/>',
    "youtube": '<rect x="2" y="5" width="20" height="14" rx="4"/><path d="M10 9l6 3-6 3z"/>',
    "dot": '<circle cx="12" cy="12" r="3"/>',
    "check": '<path d="M5 12l5 5L19 7"/>',
    "eye": '<path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z"/><circle cx="12" cy="12" r="3"/>',
    "lock": '<rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V7a4 4 0 1 1 8 0v4"/>',
    "logout": '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="M16 17l5-5-5-5"/><path d="M21 12H9"/>',
    "dashboard": '<rect x="3" y="3" width="7" height="9"/><rect x="14" y="3" width="7" height="5"/><rect x="14" y="12" width="7" height="9"/><rect x="3" y="16" width="7" height="5"/>',
    "trash": '<path d="M4 7h16"/><path d="M9 7V4h6v3"/><path d="M6 7l1 13a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-13"/>',
    "edit": '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
}


@register.simple_tag
def icon(name, css_class="icon"):
    path = _ICONS.get(name, _ICONS["dot"])
    svg = (
        f'<svg class="{css_class}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{path}</svg>'
    )
    return mark_safe(svg)


@register.simple_tag(takes_context=True)
def t(context, key):
    """Static UI string translation: {% t "nav.home" %}"""
    lang = context.get("LANGUAGE", "en")
    return translate(key, lang)


@register.simple_tag(takes_context=True)
def tf(context, obj, field):
    """Template tag: {% tf program "title" %} -> program.title_en/tet/pt for the active language."""
    lang = context.get("LANGUAGE", "en")
    return translate_field(obj, field, lang)


@register.simple_tag(takes_context=True)
def tf_safe(context, obj, field):
    """Like {% tf %} but marks the result safe. ONLY use for fields that are
    sanitized server-side at save time (e.g. NewsPost.content_*, see
    news/models.py's bleach.clean call) — never for raw user input."""
    lang = context.get("LANGUAGE", "en")
    value = translate_field(obj, field, lang)
    return mark_safe(value)


@register.simple_tag(takes_context=True)
def get_page_header(context, page_key):
    """
    Low-level accessor for pages whose header has bespoke markup around it
    (Home's hero with CTAs/stats, or a news/program/gallery detail page's
    per-item meta) but still needs its background image/overlay/text color
    to come from the same admin-managed PageHeader row as every other page:
    {% get_page_header "home" as header %} -> PageHeader instance, or None
    when there's no row yet or it's marked inactive (fall back to a plain
    default in that case, same rule the {% page_header %} banner uses).
    """
    header = PageHeader.get_for_page(page_key)
    return header if (header and header.is_active) else None


@register.inclusion_tag("partials/page_header.html", takes_context=True)
def page_header(context, page_key, title_override=None, breadcrumb_extra=None):
    """
    Full banner: {% page_header "profile" %}. Used by every public page that
    doesn't need extra per-item content in its header — the reusable
    component every such page consumes, so none of them hardcode their own
    title, background, or colors.
    """
    lang = context.get("LANGUAGE", "en")
    header = get_page_header(context, page_key)

    title = title_override or (translate_field(header, "title", lang) if header else "") or translate(
        _PAGE_HEADER_BREADCRUMB_KEYS.get(page_key, ""), lang
    )
    subtitle = translate_field(header, "subtitle", lang) if header else ""

    breadcrumb_label = translate(_PAGE_HEADER_BREADCRUMB_KEYS.get(page_key, ""), lang)
    breadcrumb = f"{breadcrumb_label} / {breadcrumb_extra}" if breadcrumb_extra else breadcrumb_label

    return {
        "LANGUAGE": lang,
        "header": header,
        "title": title,
        "subtitle": subtitle,
        "breadcrumb": breadcrumb,
        "show_breadcrumb": header.show_breadcrumb if header else True,
    }


@register.simple_tag(takes_context=True)
def lang_url(context, lang_code):
    """Builds the current URL with ?lang=<code> so the switcher preserves the page."""
    request = context["request"]
    params = request.GET.copy()
    params["lang"] = lang_code
    return f"{request.path}?{params.urlencode()}"


@register.filter
def get_attr(obj, attr_name):
    """Dynamic field access for generic dashboard list tables:
    {{ object|get_attr:field_name }} — calls the attribute if it's callable
    (covers get_FOO_display(), get_full_name(), etc.)."""
    value = getattr(obj, attr_name, "")
    if callable(value):
        try:
            value = value()
        except Exception:
            value = ""
    return value


@register.filter
def get_field(form, field_name):
    """Dynamic form field access: {{ form|get_field:name }} -> BoundField."""
    try:
        return form[field_name]
    except KeyError:
        return None
