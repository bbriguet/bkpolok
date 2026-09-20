import json
from datetime import date

import pytest

from apps.pages.models import StandardPage
from apps.profile.models import (
    Education,
    Experience,
    ExperienceAchievement,
    Language,
    MediaAppearance,
    Publication,
)
from apps.services.models import ServiceIndexPage, ServicePage

pytestmark = pytest.mark.django_db


def make_page(home, blocks, slug="test"):
    page = home.add_child(instance=StandardPage(title="Test", slug=slug, body=json.dumps(blocks)))
    return page


def get_html(client, page):
    response = client.get(page.url)
    assert response.status_code == 200
    return response.content.decode()


def test_base_layout_uses_local_assets_and_english(client, home, profile):
    html = get_html(client, home)

    assert '<html lang="en">' in html
    assert "Skip to content" in html
    assert 'aria-label="Main navigation"' in html
    assert "css/tokens.css" in html and "css/fonts.css" in html and "css/site.css" in html
    assert "fonts.googleapis.com" not in html and "fonts.gstatic.com" not in html
    assert 'rel="preload"' in html
    assert "<title>Home – Jane Doe</title>" in html


def test_nav_brand_and_footer_come_from_the_site_profile(client, home, profile):
    make_language = Language.objects.create
    make_language(code="pl", native_name="Polski", english_name="Polish", level="mother_tongue")
    make_language(
        code="fr", native_name="Français", english_name="French", level="full_professional"
    )

    html = get_html(client, home)

    assert ">J. Doe</a>" in html
    assert "Let&#x27;s talk." in html or "Let's talk." in html
    assert 'href="mailto:jane@example.ch"' in html
    assert ">linkedin.com/in/jane-doe</a>" in html
    assert ">PL</span>" in html and ">FR</span>" in html
    assert "Jane Q. Doe." in html


def test_json_ld_is_only_on_the_home_page(client, home, profile):
    other = make_page(home, [], slug="other")

    home_html = get_html(client, home)
    other_html = get_html(client, other)

    assert '<script type="application/ld+json">' in home_html
    assert '"name": "Jane Q. Doe"' in home_html
    assert "application/ld+json" not in other_html


def test_hero_block_takes_the_name_from_the_profile(client, home, profile):
    hero = {
        "type": "hero",
        "value": {
            "eyebrow": "Leadership",
            "role": "A role",
            "badge_text": "Open to offers",
            "thesis": "An introduction.",
            "buttons": [
                {"label": "Get in touch", "page": home.pk, "url": "", "variant": "primary"},
                {
                    "label": "LinkedIn",
                    "page": None,
                    "url": "https://example.org/x",
                    "variant": "ghost",
                },
            ],
            "image": None,
        },
    }
    html = get_html(client, make_page(home, [hero]))

    assert "<h1>Jane&nbsp;<em>Doe</em></h1>" in html
    assert 'class="hero-role">A role' in html
    assert "status-badge" in html and "Open to offers" in html
    assert 'class="btn btn-primary"' in html
    assert 'class="btn btn-ghost" href="https://example.org/x" target="_blank"' in html


def test_hero_falls_back_to_the_page_title_without_a_profile(client, home):
    hero = {
        "type": "hero",
        "value": {
            "role": "R",
            "thesis": "T",
            "buttons": [],
            "image": None,
            "eyebrow": "",
            "badge_text": "",
        },
    }

    html = get_html(client, make_page(home, [hero]))

    assert "<h1>Test</h1>" in html


def test_heading_block_with_eyebrow_lede_and_pills(client, home):
    heading = {
        "type": "heading",
        "value": {
            "eyebrow": "Expertise",
            "text": "Where I add value",
            "level": "h2",
            "lede": "A lede.",
            "pills": ["Alpha", "Beta"],
            "image": None,
        },
    }

    html = get_html(client, make_page(home, [heading]))

    assert '<p class="eyebrow">Expertise</p>' in html
    assert "<h2>Where I add value</h2>" in html
    assert '<p class="lede">A lede.</p>' in html
    assert html.count('class="pill"') == 2


