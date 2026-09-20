from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.fields import StreamField
from wagtail.models import Page

from .blocks import BodyStreamBlock
from .services import get_contact_details


class BodyPage(Page):
    """Common base: a Wagtail page whose content is a StreamField."""

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
        verbose_name = "Home page"
        verbose_name_plural = "Home pages"


class StandardPage(BodyPage):
    parent_page_types = ["pages.HomePage", "pages.StandardPage"]
    subpage_types = ["pages.StandardPage"]

    class Meta:
        verbose_name = "Standard page"
        verbose_name_plural = "Standard pages"


class ContactPage(BodyPage):
    max_count = 1
    parent_page_types = ["pages.HomePage"]
    subpage_types = []

    email = models.EmailField(
        "Email address",
        blank=True,
        help_text="Overrides the email address of the site profile on this page.",
    )
    phone = models.CharField("Phone", max_length=30, blank=True)
    address = models.TextField("Postal address", blank=True)

    content_panels = [
        *Page.content_panels,
        FieldPanel("email"),
        FieldPanel("phone"),
        FieldPanel("address"),
        FieldPanel("body"),
    ]

    class Meta:
        verbose_name = "Contact page"
        verbose_name_plural = "Contact pages"

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["contact"] = get_contact_details(self, request)
        return context
