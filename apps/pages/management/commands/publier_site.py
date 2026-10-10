from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from wagtail.models import Site

from apps.pages.services import configure_site, publish_drafts


class Command(BaseCommand):
    help = (
        "Met en ligne le site : nom d'hôte du site Wagtail tiré de WAGTAILADMIN_BASE_URL et "
        "publication de toutes les pages en brouillon. Idempotent ; ne supprime rien."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--base-url",
            default=settings.WAGTAILADMIN_BASE_URL,
            help="URL publique du site (défaut : WAGTAILADMIN_BASE_URL).",
        )
        parser.add_argument("--site-name", default="bkpolok", help="Nom du site Wagtail.")

    def handle(self, *args, **options):
        site = Site.objects.filter(is_default_site=True).first()
        if site is None:
            raise CommandError("Aucun site par défaut : lancez d'abord les migrations.")
        try:
            configure_site(site, options["base_url"], options["site_name"])
        except ValueError as error:
            raise CommandError(str(error)) from error
        self.stdout.write(f"Site : {site.root_url}")

        published = publish_drafts(site.root_page)
        self.stdout.write(f"Pages publiées : {len(published)}")
        for page in published:
            self.stdout.write(f"  {page.url_path}")
        self.stdout.write(
            self.style.WARNING(
                "Redémarrez le service web pour vider le cache des URL du site dans chaque "
                "processus Gunicorn."
            )
        )
