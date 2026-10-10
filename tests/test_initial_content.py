import re
from datetime import date
from io import StringIO
from pathlib import Path

import pytest
import yaml
from django.conf import settings
from django.core.management import CommandError, call_command
from wagtail.images import get_image_model
from wagtail.models import Page, Revision

from apps.pages.initial_content import (
    ContentError,
    load_initial_content,
    parse_language_levels,
    parse_media_date,
    parse_period,
    parse_position,
    split_org_line,
)
from apps.pages.models import HomePage
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
from apps.profile.services import format_org_line

pytestmark = pytest.mark.django_db

CONTENT = Path(settings.BASE_DIR) / "_artifact" / "design" / "content.yaml"
ASSETS = Path(settings.BASE_DIR) / "_artifact" / "assets"
PAGE_SLUGS = [
    "about",
    "services",
    "experience",
    "publications",
    "personal",
    "contact",
    "legal-notice",
    "privacy",
]
LEGAL_TODOS = {
    "pages.legal_notice.sections[0].paragraphs_html[0]",
    "pages.legal_notice.sections[0].paragraphs_html[1]",
    "pages.legal_notice.sections[0].paragraphs_html[2]",
    "pages.privacy.sections[2].paragraphs_html[0]",
    "pages.privacy.sections[4].paragraphs_html[0]",
}


@pytest.fixture(autouse=True)
def media_root(settings, tmp_path):
    """Les images importées vont dans un dossier temporaire, pas dans media/."""
    settings.MEDIA_ROOT = tmp_path / "media"


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
    """Copie de content.yaml dont un texte est remplacé (le test échoue si `old` a disparu).

    La copie est dans tmp_path/design/ : les images restent cherchées dans _artifact/assets
    grâce au lien tmp_path/assets.
    """
    text = CONTENT.read_text(encoding="utf-8")
    assert old in text, old
    (tmp_path / "design").mkdir(exist_ok=True)
    if not (tmp_path / "assets").exists():
        (tmp_path / "assets").symlink_to(ASSETS)
    path = tmp_path / "design" / "content.yaml"
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    return path


def publish_all(home):
    for page in Page.objects.descendant_of(home, inclusive=True):
        page.specific.save_revision().publish()


# ---------------------------------------------------------------- objets


def test_structured_data_is_loaded(loaded):
    assert Publication.objects.count() == 11
    assert Publication.objects.filter(category="medical_affairs").count() == 1
    assert Experience.objects.count() == 9
    assert Experience.objects.filter(category="industry").count() == 5
    assert Experience.objects.filter(category="research").count() == 4
    assert ExperienceAchievement.objects.count() == 13
    assert Education.objects.count() == 2
    assert Education.objects.filter(listed=True).count() == 1
    assert MediaAppearance.objects.count() == 4
    assert [lang.code for lang in Language.objects.all()] == ["pl", "fr", "en", "de", "it"]
    assert get_image_model().objects.count() == 13
    assert loaded.created["Publication"] == 11
    assert loaded.created["Expérience"] == 9
    assert loaded.not_imported == []


def test_images_carry_alt_text_and_the_designed_crop(loaded):
    images = get_image_model().objects
    portrait = images.get(title="portrait")
    figure = images.get(title="kotkamp-2014-fig1")

    assert portrait.description.startswith("Portrait of Bożena Polok laughing")
    assert portrait.focal_point_x is None  # pas de recadrage dans le design
    assert figure.focal_point_x == round(figure.width * 0.5)
    assert figure.focal_point_y == round(figure.height * 0.2)


def test_links_to_publications_and_shared_images(loaded):
    munk = Publication.objects.get(pmid="35886930")
    kotkamp = Publication.objects.get(pmid="24643012")
    achievement = ExperienceAchievement.objects.get(link_text="Munk et al. (2022)")
    iro = Experience.objects.get(title="Postdoc & Zebrafish Group Principal Investigator")

    assert achievement.publication == munk
    assert munk.note.startswith("Grew out of an expert advisory board")
    assert iro.pair_with_next is True
    assert [(i.caption, i.publication) for i in iro.images.all()] == [
        ("FIG. 1", kotkamp),
        ("FIG. 5", kotkamp),
    ]
    assert all(i.link_label == "" for i in iro.images.all())  # libellé calculé identique
    olympus = ExperienceImage.objects.get(caption="IXplore SpinSR")
    assert olympus.link_label == "Evident/Olympus" and olympus.link_url.startswith("https://")
    assert Experience.objects.get(title="Associate Global Medical Director").parallel_role == (
        "Patient Ambassador EMEA"
    )


