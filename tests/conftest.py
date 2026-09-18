import pytest
from wagtail.models import Page, Site

from apps.pages.models import HomePage


@pytest.fixture
def home() -> HomePage:
    return HomePage.objects.get()


@pytest.fixture
def site() -> Site:
    return Site.objects.get(is_default_site=True)


@pytest.fixture
def root() -> Page:
    return Page.objects.get(depth=1)
