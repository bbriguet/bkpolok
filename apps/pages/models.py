from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.fields import StreamField
from wagtail.models import Page

from .blocks import BodyStreamBlock


class BodyPage(Page):
    """Base commune : une page Wagtail dont le contenu est un StreamField."""

    body = StreamField(BodyStreamBlock(), blank=True, use_json_field=True)

    content_panels = [*Page.content_panels, FieldPanel("body")]

    class Meta:
        abstract = True


class HomePage(BodyPage):
    max_count = 1
    parent_page_types = ["wagtailcore.Page"]
    subpage_types = [
        "services.ServiceIndexPage",
        "pages.StandardPage",
        "pages.ContactPage",
    ]

    class Meta:
        verbose_name = "Page d’accueil"
        verbose_name_plural = "Pages d’accueil"


class StandardPage(BodyPage):
    parent_page_types = ["pages.HomePage", "pages.StandardPage"]
    subpage_types = ["pages.StandardPage"]

    class Meta:
        verbose_name = "Page standard"
        verbose_name_plural = "Pages standard"


class ContactPage(BodyPage):
    max_count = 1
    parent_page_types = ["pages.HomePage"]
    subpage_types = []

    email = models.EmailField("Adresse e-mail", blank=True)
    phone = models.CharField("Téléphone", max_length=30, blank=True)
    address = models.TextField("Adresse postale", blank=True)

    content_panels = [
        *Page.content_panels,
        FieldPanel("email"),
        FieldPanel("phone"),
        FieldPanel("address"),
        FieldPanel("body"),
    ]

    class Meta:
        verbose_name = "Page de contact"
        verbose_name_plural = "Pages de contact"
