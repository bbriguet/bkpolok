from django.core.exceptions import ValidationError
from django.forms.utils import ErrorList
from wagtail import blocks
from wagtail.images.blocks import ImageBlock

TEMPLATE_DIR = "pages/blocks"


class HeadingBlock(blocks.StructBlock):
    text = blocks.CharBlock(label="Texte")
    level = blocks.ChoiceBlock(
        label="Niveau",
        choices=[("h2", "Titre (h2)"), ("h3", "Sous-titre (h3)")],
        default="h2",
    )

    class Meta:
        icon = "title"
        label = "Titre"
        template = f"{TEMPLATE_DIR}/heading_block.html"


class QuoteBlock(blocks.StructBlock):
    text = blocks.TextBlock(label="Citation")
    author = blocks.CharBlock(label="Auteur", required=False)

    class Meta:
        icon = "openquote"
        label = "Citation"
        template = f"{TEMPLATE_DIR}/quote_block.html"


class CallToActionBlock(blocks.StructBlock):
    title = blocks.CharBlock(label="Titre")
    text = blocks.TextBlock(label="Texte", required=False)
    button_label = blocks.CharBlock(label="Libellé du bouton")
    page = blocks.PageChooserBlock(label="Page interne", required=False)
    url = blocks.URLBlock(label="Lien externe", required=False)

    def clean(self, value):
        result = super().clean(value)
        if bool(result.get("page")) == bool(result.get("url")):
            message = "Renseignez soit une page interne, soit un lien externe (pas les deux)."
            raise blocks.StructBlockValidationError(
                block_errors={
                    "page": ErrorList([ValidationError(message)]),
                    "url": ErrorList([ValidationError(message)]),
                }
            )
        return result

    class Meta:
        icon = "link"
        label = "Appel à l’action"
        template = f"{TEMPLATE_DIR}/call_to_action_block.html"


class FAQItemBlock(blocks.StructBlock):
    question = blocks.CharBlock(label="Question")
    answer = blocks.RichTextBlock(label="Réponse", features=["bold", "italic", "link", "ul", "ol"])


class FAQBlock(blocks.StructBlock):
    title = blocks.CharBlock(label="Titre", required=False, default="Questions fréquentes")
    items = blocks.ListBlock(FAQItemBlock(), label="Questions", min_num=1)

    class Meta:
        icon = "help"
        label = "FAQ"
        template = f"{TEMPLATE_DIR}/faq_block.html"


class BodyStreamBlock(blocks.StreamBlock):
    heading = HeadingBlock()
    paragraph = blocks.RichTextBlock(
        label="Texte riche",
        icon="pilcrow",
        features=["bold", "italic", "h3", "h4", "ul", "ol", "link", "hr"],
    )
    image = ImageBlock(label="Image", template=f"{TEMPLATE_DIR}/image_block.html")
    quote = QuoteBlock()
    call_to_action = CallToActionBlock()
    faq = FAQBlock()
