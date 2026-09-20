from django.core.exceptions import ValidationError
from django.forms.utils import ErrorList
from wagtail import blocks
from wagtail.images.blocks import ImageBlock

from apps.profile import services as profile_services
from apps.profile.blocks import (
    EducationBlock,
    LanguagesBlock,
    MediaListBlock,
    PublicationListBlock,
    TimelineBlock,
)
from apps.services.services import list_live_services

from .icons import icon_choices
from .services import button_props, offer_items

TEMPLATE_DIR = "pages/blocks"

BUTTON_VARIANTS = [("primary", "Primary"), ("ghost", "Ghost")]


def _require_page_or_url(result):
    """Un lien est soit une page interne, soit une URL externe, jamais les deux ni aucun."""
    if bool(result.get("page")) == bool(result.get("url")):
        message = "Fill in either an internal page or an external link (not both)."
        raise blocks.StructBlockValidationError(
            block_errors={
                "page": ErrorList([ValidationError(message)]),
                "url": ErrorList([ValidationError(message)]),
            }
        )


class HeadingBlock(blocks.StructBlock):
    """Tête de section : eyebrow, titre, chapeau, pastilles et photo ronde optionnels."""

    eyebrow = blocks.CharBlock(label="Eyebrow", required=False)
    text = blocks.CharBlock(label="Text")
    level = blocks.ChoiceBlock(
        label="Level",
        choices=[("h2", "Heading (h2)"), ("h3", "Subheading (h3)")],
        default="h2",
    )
    lede = blocks.TextBlock(label="Lede", required=False, rows=2)
    pills = blocks.ListBlock(blocks.CharBlock(label="Pill"), label="Pills", required=False)
    image = ImageBlock(label="Round photo", required=False)

    class Meta:
        icon = "title"
        label = "Section heading"
        template = f"{TEMPLATE_DIR}/heading_block.html"


class ButtonBlock(blocks.StructBlock):
    label = blocks.CharBlock(label="Label")
    page = blocks.PageChooserBlock(label="Internal page", required=False)
    url = blocks.URLBlock(label="External link", required=False)
    variant = blocks.ChoiceBlock(label="Style", choices=BUTTON_VARIANTS, default="primary")

    def clean(self, value):
        result = super().clean(value)
        _require_page_or_url(result)
        return result

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        context["button"] = button_props(value, context.get("request"))
        return context

    class Meta:
        icon = "link"
        label = "Button"
        template = f"{TEMPLATE_DIR}/button_block.html"


class HeroBlock(blocks.StructBlock):
    """Bandeau d'accueil. Le nom (h1) vient du profil du site."""

    eyebrow = blocks.CharBlock(label="Eyebrow", required=False)
    role = blocks.CharBlock(label="Role")
    badge_text = blocks.CharBlock(label="Status badge", required=False)
    thesis = blocks.TextBlock(label="Introduction")
    buttons = blocks.ListBlock(ButtonBlock(), label="Buttons", max_num=3, required=False)
    image = ImageBlock(label="Portrait", required=False)

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        request = context.get("request")
        context["profile"] = profile_services.get_site_profile(request) if request else None
        context["buttons"] = [button_props(button, request) for button in value["buttons"]]
        return context

    class Meta:
        icon = "user"
        label = "Hero"
        template = f"{TEMPLATE_DIR}/hero_block.html"


class QuoteBlock(blocks.StructBlock):
    text = blocks.TextBlock(label="Quote")
    author = blocks.CharBlock(label="Author", required=False)

    class Meta:
        icon = "openquote"
        label = "Pull quote"
        template = f"{TEMPLATE_DIR}/quote_block.html"


class CallToActionBlock(blocks.StructBlock):
    title = blocks.CharBlock(label="Title")
    text = blocks.TextBlock(label="Text", required=False)
    button_label = blocks.CharBlock(label="Button label")
    page = blocks.PageChooserBlock(label="Internal page", required=False)
    url = blocks.URLBlock(label="External link", required=False)
    variant = blocks.ChoiceBlock(label="Button style", choices=BUTTON_VARIANTS, default="primary")

    def clean(self, value):
        result = super().clean(value)
        _require_page_or_url(result)
        return result

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        context["button"] = button_props(value, context.get("request"), label_key="button_label")
        return context

    class Meta:
        icon = "link"
        label = "Call to action"
        template = f"{TEMPLATE_DIR}/call_to_action_block.html"


