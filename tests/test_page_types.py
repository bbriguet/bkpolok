import json

import pytest

from apps.pages.models import ContactPage, StandardPage
from apps.services.models import ServiceIndexPage, ServicePage

pytestmark = pytest.mark.django_db


@pytest.fixture
def full_body(image, home):
    return json.dumps(
        [
            {"type": "heading", "value": {"text": "Un titre", "level": "h2"}},
            {"type": "paragraph", "value": "<p>Du <b>texte</b> riche.</p>"},
            {
                "type": "image",
                "value": {"image": image.pk, "alt_text": "Une image", "decorative": False},
            },
            {"type": "quote", "value": {"text": "Une citation", "author": "Quelqu’un"}},
            {
                "type": "call_to_action",
                "value": {
                    "title": "Contactez-nous",
                    "text": "",
                    "button_label": "Écrire",
                    "page": home.pk,
                    "url": "",
                },
            },
            {
                "type": "faq",
                "value": {
                    "title": "FAQ",
                    "items": [{"question": "Pourquoi ?", "answer": "<p>Parce que.</p>"}],
                },
            },
        ]
    )


def test_all_page_types_render_every_block(client, home, full_body):
    standard = home.add_child(
        instance=StandardPage(title="Standard", slug="standard", body=full_body)
    )
    contact = home.add_child(
        instance=ContactPage(
            title="Contact",
            slug="contact",
            email="info@example.ch",
            phone="+41 21 123 45 67",
            address="Rue 1\n1000 Lausanne",
            body=full_body,
        )
    )
    index = home.add_child(
        instance=ServiceIndexPage(title="Services", slug="services", body=full_body)
    )
    service = index.add_child(
        instance=ServicePage(title="Audit", slug="audit", summary="Un audit.", body=full_body)
    )

    for page in (standard, contact, index, service):
        response = client.get(page.url)
        html = response.content.decode()
        assert response.status_code == 200, page
        assert "<h2>Un titre</h2>" in html
        assert 'alt="Une image"' in html
        assert '<blockquote class="pull-quote">' in html
        assert 'class="btn btn-primary"' in html
        assert "<details" in html

    assert "Audit" in client.get(index.url).content.decode()
    assert "info@example.ch" in client.get(contact.url).content.decode()


def test_menu_lists_pages_marked_in_menu(client, home):
    home.add_child(
        instance=StandardPage(title="Notre histoire", slug="histoire", show_in_menus=True)
    )
    home.add_child(instance=StandardPage(title="Cachée", slug="cachee", show_in_menus=False))

    html = client.get("/").content.decode()

    assert "Notre histoire" in html
    assert "Cachée" not in html


def test_home_page_only_allows_expected_children(home):
    assert set(home.specific_class.allowed_subpage_models()) == {
        ServiceIndexPage,
        StandardPage,
        ContactPage,
    }
