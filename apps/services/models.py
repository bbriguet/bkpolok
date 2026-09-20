from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.models import Page

from apps.pages.models import BodyPage

from .services import list_live_services


class ServiceIndexPage(BodyPage):
    intro = models.TextField("Introduction", blank=True)

    parent_page_types = ["pages.HomePage"]
    subpage_types = ["services.ServicePage"]

    content_panels = [
        *Page.content_panels,
        FieldPanel("intro"),
        FieldPanel("body"),
    ]

    class Meta:
        verbose_name = "page d’index des services"
        verbose_name_plural = "pages d’index des services"

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["services"] = list_live_services(self)
        return context


class ServicePage(BodyPage):
    summary = models.CharField(
        "Summary",
        max_length=600,
        blank=True,
        help_text="Shown in the list of services and in search results.",
    )

    parent_page_types = ["services.ServiceIndexPage"]
    subpage_types = []

    content_panels = [
        *Page.content_panels,
        FieldPanel("summary"),
        FieldPanel("body"),
    ]

    class Meta:
        verbose_name = "page de service"
        verbose_name_plural = "pages de service"
