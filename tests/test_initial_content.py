import re
from datetime import date
from io import StringIO
from pathlib import Path

import pytest
import yaml
from django.conf import settings
from django.core.management import CommandError, call_command
from wagtail.models import Page, Revision

from apps.pages.initial_content import (
    ContentError,
    load_initial_content,
    parse_language_levels,
    parse_media_date,
    parse_period,
    split_org_line,
)
from apps.pages.models import HomePage
from apps.profile.models import (
    Education,
    Experience,
    ExperienceAchievement,
    Language,
    MediaAppearance,
    Publication,
    SiteProfile,
)
from apps.profile.services import format_org_line

pytestmark = pytest.mark.django_db

CONTENT = Path(settings.BASE_DIR) / "_artifact" / "design" / "content.yaml"
PAGE_SLUGS = ["about", "expertise", "experience", "publications", "personal", "contact"]


@pytest.fixture
def loaded(home):
    return load_initial_content(CONTENT)


def page_at(home, *slugs):
    """Page relue en base : la fixture `home` est périmée dès que la commande crée des pages."""
    page = HomePage.objects.get(pk=home.pk)
    for slug in slugs:
        page = page.get_children().get(slug=slug)
    return page.specific


def content_with(tmp_path, old: str, new: str) -> Path:
    """Copie de content.yaml dont un texte est remplacé (le test échoue si `old` a disparu)."""
    text = CONTENT.read_text(encoding="utf-8")
    assert old in text, old
    path = tmp_path / "content.yaml"
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    return path


def publish_all(home):
    for page in Page.objects.descendant_of(home, inclusive=True):
        page.specific.save_revision().publish()


# ---------------------------------------------------------------- objets


def test_structured_data_is_loaded(loaded):
    assert Publication.objects.count() == 10
    assert Experience.objects.count() == 9
    assert Experience.objects.filter(category="industry").count() == 5
    assert Experience.objects.filter(category="research").count() == 4
    assert ExperienceAchievement.objects.count() == 10
    assert Education.objects.count() == 2
    assert MediaAppearance.objects.count() == 4
    assert [lang.code for lang in Language.objects.all()] == ["pl", "fr", "en", "de", "it"]
    assert loaded.created["Publication"] == 10
    assert loaded.created["Expérience"] == 9


def test_site_profile_carries_the_identity(loaded, site):
    profile = SiteProfile.objects.get(site=site)

    assert (profile.first_name, profile.last_name) == ("Bożena", "Polok")
    assert profile.short_name == "B. Polok"
    assert profile.legal_name == "Bożena Karolina Polok"
    assert profile.email == "bozena@bkpolok.com"
    assert profile.linkedin_url == "https://www.linkedin.com/in/dr-bozena-p-4666053"
    assert profile.footer_heading == "Let's talk medical affairs."
    assert profile.publications_page.slug == "publications"


def test_languages_keep_their_level(loaded):
    levels = {lang.code: lang.level for lang in Language.objects.all()}

    assert levels == {
        "pl": "mother_tongue",
        "fr": "full_professional",
        "en": "full_professional",
        "de": "full_professional",
        "it": "intermediate",
    }


def test_experiences_reproduce_the_source_lines(loaded):
    data = yaml.safe_load(CONTENT.read_text(encoding="utf-8"))
    items = [i for g in data["pages"]["home"]["experience"]["groups"] for i in g["items"]]

    assert len(items) == Experience.objects.count()
    for item in items:
        organisation, scope, focus = split_org_line(item["org"])
        experience = Experience.objects.get(title=item["role"], organisation=organisation)
        assert format_org_line(experience) == item["org"]
        assert experience.summary == item.get("summary", "")
        assert [a.text for a in experience.achievements.all()] == item.get("achievements", [])


def test_publication_without_pmid_stays_without(loaded):
    paper = Publication.objects.get(title__startswith="Generation of nitric oxide")

    assert paper.pmid == ""
    assert paper.sort_order == 10


