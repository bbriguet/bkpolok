import re
from datetime import date
from pathlib import Path

import pytest
from django.template import TemplateDoesNotExist
from django.template.loader import get_template, render_to_string
from django.utils.safestring import mark_safe

from apps.pages import demo
from apps.pages.icons import ICONS
from apps.pages.templatetags.ui import icon

ROOT = Path(__file__).resolve().parent.parent
COMPONENT_CSS = ROOT / "static" / "css" / "components"
INCLUDES = ROOT / "templates" / "includes"


def render(name: str, **context) -> str:
    return render_to_string(f"includes/{name}.html", context)


def _strip_comments(css: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


# ---------------------------------------------------------------- icônes


@pytest.mark.parametrize("name", [*ICONS, "chevron"])
def test_every_icon_is_an_inline_svg_file(name):
    svg = (INCLUDES / "icons" / f"{name}.svg").read_text(encoding="utf-8")

    assert svg.startswith('<svg class="icon" viewBox="0 0 24 24"')
    assert 'aria-hidden="true"' in svg
    assert "<script" not in svg and "href=" not in svg


def test_every_icon_file_is_offered_or_a_ui_icon():
    files = {path.stem for path in (INCLUDES / "icons").glob("*.svg")}

    assert files - set(ICONS) == {"chevron"}


@pytest.mark.parametrize("name", ["", None, "nope", "../base", "a/b", "CHEVRON"])
def test_icon_tag_ignores_unknown_or_unsafe_names(name):
    assert icon(name) == ""


def test_icon_tag_renders_the_file():
    assert icon("fish").startswith('<svg class="icon"')


# ---------------------------------------------------------------- CSS et JS


def test_every_component_stylesheet_is_loaded_by_base_html():
    base = (ROOT / "templates" / "base.html").read_text(encoding="utf-8")
    linked = set(re.findall(r"css/components/([a-z_]+)\.css", base))

    assert linked == {path.stem for path in COMPONENT_CSS.glob("*.css")}


def test_every_component_stylesheet_has_a_template():
    """Chaque composant a son include (sauf les utilitaires transverses)."""
    transverse = {"icon", "reveal"}
    css = {path.stem for path in COMPONENT_CSS.glob("*.css")} - transverse
    templates = {path.stem for path in INCLUDES.glob("*.html")}

    assert css - templates == set()


@pytest.mark.parametrize("path", sorted(COMPONENT_CSS.glob("*.css")), ids=lambda p: p.name)
def test_motion_only_uses_duration_tokens(path):
    """Aucune durée en dur dans transition / animation : tout passe par --dur-* (tokens.css)."""
    css = _strip_comments(path.read_text(encoding="utf-8"))
    declarations = re.findall(r"(?:transition|animation)(?:-duration|-delay)?\s*:([^;]+);", css)
    for value in declarations:
        without_vars = re.sub(r"var\([^)]*\)", "", value)
        assert not re.search(r"\d\s*m?s\b", without_vars), (path.name, value)


def test_tokens_zero_every_duration_under_reduced_motion():
    css = _strip_comments((ROOT / "static" / "css" / "tokens.css").read_text(encoding="utf-8"))
    reduced = css.split("@media (prefers-reduced-motion: reduce)")[1]

    for token in re.findall(r"(--dur-[a-z]+)\s*:", css.split("@media")[0]):
        assert re.search(rf"{token}:\s*0ms", reduced), token
    assert "--reveal-shift: 0px" in reduced


def test_infinite_animation_has_a_reduced_motion_guard():
    css = (COMPONENT_CSS / "status_badge.css").read_text(encoding="utf-8")

    assert "@keyframes status-pulse" in css
    assert re.search(
        r"@media \(prefers-reduced-motion: reduce\)\s*{\s*\.status-dot\s*{\s*animation: none", css
    )


def test_button_styles_cover_every_state():
    css = (COMPONENT_CSS / "button.css").read_text(encoding="utf-8")

    for selector in (".btn-primary:hover", ".btn-ghost:hover", ".btn-primary:active"):
        assert selector in css
    assert ':is(:disabled, [aria-disabled="true"])' in css


def test_reveal_script_only_runs_when_motion_is_allowed():
    js = (ROOT / "static" / "js" / "reveal.js").read_text(encoding="utf-8")

    assert "prefers-reduced-motion: reduce" in js
    assert "IntersectionObserver" in js


@pytest.mark.django_db
def test_base_html_loads_the_reveal_script(client, home):
    assert "js/reveal.js" in client.get(home.url).content.decode()


# ---------------------------------------------------------------- includes


def test_button_renders_link_external_disabled_link_and_real_button():
    link = render("button", label="Go", href="/x")
    external = render("button", label="Out", href="https://e.org", variant="ghost", external=True)
    disabled_link = render("button", label="Off", href="/x", disabled=True)
    button = render("button", label="Send", type="submit")
    disabled_button = render("button", label="Off", disabled=True, variant="ghost")

    assert '<a class="btn btn-primary" href="/x">Go</a>' in link
    assert 'class="btn btn-ghost" href="https://e.org" target="_blank" rel="noopener"' in external
    assert 'aria-disabled="true"' in disabled_link and "href=" not in disabled_link
    assert '<button class="btn btn-primary" type="submit">Send</button>' in button
    assert "<button" in disabled_button and " disabled>" in disabled_button


def test_nav_marks_current_and_disabled_items():
    html = render(
        "nav",
        brand="B",
        items=[
            {"label": "One", "href": "/1", "current": True},
            {"label": "Two", "href": "/2"},
            {"label": "Three", "disabled": True},
        ],
    )

    assert '<a href="/1" aria-current="page">One</a>' in html
    assert '<a href="/2">Two</a>' in html
    assert '<a role="link" aria-disabled="true">Three</a>' in html
    assert 'aria-label="Main navigation"' in html


def test_nav_without_items_has_no_list():
    assert "nav-links" not in render("nav", brand="B", items=[])


def test_section_head_variants():
    plain = render("section_head", eyebrow="E", title="T", lede="L", pills=["a", "b"])
    sub = render("section_head", title="T", level="h3", sub=True)
    photo = render(
        "section_head", title="T", image={"url": "/p.png", "width": 5, "height": 5}, image_alt="A"
    )

    assert "<h2>T</h2>" in plain and plain.count('class="pill"') == 2
    assert 'class="section-head section-head--sub"' in sub and "<h3>T</h3>" in sub
    assert 'class="section-head personal-head"' in photo
    assert 'class="personal-photo" src="/p.png"' in photo and 'alt="A"' in photo


def test_section_uses_the_background_parameter():
    tint = render("section", background="tint", anchor="about", content=mark_safe("<p>x</p>"))
    plain = render("section", background="default", content=mark_safe("<p>x</p>"))

    assert '<section class="section tint" id="about">' in tint
    assert '<section class="section">' in plain and "<p>x</p>" in plain


def test_pill_variants():
    assert render("pill", label="Alpha").strip() == '<span class="pill">Alpha</span>'
    assert (
        render("pill", label="Polski", variant="lang", lang="pl").strip()
        == '<span class="lang-pill" lang="pl">Polski</span>'
    )
    assert 'class="lang-row"' in render("pill_row", labels=["PL"], variant="lang")


def test_hero_renders_name_buttons_and_portrait():
    html = render(
        "hero",
        first_name="Jane",
        last_name="Doe",
        role="R",
        thesis="T",
        buttons=[{"label": "Go", "href": "/x", "variant": "primary", "external": False}],
        portrait={"url": "/p.png", "width": 408, "height": 408},
        portrait_alt="Portrait",
    )

    assert "<h1>Jane&nbsp;<em>Doe</em></h1>" in html
    assert '<a class="btn btn-primary" href="/x">Go</a>' in html
    assert '<div class="iris">' in html and 'alt="Portrait"' in html


def test_hero_without_portrait_has_no_iris():
    assert "iris" not in render("hero", title="Home", role="R", thesis="T")


def test_accordion_uses_native_details_and_can_group_and_open_the_first():
    html = render(
        "accordion",
        items=[
            {"question": "Q1?", "answer": "<p>A1</p>"},
            {"question": "Q2?", "answer": "<p>A2</p>"},
        ],
        group="faq",
        open_first=True,
    )

    assert html.count("<details") == 2 and html.count("<summary") == 2
    assert html.count('name="faq"') == 2
    assert html.count(" open>") == 1
    assert "<p>A1</p>" in html and '<svg class="icon"' in html


def test_card_grid_wide_only_in_off_duty_layout_and_staggers_reveal():
    cards = [{"icon": "fish", "title": "A", "text": "t", "wide": True}]

    off_duty = render("card_grid", variant="off_duty", cards=cards)
    service = render("card_grid", variant="service", cards=cards)

    assert 'class="off-card wide"' in off_duty and "off-duty-grid" in off_duty
    assert 'class="service"' in service and "wide" not in service
    assert 'style="--reveal-i: 0"' in service


def test_research_thumb_caption_link_opens_a_new_tab_only_when_external():
    thumb = {"url": "/t.png", "width": 216, "height": 216}
    internal = render(
        "research_thumb",
        image=thumb,
        alt="a",
        caption="FIG. 1",
        link_url="/p/#x",
        link_label="Doe, 2014",
    )
    external = render(
        "research_thumb",
        image=thumb,
        alt="a",
        link_url="https://e.org",
        link_label="Doe",
        external=True,
    )

    assert '<a href="/p/#x">Doe, 2014 →</a>' in internal
    assert 'target="_blank" rel="noopener"' in external


def test_media_list_uses_swiss_dates_and_dash_for_unknown_dates():
    html = render(
        "media_list",
        items=[
            {"date": date(2009, 1, 14), "outlet": "TV", "title": "T", "url": ""},
            {"date": None, "outlet": "Press", "title": "P", "url": "https://e.org"},
        ],
    )

    assert ">14.01.2009<" in html and 'class="media-date mono">—' in html


def test_footer_and_cta_compose_other_includes():
    footer = render("footer", heading="Hi", email="a@b.ch", codes=["PL"], holder="Jane")
    cta = render("cta", title="T", label="Go", href="/x", variant="ghost")

    assert 'href="mailto:a@b.ch"' in footer and 'class="lang-pill"' in footer
    assert "Jane." in footer
    assert 'class="btn btn-ghost" href="/x"' in cta


@pytest.mark.parametrize("path", sorted(INCLUDES.glob("*.html")), ids=lambda p: p.name)
def test_every_include_compiles(path):
    get_template(f"includes/{path.name}")


def test_missing_include_still_raises():
    with pytest.raises(TemplateDoesNotExist):
        get_template("includes/nope.html")


# ---------------------------------------------------------------- page de démonstration


@pytest.mark.django_db
def test_demo_page_is_a_404_outside_debug(client, settings):
    settings.DEBUG = False

    assert client.get("/_composants").status_code == 404
    assert client.get("/_composants/").status_code == 404


@pytest.mark.django_db
def test_demo_page_lists_every_component_in_debug(client, settings):
    settings.DEBUG = True

    response = client.get("/_composants")
    html = response.content.decode()

    assert response.status_code == 200
    assert 'name="robots" content="noindex"' in html
    for anchor in re.findall(r'href="#([a-z-]+)">(?:\d+|\+) ·?', html.split("demo-toc")[1]):
        assert f'id="{anchor}"' in html, anchor
    for marker in (
        "site-nav", "section-head", "btn-ghost", "status-dot", "pill-row", "iris", "pull-quote",
        "service-grid", "off-duty-grid", "aside-row", "offer-note", "timeline", "research-thumb",
        "personal-photo", "edu-card", "pub-list", "media-list", "site-footer", "demo-icons",
        "cta", "accordion__item",
    ):  # fmt: skip
        assert marker in html, marker
    assert html.count('<svg class="icon"') >= len(ICONS)


def test_demo_data_uses_no_real_content():
    context = demo.get_context()

    assert context["photo"]["url"].endswith("demo/portrait.svg")
    assert "example" in str(context).lower()
