from django.core.management.base import BaseCommand, CommandError
from wagtail.models import Site

from apps.pages.services import create_site_pages


class Command(BaseCommand):
    help = (
        "Create the site's pages (About, Expertise, …) as unpublished drafts under the home page."
    )

    def handle(self, *args, **options):
        site = Site.objects.filter(is_default_site=True).first()
        if site is None:
            raise CommandError("No default site: run the migrations first.")
        created = create_site_pages(site.root_page)
        if not created:
            self.stdout.write("Nothing to create: every page already exists.")
        for page in created:
            self.stdout.write(f"Created draft: {page.url_path}")