def test_site_profile_carries_the_identity(loaded, site):
    profile = SiteProfile.objects.get(site=site)

    assert (profile.first_name, profile.last_name) == ("Bożena", "Polok")
    assert profile.short_name == "B. Polok"
    assert profile.legal_name == "Bożena Karolina Polok"
    assert profile.email == "bozena@bkpolok.com"
    assert profile.linkedin_url == "https://www.linkedin.com/in/dr-bozena-p-4666053"
    assert profile.name_language == "pl"
    assert profile.footer_heading == "Let's talk."
    assert profile.footer_lede.startswith("For consulting projects")
    assert 'href="mailto:bozena@bkpolok.com?subject=Website%20accessibility"' in (
        profile.accessibility_statement
    )
    assert profile.copyright_notice.startswith("All text and photographs")
    assert profile.publications_page.slug == "publications"
    assert profile.legal_notice_page.slug == "legal-notice"
    assert profile.privacy_page.slug == "privacy"


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
    experience_data = data["pages"]["home"]["experience"]
    groups = experience_data["groups"] + experience_data["more"]["groups"]
    items = [i for g in groups for i in g["items"]]

    assert len(items) == Experience.objects.count()
    for item in items:
        organisation, scope, focus = split_org_line(item["org"])
        experience = Experience.objects.get(title=item["role"], organisation=organisation)
        assert format_org_line(experience) == item["org"]
        assert experience.summary == item.get("summary", "")
        texts = [a if isinstance(a, str) else a["text"] for a in item.get("achievements", [])]
        assert [a.text for a in experience.achievements.all()] == texts


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
    for slug in PAGE_SLUGS:
        if slug != "contact":
            assert len(page_at(home, slug).body) > 0, slug
    assert len(page_at(home).body) == 2  # hero + citation
    assert len(page_at(home, "contact").body) == 0  # le « contact » du YAML est le pied de page
    assert not any(p.live for p in Page.objects.descendant_of(home))
    assert page_at(home, "services", "coaching").summary.startswith("One-to-one coaching")
    assert page_at(home, "services", "coaching").title == "Coaching"
    assert page_at(home, "legal-notice").title == "Legal notice (Impressum)"


def test_home_hero_and_quote(loaded, home):
    hero, quote = page_at(home).body

    assert hero.value["role"].startswith("Senior medical affairs expertise")
    assert hero.value["now"].startswith("Today: Associate Global Medical Director")
    assert [b["label"] for b in hero.value["buttons"]] == [
        "Discuss a project",
        "How I can help",
        "LinkedIn",
    ]
    assert hero.value["buttons"][0]["page"].slug == "contact"
    assert hero.value["buttons"][1]["page"].slug == "services"
    assert hero.value["buttons"][2]["url"].startswith("https://www.linkedin.com/")
    assert hero.value["image"].title == "portrait"
    assert quote.value["author"].startswith("Antonie van Leeuwenhoek")
    assert quote.value["note"].startswith("Curiosity")
    assert not quote.value["text"].startswith("“")


