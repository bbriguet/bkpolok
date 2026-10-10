from django.db import migrations


def rename_homepage(apps, schema_editor):
    """Le site est en anglais : « Accueil » (migration 0002) devient « Home ». Slug et URL inchangés."""
    HomePage = apps.get_model("pages", "HomePage")
    HomePage.objects.filter(title="Accueil").update(title="Home")
    HomePage.objects.filter(draft_title="Accueil").update(draft_title="Home")


def restore_homepage(apps, schema_editor):
    HomePage = apps.get_model("pages", "HomePage")
    HomePage.objects.filter(title="Home").update(title="Accueil")
    HomePage.objects.filter(draft_title="Home").update(draft_title="Accueil")


class Migration(migrations.Migration):
    dependencies = [("pages", "0003_english_labels_and_design_blocks")]

    operations = [migrations.RunPython(rename_homepage, restore_homepage)]
