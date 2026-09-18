from unittest import mock

import pytest

pytestmark = pytest.mark.django_db


def test_healthz_ok(client):
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_healthz_returns_503_when_database_is_down(client):
    with mock.patch("apps.pages.views.check_database", return_value=False):
        response = client.get("/healthz")

    assert response.status_code == 503


def test_robots_txt(client):
    response = client.get("/robots.txt")

    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/plain")
    body = response.content.decode()
    assert "Disallow: /admin/" in body
    assert "Sitemap: http://testserver/sitemap.xml" in body


def test_sitemap_lists_home_page(client):
    response = client.get("/sitemap.xml")

    assert response.status_code == 200
    assert "xml" in response["Content-Type"]
    assert "<urlset" in response.content.decode()
