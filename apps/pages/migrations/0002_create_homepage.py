from django.db import migrations


def create_homepage(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    Page = apps.get_model("wagtailcore", "Page")
    Site = apps.get_model("wagtailcore", "Site")
    HomePage = apps.get_model("pages", "HomePage")

    # Supprime la page d'accueil de démonstration de Wagtail (et, en cascade, son Site),
    # en reprenant sa locale pour que la nouvelle page soit dans la langue par défaut.
    welcome = Page.objects.get(depth=2, slug="home", content_type__app_label="wagtailcore")
    locale_id = welcome.locale_id
    welcome.delete()

    content_type, _ = ContentType.objects.get_or_create(app_label="pages", model="homepage")
    homepage = HomePage.objects.create(
        title="Accueil",
        locale_id=locale_id,
        draft_title="Accueil",
        slug="home",
        content_type=content_type,
        path="00010001",
        depth=2,
        numchild=0,
        url_path="/home/",
    )
    Site.objects.create(
        hostname="localhost",
        site_name="bkpolok",
        root_page=homepage,
        is_default_site=True,
    )


def remove_homepage(apps, schema_editor):
    Page = apps.get_model("wagtailcore", "Page")
    HomePage = apps.get_model("pages", "HomePage")
    Page.objects.filter(pk__in=HomePage.objects.values("pk")).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("pages", "0001_initial"),
        ("wagtailcore", "0094_alter_page_locale"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [migrations.RunPython(create_homepage, remove_homepage)]
