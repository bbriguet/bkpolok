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
        verbose_name = "Page d’index des services"
        verbose_name_plural = "Pages d’index des services"

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["services"] = list_live_services(self)
        return context


class ServicePage(BodyPage):
    summary = models.CharField(
        "Résumé",
        max_length=250,
        blank=True,
        help_text="Affiché dans la liste des services et dans les résultats de recherche.",
    )

    parent_page_types = ["services.ServiceIndexPage"]
    subpage_types = []

    content_panels = [
        *Page.content_panels,
        FieldPanel("summary"),
        FieldPanel("body"),
    ]

    class Meta:
        verbose_name = "Page de service"
        verbose_name_plural = "Pages de service"
