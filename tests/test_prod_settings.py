"""Réglages de production : chargés dans un environnement contrôlé, sans toucher à la base."""

import importlib

import pytest
from django.core.exceptions import ImproperlyConfigured

GOOD_KEY = "k" * 64
BASE_ENV = {
    "SECRET_KEY": GOOD_KEY,
    "ALLOWED_HOSTS": "exemple.ch",
    "WAGTAILADMIN_BASE_URL": "https://exemple.ch",
    "DATABASE_URL": "postgres://u:p@db:5432/x",
}


@pytest.fixture
def load_prod(monkeypatch):
    def load(**overrides):
        for name in ("SECRET_KEY", "ALLOWED_HOSTS", "WAGTAILADMIN_BASE_URL", "SECURE_HSTS_SECONDS"):
            monkeypatch.delenv(name, raising=False)
        for name, value in {**BASE_ENV, **overrides}.items():
            monkeypatch.setenv(name, value)
        import config.settings.base
        import config.settings.prod

        importlib.reload(config.settings.base)
        return importlib.reload(config.settings.prod)

    yield load
    # Ne laisse pas les réglages de production dans le cache d'imports des autres tests.
    import config.settings.base

    importlib.reload(config.settings.base)


def test_prod_defaults_are_secure(load_prod):
    prod = load_prod()

    assert prod.DEBUG is False
    assert prod.ALLOWED_HOSTS == ["exemple.ch"]
    assert prod.SESSION_COOKIE_SECURE and prod.CSRF_COOKIE_SECURE
    assert prod.SECURE_SSL_REDIRECT is True
    assert prod.SECURE_HSTS_SECONDS > 0
    assert prod.SECURE_HSTS_INCLUDE_SUBDOMAINS is False
    assert prod.SECURE_CONTENT_TYPE_NOSNIFF is True
    assert prod.SECURE_PROXY_SSL_HEADER == ("HTTP_X_FORWARDED_PROTO", "https")
    assert r"^healthz$" in prod.SECURE_REDIRECT_EXEMPT


@pytest.mark.parametrize("key", ["change-me", "change-me" + "x" * 60, "short"])
def test_prod_refuses_a_placeholder_or_short_secret_key(load_prod, key):
    with pytest.raises(ImproperlyConfigured):
        load_prod(SECRET_KEY=key)


def test_prod_requires_the_admin_base_url(load_prod, monkeypatch):
    load_prod()
    monkeypatch.delenv("WAGTAILADMIN_BASE_URL")

    with pytest.raises(ImproperlyConfigured):
        importlib.reload(importlib.import_module("config.settings.prod"))
