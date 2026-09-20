import json
from datetime import date

import pytest
from django.db import IntegrityError, transaction

from apps.profile import services
from apps.profile.models import (
    Education,
    Experience,
    ExperienceAchievement,
    ExperienceImage,
    Language,
    MediaAppearance,
    Publication,
)

pytestmark = pytest.mark.django_db

MONTH = Experience.DatePrecision.MONTH
YEAR = Experience.DatePrecision.YEAR


@pytest.mark.parametrize(
    ("start", "end", "precision", "expected"),
    [
        (date(2022, 12, 1), None, MONTH, "DEC 2022 — PRESENT"),
        (date(2010, 1, 1), date(2010, 3, 31), MONTH, "JAN — MAR 2010"),
        (date(2006, 9, 1), date(2009, 9, 30), MONTH, "SEP 2006 — SEP 2009"),
        (date(2010, 3, 1), date(2010, 3, 31), MONTH, "MAR 2010"),
        (date(2000, 1, 1), date(2006, 12, 31), YEAR, "2000 — 2006"),
        (date(2006, 1, 1), date(2006, 12, 31), YEAR, "2006"),
        (date(2020, 1, 1), None, YEAR, "2020 — PRESENT"),
    ],
)
def test_format_period(start, end, precision, expected):
    assert services.format_period(start, end, precision) == expected


def make_experience(**overrides):
    defaults = {
        "category": Experience.Category.INDUSTRY,
        "title": "Role",
        "organisation": "Acme",
        "start_date": date(2011, 4, 1),
    }
    return Experience.objects.create(**{**defaults, **overrides})


def test_org_line_joins_scope_and_focus():
    experience = make_experience(organisation="UCB", scope="Bulle", focus="Rheumatology")

    assert services.format_org_line(experience) == "UCB — Bulle · Rheumatology"
    assert services.format_org_line(make_experience(organisation="Solo")) == "Solo"


def test_timeline_label_uses_years_from_data():
    make_experience(start_date=date(2011, 4, 1), end_date=date(2016, 1, 31))
    make_experience(start_date=date(2022, 12, 1))
    make_experience(
        category=Experience.Category.RESEARCH,
        start_date=date(2000, 1, 1),
        end_date=date(2011, 3, 31),
    )

    assert services.timeline_label("industry") == "Industry — 2011 to present"
    assert services.timeline_label("research") == "Research — 2000 to 2011"


def test_timeline_is_newest_first_with_achievements_and_images(image, profile):
    old = make_experience(title="Old", start_date=date(2011, 4, 1), end_date=date(2016, 1, 31))
    new = make_experience(title="New", start_date=date(2022, 12, 1))
    ExperienceAchievement.objects.create(experience=new, text="Did a thing", sort_order=1)
    ExperienceImage.objects.create(
        experience=old,
        image=image,
        alt_text="A figure",
        caption="FIG. 1",
        link_url="https://example.org/x",
        link_label="Vendor",
    )

    entries = services.list_timeline("industry", profile)

    assert [e.experience.title for e in entries] == ["New", "Old"]
    assert entries[0].period == "DEC 2022 — PRESENT"
    assert entries[0].achievements == ["Did a thing"]
    assert entries[1].images[0].external is True
    assert entries[1].images[0].link_label == "Vendor"


def test_experience_end_before_start_is_rejected():
    from django.core.exceptions import ValidationError

    experience = Experience(
        category="industry",
        title="x",
        organisation="y",
        start_date=date(2020, 1, 1),
        end_date=date(2019, 1, 1),
    )

    with pytest.raises(ValidationError):
        experience.clean()


