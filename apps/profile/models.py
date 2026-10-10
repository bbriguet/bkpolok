from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.db.models import Q
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel, PageChooserPanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.fields import RichTextField
from wagtail.models import Orderable

YEAR_VALIDATORS = [MinValueValidator(1900), MaxValueValidator(2100)]
LANGUAGE_CODE_VALIDATOR = RegexValidator(
    r"^[a-z]{2}$", "Use a two-letter lowercase ISO 639-1 code."
)


@register_setting(icon="user")
class SiteProfile(BaseSiteSetting):
    """Identité et coordonnées de la personne, réutilisées sur tout le site."""

    first_name = models.CharField(max_length=60)
    last_name = models.CharField(max_length=60)
    short_name = models.CharField(
        max_length=40,
        help_text="Name shown in the navigation bar, e.g. “B. Polok”.",
    )
    legal_name = models.CharField(
        max_length=120,
        help_text="Full name, used in the copyright line and in structured data.",
    )
    name_language = models.CharField(
        max_length=2,
        blank=True,
        validators=[LANGUAGE_CODE_VALIDATOR],
        help_text="Language of the name, for screen readers (ISO 639-1, e.g. “pl”).",
    )
    job_title = models.CharField(max_length=120, blank=True)
    employer = models.CharField(max_length=120, blank=True)
    email = models.EmailField()
    linkedin_url = models.URLField("LinkedIn URL", blank=True)
    pubmed_url = models.URLField(
        "PubMed URL",
        blank=True,
        help_text="Link to the full publication record, shown under the publication list.",
    )
    publications_page = models.ForeignKey(
        "wagtailcore.Page",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Page that lists the publications. Figure captions in the timeline link to it.",
    )
    footer_heading = models.CharField(
        max_length=120,
        blank=True,
        help_text="Heading of the contact block in the footer.",
    )
    footer_lede = models.TextField(
        max_length=300,
        blank=True,
        help_text="Sentence under the footer heading.",
    )
    accessibility_statement = RichTextField(
        features=["bold", "italic", "link"],
        blank=True,
        help_text="Shown in the footer of every page, under the heading “Accessibility”.",
    )
    legal_notice_page = models.ForeignKey(
        "wagtailcore.Page",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Linked from the footer of every page.",
    )
    privacy_page = models.ForeignKey(
        "wagtailcore.Page",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Linked from the footer of every page.",
    )
    copyright_notice = models.CharField(
        max_length=250,
        blank=True,
        help_text="Sentence after “© <year> <legal name>.” in the footer.",
    )
    meta_description = models.TextField(
        max_length=300,
        blank=True,
        help_text="Short description of the person: structured data and default meta description.",
    )
    share_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Default image when a page is shared (Open Graph); 1200×630 works best.",
    )

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("first_name"),
                FieldPanel("last_name"),
                FieldPanel("short_name"),
                FieldPanel("legal_name"),
                FieldPanel("name_language"),
            ],
            heading="Name",
        ),
        MultiFieldPanel(
            [
                FieldPanel("job_title"),
                FieldPanel("employer"),
                FieldPanel("meta_description"),
                FieldPanel("share_image"),
            ],
            heading="Position",
        ),
        MultiFieldPanel(
            [
                FieldPanel("email"),
                FieldPanel("linkedin_url"),
                FieldPanel("pubmed_url"),
                PageChooserPanel("publications_page"),
            ],
            heading="Contact and links",
        ),
        MultiFieldPanel(
            [
                FieldPanel("footer_heading"),
                FieldPanel("footer_lede"),
                FieldPanel("accessibility_statement"),
                PageChooserPanel("legal_notice_page"),
                PageChooserPanel("privacy_page"),
                FieldPanel("copyright_notice"),
            ],
            heading="Footer",
        ),
    ]

    class Meta:
        ordering = ["site_id"]
        verbose_name = "profil du site"
        verbose_name_plural = "profils du site"

    def __str__(self):
        return self.display_name or f"Profil du site {self.site_id}"

    @property
    def display_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


class Language(models.Model):
    class Level(models.TextChoices):
        MOTHER_TONGUE = "mother_tongue", "Mother tongue"
        FULL_PROFESSIONAL = "full_professional", "Full professional"
        INTERMEDIATE = "intermediate", "Intermediate"

    code = models.CharField(
        max_length=2,
        unique=True,
        validators=[LANGUAGE_CODE_VALIDATOR],
        help_text="ISO 639-1 code, e.g. “pl”.",
    )
    native_name = models.CharField(max_length=40, help_text="e.g. “Français”.")
    english_name = models.CharField(max_length=40, help_text="e.g. “French”.")
    level = models.CharField(max_length=20, choices=Level.choices)
    sort_order = models.PositiveSmallIntegerField(default=0)

    panels = [
        FieldPanel("code"),
        FieldPanel("native_name"),
        FieldPanel("english_name"),
        FieldPanel("level"),
        FieldPanel("sort_order"),
    ]

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "langue"
        verbose_name_plural = "langues"

    def __str__(self):
        return self.english_name


