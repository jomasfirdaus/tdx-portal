from django.db import migrations


def copy_hero_image(apps, schema_editor):
    SiteProfile = apps.get_model("core", "SiteProfile")
    PageHeader = apps.get_model("core", "PageHeader")

    profile = SiteProfile.objects.filter(pk=1).first()
    hero_name = profile.hero_image.name if profile and profile.hero_image else ""

    # Plain defaults (no overlay tint, dark text) so a fresh "home" row
    # looks exactly like the hero did before this migration — not the
    # PageHeader model's own out-of-the-box styled defaults.
    defaults = {"overlay_opacity": 0, "text_color": "#0E2A2B"}
    if hero_name:
        defaults["background_image"] = hero_name

    PageHeader.objects.update_or_create(page_key="home", defaults=defaults)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_pageheader'),
    ]

    operations = [
        migrations.RunPython(copy_hero_image, noop_reverse),
    ]
