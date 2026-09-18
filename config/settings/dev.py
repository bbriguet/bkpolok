from .base import *  # noqa: F403
from .base import env

DEBUG = env.bool("DEBUG", default=True)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1", "[::1]"])

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# runserver sert les statiques ; évite l'avertissement WhiteNoise (staticfiles/ absent).
MIDDLEWARE = [m for m in MIDDLEWARE if "whitenoise" not in m]  # noqa: F405