def test_published_pages_render_the_content(loaded, home, client):
    publish_all(home)

    pages = {slug: client.get(f"/{slug}/") for slug in PAGE_SLUGS}
    assert {s: r.status_code for s, r in pages.items()} == dict.fromkeys(PAGE_SLUGS, 200)
    html = {slug: response.content.decode() for slug, response in pages.items()}
    html["home"] = client.get("/").content.decode()

    for page_html in html.values():
        assert page_html.count("<h1") == 1
        assert "Legal notice (Impressum)</a>" in page_html  # pied de page
    assert '<span lang="pl">Bożena&nbsp;<em>Polok</em></span>' in html["home"]
    assert "Whenever I found out anything remarkable" in html["home"]
    assert "From a zebrafish lab in Sion to medical affairs across Europe" in html["about"]
    assert "The zebrafish eye, two ways" in html["about"]
    assert "How I can help" in html["services"]
    assert html["services"].count('class="offer-card"') == 3
    assert "Medical affairs consulting</a></h3>" in html["services"]
    assert "Planning a launch, an advisory board or a patient initiative?" in html["services"]
    assert "Industry — 2011 to present" in html["experience"]
    assert "<summary>Research career &amp; education, 2000–2011</summary>" in html["experience"]
    assert 'class="tl-pair"' in html["experience"]
    assert "First degree" in html["experience"]
    assert "pub-featured" in html["publications"] and "CNNM4" in html["publications"]
    assert "<summary>Show 7 more research papers</summary>" in html["publications"]
    assert "rts.ch/archives" in html["publications"]
    assert "Through my lens" in html["personal"]
    assert html["personal"].count('class="gallery-grid"') == 1
    assert "Let&#x27;s talk." in html["contact"] or "Let's talk." in html["contact"]
    assert "page--legal" in html["legal-notice"] and "[TODO: phone number]" in html["legal-notice"]
    assert "<h2>3. Visiting the website (hosting)</h2>" in html["privacy"]


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
        "images": get_image_model().objects.count(),
        "experience_images": ExperienceImage.objects.count(),
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
    assert len(report.pages_unchanged) == 11
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
    assert any("Mutations in CNNM4" in note and "title" in note for note in report.notes)
    assert any("/about/" in note for note in report.notes)


def test_update_overwrites_filled_values(loaded, home):
    publication = Publication.objects.get(pmid="19200527")
    publication.title = "Edited in the admin"
    publication.save()

    load_initial_content(CONTENT, update=True)

    assert Publication.objects.get(pmid="19200527").title.startswith("Mutations in CNNM4")
    assert Publication.objects.count() == 11


def test_records_missing_from_the_file_are_reported_not_deleted(loaded):
    Education.objects.create(degree="Old degree", institution="Somewhere")

    report = load_initial_content(CONTENT)

    assert Education.objects.filter(degree="Old degree").exists()
    assert any("Old degree" in note and "absent du YAML" in note for note in report.notes)


def test_a_missing_image_file_is_reported_not_fatal(home, tmp_path):
    path = content_with(tmp_path, "file: portrait.jpg", "file: nope.jpg")

    report = load_initial_content(path)

    assert any("nope.jpg" in item for item in report.not_imported)
    assert page_at(home).body[0].value["image"] is None


# ---------------------------------------------------------------- TODO


def test_real_file_only_has_the_legal_placeholders_to_fill(loaded):
    assert {todo.path for todo in loaded.todos} == LEGAL_TODOS
    for todo in loaded.todos:
        assert "(/legal-notice/)" in todo.location or "(/privacy/)" in todo.location
    assert loaded.todo_comments == []