def test_section_block_wraps_content_with_anchor_and_background(client, home):
    section = {
        "type": "section",
        "value": {
            "anchor": "about",
            "background": "tint",
            "content": [{"type": "heading", "value": {"text": "Inside", "level": "h2"}}],
        },
    }

    html = get_html(client, make_page(home, [section]))

    assert '<section class="section tint" id="about">' in html
    assert "<h2>Inside</h2>" in html


def test_section_anchor_must_be_a_slug():
    from wagtail.blocks import StructBlockValidationError

    from apps.pages.blocks import SectionBlock

    block = SectionBlock()
    value = block.to_python({"anchor": "Bad Anchor!", "background": "default", "content": []})

    with pytest.raises(StructBlockValidationError):
        block.clean(value)


def test_quote_block_renders_as_pull_quote(client, home):
    quote = {"type": "quote", "value": {"text": "Know the person.", "author": "Someone"}}

    html = get_html(client, make_page(home, [quote]))

    assert '<blockquote class="pull-quote">' in html
    assert "“Know the person.”" in html
    assert "<cite>— Someone</cite>" in html


def test_card_grid_variants_and_icons(client, home):
    cards = [{"icon": "fish", "title": "Zebrafish", "text": "Text.", "wide": False}]
    blocks = [
        {"type": "cards", "value": {"variant": "service", "cards": cards}},
        {
            "type": "cards",
            "value": {
                "variant": "off_duty",
                "cards": [{**cards[0], "wide": True}, {**cards[0], "icon": ""}],
            },
        },
    ]

    html = get_html(client, make_page(home, blocks))

    assert 'class="service-grid"' in html and 'class="service"' in html
    assert 'class="off-duty-grid"' in html and 'class="off-card wide"' in html
    assert html.count('<svg class="icon"') == 2  # the card without an icon renders none


def test_aside_notes_are_a_row_when_there_are_two(client, home):
    one = {"type": "aside_notes", "value": {"notes": [{"icon": "clock", "text": "Solo."}]}}
    two = {
        "type": "aside_notes",
        "value": {"notes": [{"icon": "clock", "text": "A."}, {"icon": "search", "text": "B."}]},
    }

    html = get_html(client, make_page(home, [one, two]))

    assert html.count('class="aside-notes"') == 1
    assert html.count('class="aside-notes aside-row"') == 1


def test_service_offer_block_lists_the_child_service_pages(client, home):
    index = home.add_child(instance=ServiceIndexPage(title="Expertise", slug="expertise"))
    index.add_child(instance=ServicePage(title="Coaching", slug="coaching", summary="One-to-one."))
    index.add_child(
        instance=ServicePage(title="Draft", slug="draft", summary="Hidden.", live=False)
    )
    block = {"type": "offers", "value": {"lead": "Also available:", "index_page": index.pk}}

    html = get_html(client, make_page(home, [block]))

    assert "Also available:" in html
    assert '<dt><a href="/expertise/coaching/">Coaching</a></dt>' in html
    assert "<dd>One-to-one.</dd>" in html
    assert "Hidden." not in html


def test_long_service_summary_is_allowed(home):
    index = home.add_child(instance=ServiceIndexPage(title="Expertise", slug="expertise"))
    page = index.add_child(instance=ServicePage(title="Long", slug="long", summary="x" * 550))

    page.full_clean()  # 550 characters would fail with the former 250 limit


def test_timeline_block_renders_entries_and_group_label(client, home, profile):
    experience = Experience.objects.create(
        category="industry",
        title="Director",
        organisation="Acme",
        scope="Zurich",
        focus="Widgets",
        organisation_description="A company.",
        summary="Led things.",
        start_date=date(2022, 12, 1),
    )
    ExperienceAchievement.objects.create(experience=experience, text="Grew the team")
    block = {"type": "timeline", "value": {"category": "industry"}}

    html = get_html(client, make_page(home, [block]))

    assert 'class="group-label">Industry — 2022 to present' in html
    assert 'class="tl-date">DEC 2022 — PRESENT' in html
    assert "<h3>Director</h3>" in html
    assert 'class="org">Acme — Zurich · Widgets' in html
    assert "<li>Grew the team</li>" in html


