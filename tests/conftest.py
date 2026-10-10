import io

import pytest
from django.core.files.images import ImageFile
from PIL import Image as PILImage
from wagtail.images import get_image_model
from wagtail.models import Page, Site

from apps.pages.models import HomePage
from apps.profile.models import SiteProfile


@pytest.fixture
def home() -> HomePage:
    return HomePage.objects.get()


@pytest.fixture
def site() -> Site:
    return Site.objects.get(is_default_site=True)


@pytest.fixture
def root() -> Page:
    return Page.objects.get(depth=1)


@pytest.fixture
def image():
    buffer = io.BytesIO()
    PILImage.new("RGB", (20, 20), "white").save(buffer, "PNG")
    return get_image_model().objects.create(title="test", file=ImageFile(buffer, name="test.png"))


@pytest.fixture
def profile(site) -> SiteProfile:
    """Profil de test avec des données neutres (sans lien avec le contenu réel du site)."""
    return SiteProfile.objects.create(
        site=site,
        first_name="Jane",
        last_name="Doe",
        short_name="J. Doe",
        legal_name="Jane Q. Doe",
        job_title="Director",
        employer="Acme",
        email="jane@example.ch",
        linkedin_url="https://www.linkedin.com/in/jane-doe",
        pubmed_url="https://pubmed.ncbi.nlm.nih.gov/?term=doe",
        footer_heading="Let's talk.",
        meta_description="A short description.",
    )
