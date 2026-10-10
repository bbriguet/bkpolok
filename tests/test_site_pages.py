from io import StringIO

import pytest
from django.core.management import call_command
from wagtail.models import Page

from apps.pages.models import ContactPage, StandardPage
from apps.pages.services import SITE_TREE, configure_site, create_site_pages, publish_drafts
from apps.services.models import ServiceIndexPage, ServicePage

pytestmark = pytest.mark.django_db


def test_create_site_pages_builds_the_tree_as_drafts(home):
    created = create_site_pages(home)

    slugs = [p.slug for p in home.get_children()]
    assert slugs == [
        "about",
        "services",
        "experience",
        "publications",
        "personal",
        "contact",
        "legal-notice",
        "privacy",
    ]
    assert len(created) == 11  # 8 pages + 3 offers
    assert all(not p.live for p in created)

    services = home.get_children().get(slug="services")
    assert isinstance(services.specific, ServiceIndexPage)
    assert [p.slug for p in services.get_children()] == [
        "medical-affairs-consulting",
        "patient-programs-advocacy",
        "coaching",
    ]
    assert isinstance(services.get_children().first().specific, ServicePage)
    assert isinstance(home.get_children().get(slug="contact").specific, ContactPage)
    assert isinstance(home.get_children().get(slug="about").specific, StandardPage)


def test_create_site_pages_targets_the_expected_urls(home):
    create_site_pages(home)

    urls = {p.url_path for p in Page.objects.descendant_of(home)}

    assert "/home/about/" in urls
    assert "/home/services/coaching/" in urls
    assert "/home/legal-notice/" in urls and "/home/privacy/" in urls
    assert "/home/contact/" in urls


def test_create_site_pages_is_idempotent(home):
    create_site_pages(home)

    assert create_site_pages(home) == []
    assert Page.objects.descendant_of(home).count() == 11


def test_top_level_pages_are_in_the_menu_but_services_and_legal_pages_are_not(home):
    create_site_pages(home)

    in_menu = [p.slug for p in home.get_children() if p.show_in_menus]
    assert in_menu == ["about", "services", "experience", "publications", "personal", "contact"]
    assert not any(p.show_in_menus for p in Page.objects.filter(depth=4))


def test_drafts_are_not_public_and_not_in_the_nav(client, home):
    create_site_pages(home)

    assert client.get("/about/").status_code == 404
    assert 'href="/about/"' not in client.get("/").content.decode()


def test_published_pages_appear_in_the_nav_in_tree_order(client, home):
    create_site_pages(home)
    for slug in ("about", "contact"):
        home.get_children().get(slug=slug).specific.save_revision().publish()

    html = client.get("/").content.decode()

    assert html.index('href="/about/"') < html.index('href="/contact/"')
    assert client.get("/about/").status_code == 200


def test_management_command(home, capsys):
    call_command("create_site_pages")
    first = capsys.readouterr().out
    call_command("create_site_pages")
    second = capsys.readouterr().out

    assert "/home/about/" in first
    assert "Nothing to create" in second


def test_site_tree_covers_every_nav_link_of_the_design():
    assert [slug for _, slug, _, _, in_menu in SITE_TREE if in_menu] == [
        "about",
        "services",
        "experience",
        "publications",
        "personal",
        "contact",
    ]


def test_configure_site_uses_the_public_url(site):
    configure_site(site, "https://example.ch", "example")

    site.refresh_from_db()
    assert (site.hostname, site.port, site.site_name) == ("example.ch", 443, "example")
    assert site.root_url == "https://example.ch"


def test_configure_site_rejects_an_url_without_hostname(site):
    with pytest.raises(ValueError):
        configure_site(site, "example.ch", "example")


def test_publish_drafts_publishes_every_draft_once(client, home):
    create_site_pages(home)

    assert len(publish_drafts(home)) == 11
    assert publish_drafts(home) == []
    assert client.get("/services/coaching/").status_code == 200
    assert 'href="/about/"' in client.get("/").content.decode()


def test_publier_site_command(home, site):
    create_site_pages(home)
    out = StringIO()

    call_command("publier_site", base_url="https://example.ch", stdout=out)

    site.refresh_from_db()
    assert site.hostname == "example.ch"
    assert not Page.objects.descendant_of(home).not_live().exists()
    assert "Pages publiées : 11" in out.getvalue()