def test_education_block(client, home):
    Education.objects.create(degree="PhD", institution="University of X")
    block = {"type": "education", "value": {"eyebrow": "Education", "heading": "Training"}}

    html = get_html(client, make_page(home, [block]))

    assert "<h3>Training</h3>" in html
    assert 'class="deg">PhD' in html and 'class="inst">University of X' in html


def test_publication_list_block_numbers_papers_and_does_not_localise_years(client, home, profile):
    Publication.objects.create(
        title="First",
        authors="Doe J, et al.",
        journal="Nature",
        year=2009,
        pmid="111",
        sort_order=1,
    )
    Publication.objects.create(
        title="Second", authors="Roe R", journal="Science", year=2014, sort_order=2
    )
    block = {"type": "publications", "value": None}

    html = get_html(client, make_page(home, [block]))

    assert 'class="pub-num">01' in html and 'class="pub-num">02' in html
    assert "<em>Nature</em>, 2009" in html
    assert "2’009" not in html and "2,009" not in html
    assert 'href="https://pubmed.ncbi.nlm.nih.gov/111/"' in html
    assert "PMID 111" in html
    assert 'href="https://pubmed.ncbi.nlm.nih.gov/?term=doe"' in html  # profile PubMed link
    assert html.count("PMID") == 1  # the paper without a PMID shows no link


def test_media_list_block_uses_swiss_dates_and_quotes_titles(client, home):
    MediaAppearance.objects.create(
        kind="tv", outlet="TSR", title="News item", date=date(2008, 5, 19), sort_order=1
    )
    MediaAppearance.objects.create(
        kind="tv", outlet="RTS", title="Linked", url="https://example.org/v", sort_order=2
    )
    MediaAppearance.objects.create(kind="press", outlet="Paper", title="Elsewhere")
    block = {
        "type": "media",
        "value": {
            "kind": "tv",
            "eyebrow": "Media",
            "heading": "Television",
            "note": '<p>See <a href="https://example.org/a">the archive</a>.</p>',
        },
    }

    html = get_html(client, make_page(home, [block]))

    assert "<h3>Television</h3>" in html
    assert 'class="media-date mono">19.05.2008' in html
    assert 'class="media-date mono">—' in html
    assert 'TSR — "News item"' in html
    assert '<a href="https://example.org/v" target="_blank" rel="noopener">"Linked"</a>' in html
    assert "Elsewhere" not in html
    assert 'class="media-note"' in html and "the archive" in html


def test_languages_block_shows_pills_and_caption(client, home):
    Language.objects.create(
        code="pl", native_name="Polski", english_name="Polish", level="mother_tongue", sort_order=1
    )
    Language.objects.create(
        code="fr",
        native_name="Français",
        english_name="French",
        level="full_professional",
        sort_order=2,
    )
    block = {"type": "languages", "value": None}

    html = get_html(client, make_page(home, [block]))

    assert '<span class="lang-pill" lang="pl">Polski</span>' in html
    assert "Polish (mother tongue) · French (full professional)" in html


def test_rich_text_paragraph_is_wrapped_for_styling(client, home):
    html = get_html(client, make_page(home, [{"type": "paragraph", "value": "<p>Body text.</p>"}]))

    assert 'class="rich-text"' in html


def test_stream_blocks_are_wrapped_in_block_divs_used_by_the_stylesheet(client, home):
    """site.css cible « .block-timeline + .block-timeline » : l'enveloppe doit rester."""
    blocks = [{"type": "timeline", "value": {"category": c}} for c in ("industry", "research")]
    make_experience = Experience.objects.create
    for category in ("industry", "research"):
        make_experience(
            category=category, title=category, organisation="X", start_date=date(2000, 1, 1)
        )

    html = get_html(client, make_page(home, blocks))

    assert html.count('<div class="block-timeline">') == 2
