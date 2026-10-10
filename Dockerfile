FROM python:3.12-slim AS base

COPY --from=ghcr.io/astral-sh/uv:0.12.16 /uv /usr/local/bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_LINK_MODE=copy \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Cible dev : dépendances de développement incluses, code monté en volume par compose.
FROM base AS dev
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project
COPY . .
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# Cible prod : sans dépendances de développement.
FROM base AS prod
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev
COPY . .
ENV DJANGO_SETTINGS_MODULE=config.settings.prod
RUN SECRET_KEY=build-only-placeholder-key-not-used-at-runtime-0123456789-abcdefghijklmnopqrstuvwxyz \
    ALLOWED_HOSTS=localhost \
    WAGTAILADMIN_BASE_URL=http://localhost \
    DATABASE_URL=sqlite:////tmp/collectstatic.db \
    python manage.py collectstatic --noinput
EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