def test_todo_values_are_imported_as_is_and_located(home, client, tmp_path):
    path = content_with(
        tmp_path,
        'role: "Senior medical affairs expertise for teams that need it',
        'role: "TODO confirm: 15 years?',
    )
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        'job_title: "Associate Global Medical Director"', 'job_title: "TODO exact title"', 1
    )
    text = text.replace(
        'title: "Coaching"\n          text: "One-to-one',
        'title: "Coaching"\n          text: "TODO — One-to-one',
        1,
    )
    text = text.replace(
        'journal: "Zebrafish", year: 2013', 'journal: "TODO journal", year: 2013', 1
    )
    path.write_text(text, encoding="utf-8")

    report = load_initial_content(path)

    by_path = {todo.path: todo for todo in report.todos if todo.path not in LEGAL_TODOS}
    assert set(by_path) == {
        "pages.home.hero.role",
        "site.json_ld.job_title",
        "pages.home.services.offers[2].text",
        "pages.home.publications.research.papers[2].journal",
    }
    assert by_path["pages.home.hero.role"].value.startswith("TODO confirm: 15 years?")
    assert "Page « Home »" in by_path["pages.home.hero.role"].location
    assert "Profil du site" in by_path["site.json_ld.job_title"].location
    assert "/services/coaching/" in by_path["pages.home.services.offers[2].text"].location
    assert "Bigh3" in by_path["pages.home.publications.research.papers[2].journal"].location
    # importées telles quelles
    assert page_at(home).body[0].value["role"].startswith("TODO confirm: 15 years?")
    assert SiteProfile.objects.get().job_title == "TODO exact title"
    assert page_at(home, "services", "coaching").summary.startswith("TODO — One-to-one")
    assert Publication.objects.get(pmid="23536989").journal == "TODO journal"
    # et visibles sur la page une fois publiée
    publish_all(home)
    assert "TODO confirm: 15 years?" in client.get("/").content.decode()


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ("year: 2009, pmid", "year: TODO, pmid"),
        ('date: "Dec 2022 — present"', 'date: "TODO"'),
        ('date: "19 May 2008"', 'date: "TODO"'),
        ('position: "50% 20%"', 'position: "TODO"'),
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
        'thesis: "Geneticist by training',
        'thesis: "TODO rewrite. Geneticist by training',
    )
    out = StringIO()
    call_command("charger_contenu_initial", file=path, stdout=out)
    assert f"TODO restants : {len(LEGAL_TODOS) + 1}" in out.getvalue()
    assert "pages.home.hero.thesis" in out.getvalue()

    bad = content_with(tmp_path, "year: 2009, pmid", "year: TODO, pmid")
    with pytest.raises(CommandError, match="rien n'a été écrit"):
        call_command("charger_contenu_initial", file=bad, stdout=StringIO())


def test_todo_in_a_yaml_comment_is_reported_not_imported(home, tmp_path):
    path = content_with(tmp_path, "site:\n", "site:  # TODO check\n")

    report = load_initial_content(path)

    assert {todo.path for todo in report.todos} == LEGAL_TODOS
    line = CONTENT.read_text(encoding="utf-8").splitlines().index("site:") + 1
    assert report.todo_comments == [(line, "site:  # TODO check")]


def test_command_prints_the_summary(home):
    out = StringIO()

    call_command("charger_contenu_initial", stdout=out)
    text = out.getvalue()

    assert "créées : 11" in text
    assert "Publication : 11 créé(s)" in text
    assert "Image : 13 créé(s)" in text
    assert f"TODO restants : {len(LEGAL_TODOS)}" in text
    assert "Non importé" not in text


def test_command_rejects_a_missing_file(home, tmp_path):
    with pytest.raises(CommandError, match="introuvable"):
        call_command("charger_contenu_initial", file=tmp_path / "nope.yaml")


# ---------------------------------------------------------------- analyseurs


@pytest.mark.parametrize(
    ("text", "start", "end", "precision"),
    [
        ("Dec 2022 — present", date(2022, 12, 1), None, "month"),
        ("Jun 2019 — Nov 2022", date(2019, 6, 1), date(2022, 11, 30), "month"),
        ("Jan — Mar 2010", date(2010, 1, 1), date(2010, 3, 31), "month"),
        ("2000 — 2006", date(2000, 1, 1), date(2006, 12, 31), "year"),
    ],
)
def test_parse_period(text, start, end, precision):
    assert parse_period(text, "x") == (start, end, precision)


@pytest.mark.parametrize(
    "text", ["TODO", "2000", "Foo 2000 — 2001", "Jan — present", "2000 — ", "DEC 2022 — PRESENT"]
)
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
    assert parse_media_date("14 Jan 2009", "x") == date(2009, 1, 14)
    assert parse_media_date("—", "x") is None
    for text in ("TODO", "14.01.2009", "32 Jan 2009", "14 Foo 2009"):
        with pytest.raises(ContentError):
            parse_media_date(text, "x")


def test_parse_position():
    assert parse_position("50% 20%", "x") == (0.5, 0.2)
    for text in ("TODO", "50%", "120% 0%"):
        with pytest.raises(ContentError):
            parse_position(text, "x")


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