def test_publication_figure_link_points_to_the_publications_page(image, profile, home):
    from apps.pages.models import StandardPage

    page = home.add_child(instance=StandardPage(title="Publications", slug="pubs"))
    profile.publications_page = page
    profile.save()
    paper = Publication.objects.create(
        title="A paper", authors="Kotkamp K, Kur E, et al.", journal="PLoS One", year=2014
    )
    experience = make_experience()
    ExperienceImage.objects.create(
        experience=experience, image=image, alt_text="a", publication=paper
    )

    image_entry = services.list_timeline("industry", profile)[0].images[0]

    assert image_entry.link_label == "Kotkamp et al., 2014"
    assert image_entry.link_url == f"{page.url}#pub-{paper.pk}"
    assert image_entry.external is False


def test_publications_follow_sort_order_and_are_numbered():
    b = Publication.objects.create(
        title="B", authors="x", journal="J", year=2014, sort_order=2, pmid="222"
    )
    a = Publication.objects.create(title="A", authors="x", journal="J", year=2009, sort_order=1)

    entries = services.list_publications()

    assert [(e.number, e.publication.title) for e in entries] == [("01", "A"), ("02", "B")]
    assert entries[0].pubmed_url == ""
    assert entries[1].pubmed_url == "https://pubmed.ncbi.nlm.nih.gov/222/"
    assert entries[1].anchor == f"pub-{b.pk}"
    assert entries[0].anchor == f"pub-{a.pk}"


def test_pmid_is_unique_when_set_but_may_be_empty():
    Publication.objects.create(title="A", authors="x", journal="J", year=2009, pmid="1")
    Publication.objects.create(title="B", authors="x", journal="J", year=2009)
    Publication.objects.create(title="C", authors="x", journal="J", year=2009)

    with pytest.raises(IntegrityError), transaction.atomic():
        Publication.objects.create(title="D", authors="x", journal="J", year=2009, pmid="1")


def make_language(code, english, level, sort_order):
    return Language.objects.create(
        code=code, native_name=english, english_name=english, level=level, sort_order=sort_order
    )


def test_languages_caption_groups_consecutive_levels():
    make_language("pl", "Polish", "mother_tongue", 1)
    make_language("fr", "French", "full_professional", 2)
    make_language("en", "English", "full_professional", 3)
    make_language("de", "German", "full_professional", 4)
    make_language("it", "Italian", "intermediate", 5)

    assert services.languages_caption() == (
        "Polish (mother tongue) · French, English & German (full professional)"
        " · Italian (intermediate)"
    )
    assert services.language_codes() == ["PL", "FR", "EN", "DE", "IT"]


def test_display_url_strips_scheme_and_www():
    assert services.display_url("https://www.linkedin.com/in/x/") == "linkedin.com/in/x"
    assert services.display_url("http://example.ch") == "example.ch"


def test_person_jsonld_is_derived_from_the_data(profile):
    make_language("fr", "French", "full_professional", 1)
    Education.objects.create(degree="PhD", institution="University of X")

    data = services.build_person_jsonld(profile)

    assert data["@type"] == "Person"
    assert data["name"] == "Jane Q. Doe"
    assert data["alternateName"] == "Jane Doe"
    assert data["jobTitle"] == "Director"
    assert data["worksFor"] == {"@type": "Organization", "name": "Acme"}
    assert data["email"] == "mailto:jane@example.ch"
    assert data["sameAs"] == ["https://www.linkedin.com/in/jane-doe"]
    assert data["knowsLanguage"] == ["fr"]
    assert data["alumniOf"] == [{"@type": "CollegeOrUniversity", "name": "University of X"}]
    assert data["description"] == "A short description."


def test_person_jsonld_json_cannot_close_the_script_tag(profile):
    profile.job_title = "</script><script>alert(1)</script>"

    payload = services.person_jsonld_json(profile)

    assert "<" not in payload
    assert json.loads(payload)["jobTitle"] == "</script><script>alert(1)</script>"


def test_media_appearances_are_filtered_by_kind():
    MediaAppearance.objects.create(kind="tv", outlet="TV", title="A", sort_order=1)
    MediaAppearance.objects.create(kind="press", outlet="Paper", title="B", sort_order=1)

    assert [m.title for m in services.list_media("tv")] == ["A"]
    assert [m.title for m in services.list_media("press")] == ["B"]
