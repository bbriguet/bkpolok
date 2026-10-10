from django.core.exceptions import ValidationError
from django.db import models
from django.shortcuts import redirect
from wagtail.admin.panels import FieldPanel
from wagtail.contrib.routable_page.models import RoutablePageMixin, path
from wagtail.fields import StreamField
from wagtail.models import Page

from apps.contact.forms import ContactForm
from apps.contact.services import submit_contact_form

from .blocks import BodyStreamBlock
from .services import count_heroes, get_contact_details, is_legal_page


class BodyPage(Page):
    """Common base: a Wagtail page whose content is a StreamField."""

    body = StreamField(BodyStreamBlock(), blank=True, use_json_field=True)
    og_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Share image",
        help_text="Shown when the page is shared (Open Graph). Falls back to the site profile.",
    )

    content_panels = [*Page.content_panels, FieldPanel("body")]
    promote_panels = [*Page.promote_panels, FieldPanel("og_image")]

    class Meta:
        abstract = True

    @property
    def has_hero(self) -> bool:
        """Vrai si le corps contient un bandeau d'accueil, qui porte alors le <h1> de la page."""
        return count_heroes(self.body) > 0

    def clean(self):
        super().clean()
        if count_heroes(self.body) > 1:
            raise ValidationError({"body": "A page can only have one hero (it holds the h1)."})


class HomePage(BodyPage):
    max_count = 1
    parent_page_types = ["wagtailcore.Page"]
    subpage_types = [
        "services.ServiceIndexPage",
        "pages.StandardPage",
        "pages.ContactPage",
    ]

    class Meta:
        verbose_name = "page d’accueil"
        verbose_name_plural = "pages d’accueil"


class StandardPage(BodyPage):
    parent_page_types = ["pages.HomePage", "pages.StandardPage"]
    subpage_types = ["pages.StandardPage"]

    class Meta:
        verbose_name = "page standard"
        verbose_name_plural = "pages standard"

    def get_context(self, request, *args, **kwargs):
        from apps.profile.services import get_site_profile

        context = super().get_context(request, *args, **kwargs)
        context["is_legal"] = is_legal_page(self, get_site_profile(request))
        return context


class ContactPage(RoutablePageMixin, BodyPage):
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
        verbose_name = "page de contact"
        verbose_name_plural = "pages de contact"

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["contact"] = get_contact_details(self, request)
        return context

    @path("")
    def index(self, request):
        """Affiche le formulaire ; sur POST valide, enregistre, envoie, puis redirige (PRG)."""
        form = ContactForm(request.POST) if request.method == "POST" else ContactForm()
        if request.method == "POST" and form.is_valid():
            submit_contact_form(form, get_contact_details(self, request)["email"])
            return redirect(self.url + self.reverse_subpage("thank_you"))
        status = 422 if form.is_bound else 200
        response = self.render(request, context_overrides={"form": form})
        response.status_code = status
        return response

    @path("thank-you/")
    def thank_you(self, request):
        """Page de confirmation (non indexée)."""
        return self.render(
            request,
            template="pages/contact_thank_you_page.html",
            context_overrides={"noindex": True},
        )
