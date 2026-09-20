import json
import re
from datetime import date
from xml.etree import ElementTree

import pytest
from django.core.exceptions import ValidationError
from wagtail.models import Page

from apps.pages.models import StandardPage
from apps.pages.services import create_site_pages
from apps.profile.models import Experience, ExperienceImage

pytestmark = pytest.mark.django_db

# URLs de l'arbre du site (docs/site-architecture.md) ; la dernière est la confirmation du contact.
EXPECTED_URLS = [
    "/",
    "/about/",
    "/expertise/",
    "/expertise/medical-affairs-consulting/",
    "/expertise/patient-programs-advocacy/",
    "/expertise/coaching/",
    "/experience/",
    "/publications/",
    "/personal/",
    "/contact/",
    "/contact/thank-you/",
]

HERO = {
    "type": "hero",
    "value": {
        "eyebrow": "Leadership",
        "role": "A role",
        "badge_text": "",
        "thesis": "An introduction.",
        "buttons": [],
        "image": None,
    },
}


def hero_with_image(image):
    return {
        **HERO,
        "value": {**HERO["value"], "image": {"image": image.pk, "alt_text": "Portrait"}},
    }


@pytest.fixture
def published_site(home, profile):
    """Le site complet : chaque page de l'arbre publiée, l'accueil avec un bandeau."""
    create_site_pages(home)
    for page in Page.objects.descendant_of(home).specific():
        page.save_revision().publish()
    home.body = json.dumps([HERO])
    home.save_revision().publish()
    return home


def find_urls(home):
    return ["/"] + [p.url for p in Page.objects.descendant_of(home).live().order_by("path")]


def test_the_published_tree_has_exactly_the_documented_urls(published_site):
    urls = find_urls(published_site) + ["/contact/thank-you/"]

    assert urls == EXPECTED_URLS


@pytest.mark.parametrize("url", EXPECTED_URLS)
def test_every_url_answers_200_with_one_h1_and_the_seo_basics(client, published_site, url):
    response = client.get(url)
    html = response.content.decode()

    assert response.status_code == 200
    assert len(re.findall(r"<h1[\s>]", html)) == 1
    assert re.search(r"<title>[^<]+</title>", html)
    assert '<meta property="og:title"' in html
    assert '<meta property="og:site_name" content="Jane Doe">' in html
    assert '<meta name="twitter:card"' in html
    assert '<main id="content"' in html and "<nav " in html and "<footer" in html


@pytest.mark.parametrize("url", ["/robots.txt", "/sitemap.xml", "/healthz"])
def test_technical_urls_answer_200(client, published_site, url):
    assert client.get(url).status_code == 200


def test_sitemap_lists_live_pages_only(client, published_site):
    published_site.add_child(instance=StandardPage(title="Draft", slug="draft", live=False))
    response = client.get("/sitemap.xml")
    root = ElementTree.fromstring(response.content)
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locations = {loc.text for loc in root.findall("s:url/s:loc", ns)}

    assert response["Content-Type"].startswith("application/xml")
    assert {f"http://localhost{url}" for url in EXPECTED_URLS[:-1]} <= locations
    assert not any("thank-you" in loc or "draft" in loc for loc in locations)


def test_robots_txt_hides_the_admin_and_points_to_the_sitemap(client):
    body = client.get("/robots.txt").content.decode()

    assert client.get("/robots.txt")["Content-Type"] == "text/plain; charset=utf-8"
    assert "Disallow: /admin/" in body
    assert "Sitemap: http://testserver/sitemap.xml" in body


def test_meta_description_falls_back_from_page_to_summary_to_profile(client, published_site):
    service = Page.objects.get(slug="coaching").specific
    about = Page.objects.get(slug="about").specific

    assert (
        'name="description" content="A short description."'
        in client.get(about.url).content.decode()
    )

    service.summary = "One-to-one coaching for medical affairs leaders."
    service.save_revision().publish()
    html = client.get(service.url).content.decode()
    assert 'name="description" content="One-to-one coaching for medical affairs leaders."' in html
    assert 'property="og:description" content="One-to-one coaching' in html

    service.search_description = "Explicit description."
    service.save_revision().publish()
    assert (
        'name="description" content="Explicit description."'
        in client.get(service.url).content.decode()
    )


