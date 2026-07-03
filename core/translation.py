"""
Small helper shared by every app that stores per-language columns
(`field_en`, `field_tet`, `field_pt`) on its models, e.g. Program.title_en.
"""
from core.i18n import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES


def tr(obj, base_field, lang):
    """
    Return getattr(obj, f"{base_field}_{lang}") if it has a non-empty value,
    otherwise fall back to the English column, otherwise the first
    non-empty language available.
    """
    if lang not in SUPPORTED_LANGUAGES:
        lang = DEFAULT_LANGUAGE
    value = getattr(obj, f"{base_field}_{lang}", "") or ""
    if value.strip():
        return value
    fallback = getattr(obj, f"{base_field}_{DEFAULT_LANGUAGE}", "") or ""
    if fallback.strip():
        return fallback
    for code in SUPPORTED_LANGUAGES:
        value = getattr(obj, f"{base_field}_{code}", "") or ""
        if value.strip():
            return value
    return ""
