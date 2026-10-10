from wagtail import blocks

from . import services
from .models import Experience, MediaAppearance, Publication

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
        context["rows"] = services.timeline_rows(
            services.list_timeline(category, _profile(context))
        )
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
    """Ancienne liste de toutes les publications. Gardée pour les migrations qui la citent ;
    les pages utilisent `PublicationsBlock`."""

    class Meta:
        icon = "list-ol"
        label = "Publication list (old)"


class PublicationsBlock(blocks.StructBlock):
    """Publications d'une catégorie (modèle « Publication »).

    Les travaux de medical affairs sont des cartes mises en avant (★) ; les travaux de recherche
    une liste numérotée dont seules les premières sont visibles, les autres sous « voir plus ».
    """

    category = blocks.ChoiceBlock(
        choices=Publication.Category.choices,
        default=Publication.Category.RESEARCH,
        label="Category",
    )
    visible = blocks.IntegerBlock(
        label="Papers shown",
        min_value=0,
        default=0,
        required=False,
        help_text="The others sit under a “show more” button. 0 shows them all.",
    )
    more_label = blocks.CharBlock(
        label="“Show more” label",
        default="Show {count} more papers",
        required=False,
        help_text="{count} is replaced by the number of hidden papers.",
    )
    show_pubmed_link = blocks.BooleanBlock(
        label="Link to the full PubMed record",
        default=True,
        required=False,
        help_text="The address is set in the site profile.",
    )

    # Le type « publications » était un StaticBlock (valeur None) : les anciens corps de page,
    # révisions comprises, restent lisibles.
    def to_python(self, value):
        return super().to_python(value or {})

    def bulk_to_python(self, values):
        return super().bulk_to_python([value or {} for value in values])

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        profile = _profile(context)
        publications = services.list_publications(value["category"])
        visible = value["visible"] or len(publications)
        hidden = publications[visible:]
        context["featured"] = value["category"] == Publication.Category.MEDICAL_AFFAIRS
        context["publications"] = publications[:visible]
        context["more_publications"] = hidden
        context["more_label"] = (value["more_label"] or "Show {count} more papers").replace(
            "{count}", str(len(hidden))
        )
        context["more_start"] = visible + 1
        context["pubmed_url"] = profile.pubmed_url if profile and value["show_pubmed_link"] else ""
        return context

    class Meta:
        icon = "list-ol"
        label = "Publication list"
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
    """Légende des langues parlées et de leurs niveaux (modèle « Language »)."""

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        languages = services.list_languages()
        context["languages"] = languages
        context["caption"] = services.languages_caption(languages)
        return context

    class Meta:
        icon = "site"
        label = "Languages"
        admin_text = "Shows the languages set in Profile › Languages and their levels."
        template = f"{TEMPLATE_DIR}/languages_block.html"