class CardBlock(blocks.StructBlock):
    icon = blocks.ChoiceBlock(label="Icon", choices=icon_choices, required=False)
    title = blocks.CharBlock(label="Title")
    text = blocks.TextBlock(label="Text")
    wide = blocks.BooleanBlock(
        label="Span two columns",
        required=False,
        help_text="Only used by the “Off the clock” layout.",
    )


class CardGridBlock(blocks.StructBlock):
    variant = blocks.ChoiceBlock(
        label="Layout",
        choices=[
            ("service", "Service cards (teal icons, sans-serif titles)"),
            ("off_duty", "Off the clock cards (amber icons, serif titles)"),
        ],
        default="service",
    )
    cards = blocks.ListBlock(CardBlock(), label="Cards", min_num=1)

    class Meta:
        icon = "grip"
        label = "Card grid"
        template = f"{TEMPLATE_DIR}/card_grid_block.html"


class AsideNoteBlock(blocks.StructBlock):
    icon = blocks.ChoiceBlock(label="Icon", choices=icon_choices, required=False)
    text = blocks.TextBlock(label="Text")


class AsideNotesBlock(blocks.StructBlock):
    notes = blocks.ListBlock(AsideNoteBlock(), label="Notes", min_num=1, max_num=2)

    class Meta:
        icon = "info-circle"
        label = "Aside notes"
        help_text = "One note, or two side by side."
        template = f"{TEMPLATE_DIR}/aside_notes_block.html"


class ServiceOfferBlock(blocks.StructBlock):
    """Encadré listant automatiquement les pages de service enfants d'une page d'index."""

    lead = blocks.CharBlock(label="Lead sentence")
    index_page = blocks.PageChooserBlock(
        label="Services index page", page_type="services.ServiceIndexPage"
    )

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        index_page = value["index_page"]
        pages = list_live_services(index_page.specific) if index_page else []
        context["offers"] = offer_items(pages, context.get("request"))
        return context

    class Meta:
        icon = "list-ul"
        label = "Service offers"
        template = f"{TEMPLATE_DIR}/service_offer_block.html"


class FAQItemBlock(blocks.StructBlock):
    question = blocks.CharBlock(label="Question")
    answer = blocks.RichTextBlock(label="Answer", features=["bold", "italic", "link", "ul", "ol"])


class FAQBlock(blocks.StructBlock):
    title = blocks.CharBlock(label="Title", required=False, default="Frequently asked questions")
    items = blocks.ListBlock(FAQItemBlock(), label="Questions", min_num=1)

    class Meta:
        icon = "help"
        label = "FAQ"
        template = f"{TEMPLATE_DIR}/faq_block.html"


class ContentStreamBlock(blocks.StreamBlock):
    """Blocs de contenu, utilisables à plat ou dans une section."""

    hero = HeroBlock()
    heading = HeadingBlock()
    paragraph = blocks.RichTextBlock(
        label="Rich text",
        icon="pilcrow",
        features=["bold", "italic", "h3", "h4", "ul", "ol", "link", "hr"],
        template=f"{TEMPLATE_DIR}/paragraph_block.html",
    )
    image = ImageBlock(label="Image", template=f"{TEMPLATE_DIR}/image_block.html")
    quote = QuoteBlock()
    call_to_action = CallToActionBlock()
    cards = CardGridBlock()
    aside_notes = AsideNotesBlock()
    offers = ServiceOfferBlock()
    faq = FAQBlock()
    languages = LanguagesBlock()
    timeline = TimelineBlock()
    education = EducationBlock()
    publications = PublicationListBlock()
    media = MediaListBlock()


class SectionBlock(blocks.StructBlock):
    """Bande de page : ancre optionnelle, fond par défaut ou teinté, et des blocs de contenu."""

    anchor = blocks.RegexBlock(
        regex=r"^[a-z][a-z0-9-]*$",
        label="Anchor",
        required=False,
        help_text="Optional id for in-page links, e.g. “contact” (lowercase, digits, hyphens).",
        error_messages={
            "invalid": "Use lowercase letters, digits and hyphens, starting with a letter."
        },
    )
    background = blocks.ChoiceBlock(
        label="Background",
        choices=[("default", "Default"), ("tint", "Tinted")],
        default="default",
    )
    content = ContentStreamBlock(label="Content")

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        # `includes/section.html` reçoit le contenu déjà rendu (include_block ne sait pas « as »).
        context["content"] = value["content"].render_as_block(context=context)
        return context

    class Meta:
        icon = "form"
        label = "Section"
        template = f"{TEMPLATE_DIR}/section_block.html"


class BodyStreamBlock(ContentStreamBlock):
    section = SectionBlock()

    class Meta:
        block_counts = {"hero": {"max_num": 1}}