def test_undated_press_item_has_no_date(loaded):
    item = MediaAppearance.objects.get(title="Maladie génétique: découverte sédunoise")

    assert item.date is None
    assert MediaAppearance.objects.get(title="New gene discovery in IRO").date == date(2008, 5, 19)


# ---------------------------------------------------------------- pages


def test_pages_are_filled_and_stay_drafts(loaded, home):
    for slug in PAGE_SLUGS[:-1]:
        assert len(page_at(home, slug).body) > 0, slug
    assert len(page_at(home).body) == 2  # hero + citation
    assert len(page_at(home, "contact").body) == 0  # le « contact » du YAML est le pied de page
    assert not any(p.live for p in Page.objects.descendant_of(home))
    assert page_at(home, "expertise", "coaching").summary.startswith("One-to-one coaching")


def test_home_hero_and_quote(loaded, home):
    hero, quote = page_at(home).body

    assert hero.value["role"].startswith("15 years in medical affairs")
    assert [b["label"] for b in hero.value["buttons"]] == [
        "Get in touch",
        "LinkedIn ↗",
        "See publications",
    ]
    assert hero.value["buttons"][0]["page"].slug == "contact"
    assert hero.value["buttons"][1]["url"].startswith("https://www.linkedin.com/")
    assert quote.value["author"] == "Hippocrates"
    assert not quote.value["text"].startswith("“")


def test_published_pages_render_the_content(loaded, home, client):
    publish_all(home)

    pages = {slug: client.get(f"/{slug}/") for slug in PAGE_SLUGS}
    assert {s: r.status_code for s, r in pages.items()} == dict.fromkeys(PAGE_SLUGS, 200)
    html = {slug: response.content.decode() for slug, response in pages.items()}
    html["home"] = client.get("/").content.decode()

    for page_html in html.values():
        assert page_html.count("<h1") == 1
    assert "Bożena <em>Polok</em>" in html["home"] or "Bożena" in html["home"]
    assert "It is far more important to know what person the disease has" in html["home"]
    assert "From a zebrafish lab in Sion to medical affairs across five regions" in html["about"]
    assert "Polski" in html["about"]
    assert "Where I add the most value" in html["expertise"]
    assert "Medical Affairs Consulting" in html["expertise"]
    assert "DEC 2022 — PRESENT" in html["experience"]
    assert "Industry — 2011 to present" in html["experience"]
    assert "Research — 2000 to 2011" in html["experience"]
    assert "CNNM4" in html["publications"]
    assert "Television" in html["publications"]
    assert "rts.ch/archives" in html["publications"]
    assert "Mentoring" in html["personal"]
    assert "Let&#x27;s talk medical affairs." in html["contact"] or "Let's talk" in html["contact"]


# ---------------------------------------------------------------- idempotence


def snapshot():
    return {
        "pages": Page.objects.count(),
        "revisions": Revision.objects.count(),
        "publications": Publication.objects.count(),
        "experiences": Experience.objects.count(),
        "achievements": ExperienceAchievement.objects.count(),
        "education": Education.objects.count(),
        "media": MediaAppearance.objects.count(),
        "languages": Language.objects.count(),
        "profiles": SiteProfile.objects.count(),
    }


def test_second_run_creates_and_changes_nothing(home):
    load_initial_content(CONTENT)
    before = snapshot()

    report = load_initial_content(CONTENT)

    assert snapshot() == before
    assert report.pages_created == []
    assert report.pages_filled == []
    assert len(report.pages_unchanged) == 9
    assert sum(report.created.values()) == 0
    assert sum(report.updated.values()) == 0
    # seuls les écarts « structurels » connus restent signalés, pas de faux positifs
    assert [n for n in report.notes if n.startswith(("Page", "Profil"))] == []


def test_run_completes_the_empty_drafts_of_create_site_pages(home):
    call_command("create_site_pages")
    assert len(page_at(home, "about").body) == 0

    report = load_initial_content(CONTENT)

    assert report.pages_created == []
    assert len(page_at(home, "about").body) > 0