class Experience(ClusterableModel):
    class Category(models.TextChoices):
        INDUSTRY = "industry", "Industry"
        RESEARCH = "research", "Research"

    class DatePrecision(models.TextChoices):
        MONTH = "month", "Month and year"
        YEAR = "year", "Year only"

    category = models.CharField(max_length=10, choices=Category.choices)
    title = models.CharField(max_length=150)
    organisation = models.CharField(max_length=120)
    scope = models.CharField(
        max_length=200,
        blank=True,
        help_text="Place, markets or division, e.g. “Vernier, Switzerland”.",
    )
    focus = models.CharField(
        max_length=150,
        blank=True,
        help_text="Therapeutic or technical focus, e.g. “Gastroenterology & Rheumatology”.",
    )
    parallel_role = models.CharField(
        max_length=150,
        blank=True,
        help_text="Role held at the same time, shown as “In parallel: …”.",
    )
    organisation_description = models.TextField(blank=True)
    summary = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Leave empty for a current position.",
    )
    date_precision = models.CharField(
        max_length=5,
        choices=DatePrecision.choices,
        default=DatePrecision.MONTH,
        help_text="How the period is displayed: “Dec 2022 — present” or “2000 — 2006”.",
    )
    pair_with_next = models.BooleanField(
        "Share images with the next entry",
        default=False,
        help_text="Shows this entry's images in one column beside it and the next (older) entry.",
    )

    panels = [
        FieldPanel("category"),
        FieldPanel("title"),
        FieldPanel("organisation"),
        FieldPanel("scope"),
        FieldPanel("focus"),
        FieldPanel("parallel_role"),
        FieldPanel("organisation_description"),
        FieldPanel("summary"),
        FieldPanel("start_date"),
        FieldPanel("end_date"),
        FieldPanel("date_precision"),
        InlinePanel("achievements", label="Achievements"),
        InlinePanel("images", label="Images"),
        FieldPanel("pair_with_next"),
    ]

    class Meta:
        ordering = ["-start_date", "-id"]
        verbose_name = "expérience"
        verbose_name_plural = "expériences"

    def __str__(self):
        return f"{self.title} — {self.organisation}"

    def clean(self):
        super().clean()
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "The end date cannot be before the start date."})


class ExperienceAchievement(Orderable):
    experience = ParentalKey(Experience, on_delete=models.CASCADE, related_name="achievements")
    text = models.CharField(max_length=300)
    publication = models.ForeignKey(
        "Publication",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Paper that the words below link to.",
    )
    link_text = models.CharField(
        max_length=80,
        blank=True,
        help_text="Words of the text that link to the paper, e.g. “Munk et al. (2022)”.",
    )

    panels = [FieldPanel("text"), FieldPanel("publication"), FieldPanel("link_text")]

    class Meta(Orderable.Meta):
        verbose_name = "réalisation"
        verbose_name_plural = "réalisations"

    def __str__(self):
        return self.text

    def clean(self):
        super().clean()
        if self.link_text and self.publication_id is None:
            raise ValidationError({"publication": "Choose the paper that the words link to."})
        if self.publication_id is not None and not self.link_text:
            raise ValidationError({"link_text": "Type the words that link to the paper."})
        if self.link_text and self.link_text not in self.text:
            raise ValidationError({"link_text": "These words must appear as is in the text."})