def test_open_graph_image_comes_from_the_page_then_the_profile(
    client, published_site, profile, image
):
    about = Page.objects.get(slug="about").specific
    assert "og:image" not in client.get(about.url).content.decode()
    assert 'content="summary"' in client.get(about.url).content.decode()

    profile.share_image = image
    profile.save()
    html = client.get(about.url).content.decode()
    assert re.search(r'og:image" content="http://localhost/media/images/test[^"]+"', html)
    assert 'content="summary_large_image"' in html
    # Dimensions réelles de la rendition (Wagtail n'agrandit pas l'image de test de 20×20).
    assert 'og:image:width" content="20"' in html and 'og:image:height" content="12"' in html

    about.og_image = image
    about.save_revision().publish()
    assert 'og:image" content="http://localhost/media/' in client.get(about.url).content.decode()


def test_canonical_and_og_url_use_the_absolute_page_url(client, published_site):
    html = client.get("/about/").content.decode()

    assert '<link rel="canonical" href="http://localhost/about/">' in html
    assert '<meta property="og:url" content="http://localhost/about/">' in html


def test_nav_and_footer_come_from_the_tree_not_from_the_templates(client, published_site):
    nav_page = Page.objects.get(slug="personal").specific
    nav_page.show_in_menus = False
    nav_page.save_revision().publish()
    html = client.get("/").content.decode()
    nav = html.split('aria-label="Main navigation"')[1].split("</nav>")[0]

    assert re.findall(r'<a href="([^"]+)"', nav) == [
        "/about/",
        "/expertise/",
        "/experience/",
        "/publications/",
        "/contact/",
    ]
    assert 'href="mailto:jane@example.ch"' in html  # pied de page : profil du site


# ------------------------------------------------------------------ un seul <h1>


def test_a_hero_replaces_the_page_title_h1_on_every_page_type(client, published_site):
    for slug in ("about", "coaching", "expertise", "contact"):
        page = Page.objects.get(slug=slug).specific
        page.body = json.dumps([HERO])
        page.save_revision().publish()

        html = client.get(page.url).content.decode()

        assert len(re.findall(r"<h1[\s>]", html)) == 1, slug
        assert "<h1>Jane&nbsp;<em>Doe</em></h1>" in html


def test_a_hero_inside_a_section_still_gives_a_single_h1(client, home, profile):
    section = {
        "type": "section",
        "value": {"anchor": "", "background": "default", "content": [HERO]},
    }
    page = home.add_child(instance=StandardPage(title="S", slug="s", body=json.dumps([section])))
    page.save_revision().publish()

    html = client.get(page.url).content.decode()

    assert len(re.findall(r"<h1[\s>]", html)) == 1
    assert "<h1>S</h1>" not in html


def test_home_without_a_hero_still_has_its_h1_when_the_body_is_not_empty(client, home, profile):
    home.body = json.dumps([{"type": "paragraph", "value": "<p>Text</p>"}])
    home.save_revision().publish()

    html = client.get("/").content.decode()

    assert len(re.findall(r"<h1[\s>]", html)) == 1


def test_two_heroes_are_refused_even_when_nested_in_a_section(home):
    section = {
        "type": "section",
        "value": {"anchor": "", "background": "default", "content": [HERO]},
    }
    page = StandardPage(title="Two", slug="two", body=json.dumps([HERO, section]))

    with pytest.raises(ValidationError):
        page.clean()


# ------------------------------------------------------------------ images


def test_every_image_has_dimensions_and_alt_and_is_lazy_except_the_hero(
    client, home, profile, image
):
    experience = Experience.objects.create(
        title="Role",
        organisation="Acme",
        category="industry",
        start_date=date(2020, 1, 1),
        date_precision="month",
    )
    ExperienceImage.objects.create(
        experience=experience, image=image, alt_text="A figure", caption="FIG. 1"
    )
    blocks = [
        hero_with_image(image),
        {
            "type": "heading",
            "value": {
                "text": "Off the clock",
                "level": "h2",
                "eyebrow": "",
                "lede": "",
                "pills": [],
                "image": {"image": image.pk, "alt_text": "A round photo"},
            },
        },
        {"type": "image", "value": {"image": image.pk, "alt_text": "A plain image"}},
        {"type": "timeline", "value": {"category": "industry"}},
    ]
    home.body = json.dumps(blocks)
    home.save_revision().publish()

    html = client.get("/").content.decode()
    images = re.findall(r"<img\b[^>]*>", html)

    assert len(images) == 4
    for tag in images:
        assert re.search(r'\swidth="\d+"', tag), tag
        assert re.search(r'\sheight="\d+"', tag), tag
        assert re.search(r'\salt="[^"]+"', tag), tag
    lazy = [tag for tag in images if 'loading="lazy"' in tag]
    eager = [tag for tag in images if 'loading="lazy"' not in tag]
    assert len(lazy) == 3
    assert len(eager) == 1 and 'alt="Portrait"' in eager[0]  # bandeau : image du premier écran
