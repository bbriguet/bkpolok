from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403
from .base import SECRET_KEY, env

DEBUG = False
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")  # obligatoire en production
# Sans valeur par défaut : les liens des emails de l'admin pointeraient sur localhost.
WAGTAILADMIN_BASE_URL = env("WAGTAILADMIN_BASE_URL")

# Refuse de démarrer avec la valeur d'exemple de .env.example ou une clé trop courte.
if SECRET_KEY.startswith("change-me") or len(SECRET_KEY) < 50:
    raise ImproperlyConfigured("SECRET_KEY must be a random value of at least 50 characters.")

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# Caddy termine le TLS et redirige HTTP -> HTTPS ; Django fait confiance à son en-tête.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SECURE_REDIRECT_EXEMPT = [r"^healthz$"]  # sonde de santé en HTTP depuis le réseau Docker
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
# HSTS est irréversible côté navigateur : 30 jours par défaut, à passer à 31536000 (1 an) une fois
# le HTTPS validé. Les sous-domaines ne sont inclus que sur demande explicite.
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=2592000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False)

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("EMAIL_PORT", default=25)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default=EMAIL_HOST_USER)