def test_filled_values_are_kept_and_reported(loaded, home):
    publication = Publication.objects.get(pmid="19200527")
    publication.title = "Edited in the admin"
    publication.save()
    about = page_at(home, "about")
    edited = about.body.raw_data[0]["value"]["content"]
    edited[1]["value"] = "<p>Edited paragraph.</p>"
    about.body = about.body.raw_data
    about.save()

    report = load_initial_content(CONTENT)

    assert Publication.objects.get(pmid="19200527").title == "Edited in the admin"
    assert "Edited paragraph." in str(page_at(home, "about").body.raw_data)
    assert any("Publication n° 01" in note and "title" in note for note in report.notes)
    assert any("/about/" in note for note in report.notes)


def test_update_overwrites_filled_values(loaded, home):
    publication = Publication.objects.get(pmid="19200527")
    publication.title = "Edited in the admin"
    publication.save()

    load_initial_content(CONTENT, update=True)

    assert Publication.objects.get(pmid="19200527").title.startswith("Mutations in CNNM4")
    assert Publication.objects.count() == 10


# ---------------------------------------------------------------- TODO


def test_real_file_contains_no_todo(loaded):
    assert loaded.todos == []
    assert loaded.todo_comments == []


def test_todo_values_are_imported_as_is_and_located(home, client, tmp_path):
    path = content_with(
        tmp_path,
        'role: "15 years in medical affairs, built on a research career at the bench."',
        'role: "TODO confirm: 15 years?"',
    )
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        'job_title: "Associate Global Medical Director"', 'job_title: "TODO exact title"', 1
    )
    text = text.replace(
        'title: "Coaching"\n            text: "One-to-one',
        'title: "Coaching"\n            text: "TODO — One-to-one',
        1,
    )
    text = text.replace(
        'journal: "Zebrafish", year: 2013', 'journal: "TODO journal", year: 2013', 1
    )
    path.write_text(text, encoding="utf-8")

    report = load_initial_content(path)

    by_path = {todo.path: todo for todo in report.todos}
    assert set(by_path) == {
        "pages.home.hero.role",
        "site.json_ld.job_title",
        "pages.home.expertise.offer.items[2].text",
        "pages.home.publications.papers[2].journal",
    }
    assert by_path["pages.home.hero.role"].value == "TODO confirm: 15 years?"
    assert "Page « Home »" in by_path["pages.home.hero.role"].location
    assert "Profil du site" in by_path["site.json_ld.job_title"].location
    assert "/expertise/coaching/" in by_path["pages.home.expertise.offer.items[2].text"].location
    assert "Publication n° 03" in by_path["pages.home.publications.papers[2].journal"].location
    # importées telles quelles
    assert page_at(home).body[0].value["role"] == "TODO confirm: 15 years?"
    assert SiteProfile.objects.get().job_title == "TODO exact title"
    assert page_at(home, "expertise", "coaching").summary.startswith("TODO — One-to-one")
    assert Publication.objects.get(pmid="23536989").journal == "TODO journal"
    # et visibles sur la page une fois publiée
    publish_all(home)
    assert "TODO confirm: 15 years?" in client.get("/").content.decode()


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ("year: 2009, pmid", "year: TODO, pmid"),
        ('date: "DEC 2022 — PRESENT"', 'date: "TODO"'),
        ('date: "19.05.2008"', 'date: "TODO"'),
    ],
)
def test_todo_in_a_number_or_a_date_aborts_without_writing(home, tmp_path, old, new):
    path = content_with(tmp_path, old, new)
    before = snapshot()

    with pytest.raises(ContentError, match="TODO|illisible"):
        load_initial_content(path)

    assert snapshot() == before


