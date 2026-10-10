import pytest
from wagtail.models import Page, Site

from apps.pages.models import HomePage

pytestmark = pytest.mark.django_db


def test_home_page_returns_200(client):
    response = client.get("/")

    assert response.status_code == 200
    assert '<html lang="en">' in response.content.decode()


def test_home_page_is_titled_in_english(home):
    assert home.title == "Home"


def test_default_site_points_to_home_page():
    site = Site.objects.get(is_default_site=True)

    assert isinstance(site.root_page.specific, HomePage)


def test_page_tree_is_consistent():
    problems = Page.find_problems()

    assert problems == ([], [], [], [], [])
