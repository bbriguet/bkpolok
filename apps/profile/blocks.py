from wagtail import blocks

from . import services
from .models import Experience, MediaAppearance

TEMPLATE_DIR = "profile/blocks"


def _profile(context):
    request = context.get("request")
    return services.get_site_profile(request) if request else None


class TimelineBlock(blocks.StructBlock):
    """Chronologie alimentée par les entrées « Experience » d'une catégorie."""

    category = blocks.ChoiceBlock(choices=Experience.Category.choices, label="Category")

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        category = value["category"]
        context["label"] = services.timeline_label(category)
        context["entries"] = services.list_timeline(category, _profile(context))
        return context

    class Meta:
        icon = "history"
        label = "Experience timeline"
        template = f"{TEMPLATE_DIR}/timeline_block.html"


class EducationBlock(blocks.StructBlock):
    eyebrow = blocks.CharBlock(label="Eyebrow", required=False, default="Education")
    heading = blocks.CharBlock(label="Heading", default="Research training")

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        context["education"] = services.list_education()
        return context

    class Meta:
        icon = "doc-full"
        label = "Education"
        template = f"{TEMPLATE_DIR}/education_block.html"


class PublicationListBlock(blocks.StaticBlock):
    """Liste numérotée des publications (modèle « Publication »)."""

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        profile = _profile(context)
        context["publications"] = services.list_publications()
        context["pubmed_url"] = profile.pubmed_url if profile else ""
        return context

    class Meta:
        icon = "list-ol"
        label = "Publication list"
        admin_text = "Lists every publication, in the order set in Profile › Publications."
        template = f"{TEMPLATE_DIR}/publication_list_block.html"


class MediaListBlock(blocks.StructBlock):
    kind = blocks.ChoiceBlock(choices=MediaAppearance.Kind.choices, label="Kind")
    eyebrow = blocks.CharBlock(label="Eyebrow", required=False)
    heading = blocks.CharBlock(label="Heading")
    note = blocks.RichTextBlock(label="Note", required=False, features=["bold", "italic", "link"])

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        context["items"] = services.list_media(value["kind"])
        return context

    class Meta:
        icon = "media"
        label = "Media list"
        template = f"{TEMPLATE_DIR}/media_list_block.html"


class LanguagesBlock(blocks.StaticBlock):
    """Pastilles des langues parlées et légende des niveaux (modèle « Language »)."""

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        languages = services.list_languages()
        context["languages"] = languages
        context["caption"] = services.languages_caption(languages)
        return context

    class Meta:
        icon = "site"
        label = "Languages"
        admin_text = "Lists the languages set in Profile › Languages."
        template = f"{TEMPLATE_DIR}/languages_block.html"
