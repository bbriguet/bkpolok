import pytest
from django.core.management import call_command
from wagtail.models import Page

from apps.pages.models import ContactPage, StandardPage
from apps.pages.services import SITE_TREE, create_site_pages
from apps.services.models import ServiceIndexPage, ServicePage

pytestmark = pytest.mark.django_db


def test_create_site_pages_builds_the_tree_as_drafts(home):
    created = create_site_pages(home)

    slugs = [p.slug for p in home.get_children()]
    assert slugs == ["about", "expertise", "experience", "publications", "personal", "contact"]
    assert len(created) == 9  # 6 pages + 3 offers
    assert all(not p.live for p in created)

    expertise = home.get_children().get(slug="expertise")
    assert isinstance(expertise.specific, ServiceIndexPage)
    assert [p.slug for p in expertise.get_children()] == [
        "medical-affairs-consulting",
        "patient-programs-advocacy",
        "coaching",
    ]
    assert isinstance(expertise.get_children().first().specific, ServicePage)
    assert isinstance(home.get_children().get(slug="contact").specific, ContactPage)
    assert isinstance(home.get_children().get(slug="about").specific, StandardPage)


def test_create_site_pages_targets_the_expected_urls(home):
    create_site_pages(home)

    urls = {p.url_path for p in Page.objects.descendant_of(home)}

    assert "/home/about/" in urls
    assert "/home/expertise/coaching/" in urls
    assert "/home/contact/" in urls


def test_create_site_pages_is_idempotent(home):
    create_site_pages(home)

    assert create_site_pages(home) == []
    assert Page.objects.descendant_of(home).count() == 9


def test_top_level_pages_are_in_the_menu_but_services_are_not(home):
    create_site_pages(home)

    assert all(p.show_in_menus for p in home.get_children())
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
    assert [slug for _, slug, _, _ in SITE_TREE] == [
        "about",
        "expertise",
        "experience",
        "publications",
        "personal",
        "contact",
    ]
