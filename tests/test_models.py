"""Chaque modèle : création, libellés français, ordre, admin Wagtail, page qui le liste."""

import json
from datetime import date

import pytest
from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse

from apps.pages.models import ContactPage, HomePage, StandardPage
from apps.profile.models import (
    Education,
    Experience,
    ExperienceAchievement,
    ExperienceImage,
    Language,
    MediaAppearance,
    Publication,
    SiteProfile,
)
from apps.services.models import ServiceIndexPage, ServicePage

pytestmark = pytest.mark.django_db

DATA_MODELS = [
    SiteProfile,
    Language,
    Experience,
    ExperienceAchievement,
    ExperienceImage,
    Publication,
    Education,
    MediaAppearance,
]
PAGE_MODELS = [HomePage, StandardPage, ServiceIndexPage, ServicePage, ContactPage]


def html_of(client, page) -> str:
    response = client.get(page.url)
    assert response.status_code == 200
    return response.content.decode()


def page_with(home, *blocks) -> StandardPage:
    body = json.dumps([{"type": t, "value": v} for t, v in blocks])
    return home.add_child(instance=StandardPage(title="Page", slug="page", body=body))


@pytest.fixture
def admin_client(client):
    user = get_user_model().objects.create_superuser("admin", "admin@example.ch", "pw")
    client.force_login(user)
    return client


# ------------------------------------------------------------------ création


def test_create_site_profile(profile):
    profile.refresh_from_db()

    assert str(profile) == "Jane Doe"
    assert SiteProfile.objects.get(site=profile.site) == profile


def test_create_language():
    language = Language.objects.create(
        code="fr",
        native_name="Français",
        english_name="French",
        level=Language.Level.FULL_PROFESSIONAL,
    )

    assert str(language) == "French"
    assert language.sort_order == 0


def test_create_experience_with_achievement_and_image(image):
    experience = Experience.objects.create(
        category=Experience.Category.RESEARCH,
        title="Researcher",
        organisation="University of X",
        start_date=date(2000, 1, 1),
        end_date=date(2006, 12, 31),
        date_precision=Experience.DatePrecision.YEAR,
    )
    achievement = ExperienceAchievement.objects.create(experience=experience, text="A result")
    figure = ExperienceImage.objects.create(
        experience=experience, image=image, alt_text="A figure", caption="FIG. 1"
    )

    assert str(experience) == "Researcher — University of X"
    assert str(achievement) == "A result"
    assert str(figure) == "FIG. 1"
    assert str(ExperienceImage(alt_text="Only alt")) == "Only alt"
    assert list(experience.achievements.all()) == [achievement]
    assert list(experience.images.all()) == [figure]


def test_create_publication():
    publication = Publication.objects.create(
        title="A paper", authors="Doe J", journal="Nature", year=2014, pmid="123"
    )

    assert str(publication) == "A paper (2014)"


def test_create_education():
    education = Education.objects.create(degree="PhD", institution="University of X", year=2006)

    assert str(education) == "PhD — University of X"


def test_create_media_appearance():
    media = MediaAppearance.objects.create(kind="tv", outlet="TSR", title="News item")

    assert str(media) == "TSR — News item"
    assert media.date is None


def test_create_every_page_type(home):
    index = home.add_child(instance=ServiceIndexPage(title="Expertise", slug="expertise"))
    service = index.add_child(instance=ServicePage(title="Offer", slug="offer", summary="S"))
    standard = home.add_child(instance=StandardPage(title="About", slug="about"))
    contact = home.add_child(
        instance=ContactPage(title="Contact", slug="contact", email="a@b.ch", phone="+41 21 1")
    )

    assert [str(p) for p in (home, index, service, standard, contact)] == [
        home.title,
        "Expertise",
        "Offer",
        "About",
        "Contact",
    ]


# ------------------------------------------------------------------ conventions


FRENCH_LABELS = {
    SiteProfile: ("profil du site", "profils du site"),
    Language: ("langue", "langues"),
    Experience: ("expérience", "expériences"),
    ExperienceAchievement: ("réalisation", "réalisations"),
    ExperienceImage: ("image d’expérience", "images d’expérience"),
    Publication: ("publication", "publications"),
    Education: ("formation", "formations"),
    MediaAppearance: ("apparition médiatique", "apparitions médiatiques"),
    HomePage: ("page d’accueil", "pages d’accueil"),
    StandardPage: ("page standard", "pages standard"),
    ServiceIndexPage: ("page d’index des services", "pages d’index des services"),
    ServicePage: ("page de service", "pages de service"),
    ContactPage: ("page de contact", "pages de contact"),
}


@pytest.mark.parametrize("model", FRENCH_LABELS, ids=lambda m: m.__name__)
def test_verbose_names_are_in_french(model):
    assert (model._meta.verbose_name, model._meta.verbose_name_plural) == FRENCH_LABELS[model]


@pytest.mark.parametrize("model", DATA_MODELS, ids=lambda m: m.__name__)
def test_data_models_have_an_explicit_ordering(model):
    assert model._meta.ordering


def test_no_float_field_in_the_project_models():
    project_models = [m for m in apps.get_models() if m.__module__.startswith("apps.")]
    float_fields = [
        f"{m.__name__}.{f.name}"
        for m in project_models
        for f in m._meta.get_fields()
        if f.get_internal_type() == "FloatField"
    ]

    assert float_fields == []


@pytest.mark.parametrize(
    ("model", "field"),
    [
        (SiteProfile, "linkedin_url"),
        (SiteProfile, "pubmed_url"),
        (ExperienceImage, "link_url"),
        (MediaAppearance, "url"),
    ],
)
def test_urls_use_url_fields(model, field):
    assert isinstance(model._meta.get_field(field), models.URLField)