def test_command_reports_todos_and_aborts_cleanly(home, tmp_path):
    path = content_with(
        tmp_path,
        "thesis: >-\n        I trained",
        "thesis: >-\n        TODO rewrite. I trained",
    )
    out = StringIO()
    call_command("charger_contenu_initial", file=path, stdout=out)
    assert "TODO restants : 1" in out.getvalue()
    assert "pages.home.hero.thesis" in out.getvalue()

    bad = content_with(tmp_path, "year: 2009, pmid", "year: TODO, pmid")
    with pytest.raises(CommandError, match="rien n'a été écrit"):
        call_command("charger_contenu_initial", file=bad, stdout=StringIO())


def test_todo_in_a_yaml_comment_is_reported_not_imported(home, tmp_path):
    path = content_with(tmp_path, "site:\n", "site:  # TODO check\n")

    report = load_initial_content(path)

    assert report.todos == []
    assert report.todo_comments == [(6, "site:  # TODO check")]


def test_command_prints_the_summary(home):
    out = StringIO()

    call_command("charger_contenu_initial", stdout=out)
    text = out.getvalue()

    assert "créées : 9" in text
    assert "Publication : 10 créé(s)" in text
    assert "TODO restants : 0" in text
    assert "aucun fichier image fourni" in text


def test_command_rejects_a_missing_file(home, tmp_path):
    with pytest.raises(CommandError, match="introuvable"):
        call_command("charger_contenu_initial", file=tmp_path / "nope.yaml")


# ---------------------------------------------------------------- analyseurs


@pytest.mark.parametrize(
    ("text", "start", "end", "precision"),
    [
        ("DEC 2022 — PRESENT", date(2022, 12, 1), None, "month"),
        ("JUN 2019 — NOV 2022", date(2019, 6, 1), date(2022, 11, 30), "month"),
        ("JAN — MAR 2010", date(2010, 1, 1), date(2010, 3, 31), "month"),
        ("2000 — 2006", date(2000, 1, 1), date(2006, 12, 31), "year"),
    ],
)
def test_parse_period(text, start, end, precision):
    assert parse_period(text, "x") == (start, end, precision)


@pytest.mark.parametrize("text", ["TODO", "2000", "FOO 2000 — 2001", "JAN — PRESENT", "2000 — "])
def test_parse_period_refuses_what_it_cannot_read(text):
    with pytest.raises(ContentError):
        parse_period(text, "x")


def test_split_org_line_variants():
    assert split_org_line("Sanofi SA — Vernier, Switzerland") == (
        "Sanofi SA",
        "Vernier, Switzerland",
        "",
    )
    assert split_org_line("UCB Pharma — Bulle, Switzerland · Gastroenterology & Rheumatology") == (
        "UCB Pharma",
        "Bulle, Switzerland",
        "Gastroenterology & Rheumatology",
    )
    assert split_org_line("BIDMC, Harvard Medical School, Boston · Cardiology") == (
        "BIDMC, Harvard Medical School, Boston",
        "",
        "Cardiology",
    )


def test_parse_media_date():
    assert parse_media_date("14.01.2009", "x") == date(2009, 1, 14)
    assert parse_media_date("—", "x") is None
    with pytest.raises(ContentError):
        parse_media_date("TODO", "x")


def test_parse_language_levels():
    levels = parse_language_levels(
        "Polish (mother tongue) · French & English (full professional)", "x"
    )

    assert levels == {
        "Polish": "mother_tongue",
        "French": "full_professional",
        "English": "full_professional",
    }
    with pytest.raises(ContentError):
        parse_language_levels("Polish (TODO)", "x")


def test_page_slugs_match_the_tree(home):
    call_command("create_site_pages")

    assert [p.slug for p in page_at(home).get_children()] == PAGE_SLUGS


def test_body_ids_do_not_break_idempotence(home):
    load_initial_content(CONTENT)
    first = page_at(home, "personal").body.raw_data
    load_initial_content(CONTENT)

    assert re.sub(r'"id": "[^"]+"', "", str(first)) == re.sub(
        r'"id": "[^"]+"', "", str(page_at(home, "personal").body.raw_data)
    )