class Publication(models.Model):
    class Category(models.TextChoices):
        MEDICAL_AFFAIRS = "medical_affairs", "Medical affairs work"
        RESEARCH = "research", "Research"

    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.RESEARCH,
        help_text="Medical affairs papers are highlighted (★); research papers are numbered.",
    )
    title = models.CharField(max_length=300)
    authors = models.CharField(
        max_length=300, help_text="As printed, e.g. “Polok B, Escher P, et al.”."
    )
    journal = models.CharField(max_length=120)
    year = models.PositiveSmallIntegerField(validators=YEAR_VALIDATORS)
    pmid = models.CharField(
        "PMID",
        max_length=12,
        blank=True,
        validators=[RegexValidator(r"^\d+$", "A PMID contains digits only.")],
        help_text="PubMed identifier. The PubMed link is built from it.",
    )
    note = models.TextField(
        blank=True,
        help_text="Optional sentence shown under the reference (highlighted papers).",
    )
    sort_order = models.PositiveSmallIntegerField(
        default=0,
        help_text="Display order; the number shown next to each paper follows it, per category.",
    )

    panels = [
        FieldPanel("category"),
        FieldPanel("title"),
        FieldPanel("authors"),
        FieldPanel("journal"),
        FieldPanel("year"),
        FieldPanel("pmid"),
        FieldPanel("note"),
        FieldPanel("sort_order"),
    ]

    class Meta:
        ordering = ["category", "sort_order", "id"]
        verbose_name = "publication"
        verbose_name_plural = "publications"
        constraints = [
            models.UniqueConstraint(
                fields=["pmid"],
                condition=~Q(pmid=""),
                name="profile_publication_unique_pmid",
            )
        ]

    def __str__(self):
        return f"{self.title} ({self.year})"


class ExperienceImage(Orderable):
    experience = ParentalKey(Experience, on_delete=models.CASCADE, related_name="images")
    image = models.ForeignKey("wagtailimages.Image", on_delete=models.CASCADE, related_name="+")
    alt_text = models.CharField(max_length=250)
    caption = models.CharField(max_length=60, blank=True, help_text="e.g. “FIG. 1”.")
    publication = models.ForeignKey(
        Publication,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Links the caption to this paper (label built from its first author and year).",
    )
    link_label = models.CharField(
        max_length=80,
        blank=True,
        help_text="Overrides the caption link label. An arrow is added automatically.",
    )
    link_url = models.URLField(
        blank=True,
        help_text="External link, used when no publication is selected.",
    )

    panels = [
        FieldPanel("image"),
        FieldPanel("alt_text"),
        FieldPanel("caption"),
        FieldPanel("publication"),
        FieldPanel("link_label"),
        FieldPanel("link_url"),
    ]

    class Meta(Orderable.Meta):
        verbose_name = "image d’expérience"
        verbose_name_plural = "images d’expérience"

    def __str__(self):
        return self.caption or self.alt_text


class Education(models.Model):
    degree = models.CharField(max_length=150)
    institution = models.CharField(max_length=150)
    year = models.PositiveSmallIntegerField(null=True, blank=True, validators=YEAR_VALIDATORS)
    description = models.TextField(blank=True)
    listed = models.BooleanField(
        "Show as a card",
        default=True,
        help_text="Unticked: kept for structured data (alumniOf) but not shown, e.g. a degree "
        "already in the timeline.",
    )
    sort_order = models.PositiveSmallIntegerField(default=0)

    panels = [
        FieldPanel("degree"),
        FieldPanel("institution"),
        FieldPanel("year"),
        FieldPanel("description"),
        FieldPanel("listed"),
        FieldPanel("sort_order"),
    ]

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "formation"
        verbose_name_plural = "formations"

    def __str__(self):
        return f"{self.degree} — {self.institution}"


class MediaAppearance(models.Model):
    class Kind(models.TextChoices):
        TELEVISION = "tv", "Television"
        PRESS = "press", "Press"

    kind = models.CharField(max_length=5, choices=Kind.choices)
    outlet = models.CharField(max_length=80, help_text="e.g. “TSR”, “swissinfo.ch”.")
    title = models.CharField(
        max_length=200,
        help_text="Displayed inside quotation marks; no need to type them.",
    )
    title_language = models.CharField(
        max_length=2,
        blank=True,
        validators=[LANGUAGE_CODE_VALIDATOR],
        help_text="Language of the title as written, if not English (ISO 639-1, e.g. “fr”).",
    )
    date = models.DateField(null=True, blank=True, help_text="Leave empty if unknown.")
    url = models.URLField(blank=True)
    language = models.CharField(
        max_length=2,
        blank=True,
        validators=[LANGUAGE_CODE_VALIDATOR],
        help_text="Language of the linked page or video, if not English (announced to "
        "screen readers).",
    )
    sort_order = models.PositiveSmallIntegerField(default=0)

    panels = [
        FieldPanel("kind"),
        FieldPanel("outlet"),
        FieldPanel("title"),
        FieldPanel("title_language"),
        FieldPanel("date"),
        FieldPanel("url"),
        FieldPanel("language"),
        FieldPanel("sort_order"),
    ]

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "apparition médiatique"
        verbose_name_plural = "apparitions médiatiques"

    def __str__(self):
        return f"{self.outlet} — {self.title}"