# ------------------------------------------------------------------ admin Wagtail


@pytest.mark.parametrize(
    "model",
    [Experience, Publication, Education, MediaAppearance, Language],
    ids=lambda m: m.__name__,
)
def test_snippet_admin_lists_and_creates(admin_client, model):
    label = model._meta.app_label, model._meta.model_name
    namespace = f"wagtailsnippets_{label[0]}_{label[1]}"

    listing = admin_client.get(reverse(f"{namespace}:list"))
    add = admin_client.get(reverse(f"{namespace}:add"))

    assert listing.status_code == 200
    assert add.status_code == 200


def test_snippet_admin_shows_french_names(admin_client, home):
    Publication.objects.create(title="A paper", authors="Doe J", journal="Nature", year=2014)

    html = admin_client.get(reverse("wagtailsnippets_profile_publication:list")).content.decode()

    assert "A paper" in html
    assert "Publications" in html


def test_experience_admin_form_edits_its_inline_models(admin_client):
    html = admin_client.get(reverse("wagtailsnippets_profile_experience:add")).content.decode()

    assert "achievements" in html and "images" in html


def test_site_profile_is_editable_as_a_site_setting(admin_client, profile):
    url = reverse("wagtailsettings:edit", args=["profile", "siteprofile", profile.site_id])

    response = admin_client.get(url)

    assert response.status_code == 200
    assert "Jane" in response.content.decode()


@pytest.mark.parametrize("page_model", PAGE_MODELS, ids=lambda m: m.__name__)
def test_page_types_can_be_created_from_the_page_admin(admin_client, home, page_model):
    if page_model is HomePage:
        pytest.skip("la page d’accueil est unique (max_count = 1) et existe déjà")
    parent = home
    if page_model is ServicePage:
        parent = home.add_child(instance=ServiceIndexPage(title="Expertise", slug="expertise"))
    ct = page_model._meta
    url = reverse("wagtailadmin_pages:add", args=[ct.app_label, ct.model_name, parent.pk])

    assert admin_client.get(url).status_code == 200


# ------------------------------------------------------------------ pages qui listent les modèles


def test_home_page_renders_profile_and_languages(client, home, profile):
    Language.objects.create(
        code="pl", native_name="Polski", english_name="Polish", level="mother_tongue"
    )

    html = html_of(client, home)

    assert "J. Doe" in html  # SiteProfile.short_name (navigation)
    assert "jane@example.ch" in html
    assert "Let&#x27;s talk." in html or "Let's talk." in html
    assert ">PL<" in html.replace(" ", "")  # Language.code dans le pied de page


def test_standard_page_renders_the_languages_block(client, home):
    Language.objects.create(
        code="fr", native_name="Français", english_name="French", level="full_professional"
    )
    page = page_with(home, ("languages", None))

    html = html_of(client, page)

    assert "Français" in html
    assert "French (full professional)" in html


def test_timeline_page_lists_experiences_achievements_and_images(client, home, profile, image):
    experience = Experience.objects.create(
        category="industry", title="Director", organisation="Acme", start_date=date(2022, 12, 1)
    )
    ExperienceAchievement.objects.create(experience=experience, text="Grew the team")
    ExperienceImage.objects.create(
        experience=experience, image=image, alt_text="Figure alt", caption="FIG. 1"
    )
    page = page_with(home, ("timeline", {"category": "industry"}))

    html = html_of(client, page)

    assert "Director" in html and "Acme" in html
    assert "Grew the team" in html
    assert "Figure alt" in html and "FIG. 1" in html
    assert "DEC 2022" in html


def test_publications_page_lists_publications(client, home, profile):
    Publication.objects.create(title="A paper", authors="Doe J", journal="Nature", year=2014)
    page = page_with(home, ("publications", None))

    html = html_of(client, page)

    assert "A paper" in html and "Nature" in html


def test_education_page_lists_education(client, home):
    Education.objects.create(degree="PhD", institution="University of X", year=2006)
    page = page_with(home, ("education", {"eyebrow": "Education", "heading": "Training"}))

    html = html_of(client, page)

    assert "PhD" in html and "University of X" in html


def test_media_page_lists_media_appearances(client, home):
    MediaAppearance.objects.create(
        kind="press", outlet="Paper", title="An article", date=date(2008, 5, 19)
    )
    page = page_with(
        home, ("media", {"kind": "press", "eyebrow": "", "heading": "Press", "note": ""})
    )

    html = html_of(client, page)

    assert "An article" in html and "Paper" in html
    assert "19.05.2008" in html


def test_service_index_page_lists_its_services(client, home):
    index = home.add_child(instance=ServiceIndexPage(title="Expertise", slug="expertise"))
    index.add_child(instance=ServicePage(title="Offer", slug="offer", summary="What it is"))

    html = html_of(client, index)

    assert "Offer" in html and "What it is" in html


def test_service_page_renders(client, home):
    index = home.add_child(instance=ServiceIndexPage(title="Expertise", slug="expertise"))
    service = index.add_child(instance=ServicePage(title="Offer", slug="offer", summary="S"))

    assert "Offer" in html_of(client, service)


def test_contact_page_renders_its_details(client, home, profile):
    contact = home.add_child(
        instance=ContactPage(
            title="Contact",
            slug="contact",
            email="info@example.ch",
            phone="+41 21 123 45 67",
            address="Rue 1\n1000 Lausanne",
        )
    )

    html = html_of(client, contact)

    assert "info@example.ch" in html
    assert "+41 21 123 45 67" in html
    assert "1000 Lausanne" in html
