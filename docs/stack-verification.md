# bkpolok — Stack verification & runbook

Last verified 2026-09-18 (macOS, Darwin 24.6, arm64), after installing the missing pieces.
Per component: status, how to re-check, how to fix.

## Summary

| Component | Status | Detail |
|---|---|---|
| Python | OK | 3.12.14 local; 3.12-slim in the image |
| uv | OK | 0.12.16 (local and pinned in Dockerfile), lockfile in sync |
| Django 5.x | OK | 5.2.17; `check` clean, no missing migrations |
| Wagtail 6.x | OK | 6.4.2; admin login, home, sitemap, robots, `/healthz` all return 200 |
| PostgreSQL 16 | OK | Container `postgres:16` (16.15) healthy; Homebrew 16.15 also running locally |
| Docker Compose | OK | 5.5.1 via `docker compose` plugin; runtime = Colima (Docker server 29.5.2) |
| Caddy | Installed, not configured | 2.11.4 installed via Homebrew; no Caddyfile/`deploy/` in the repo (see section 6) |
| ruff / pytest | OK | lint + format clean; 10 tests pass inside the `web` container |
| Prod image | OK | `--target prod` builds; `collectstatic` succeeds (214 files) |

## Changes made on 2026-09-18

Installed (Homebrew): `colima` 0.10.3 (+ `lima`), `caddy` 2.11.4.
Machine config: `~/.docker/cli-plugins/docker-compose` symlink so `docker compose` works.
Repo:
- `.env` created from `.env.example` with a generated `SECRET_KEY` and `POSTGRES_PASSWORD` (gitignored, mode 600).
- `config/settings/base.py`: `FORMS_URLFIELD_ASSUME_HTTPS = True` (silences the Django 6.0 URLField warning; URL fields without a scheme now default to https).
- `Dockerfile`: `uv:latest` pinned to `uv:0.12.16`.
- Not touched: `deploy/`, `.github/workflows/` (project rule).

Remaining test warning (1): Django announces `FORMS_URLFIELD_ASSUME_HTTPS` itself is removed in 6.0. Expected; drop the setting when upgrading to Django 6.

## 1. Python + uv

```bash
uv --version
uv lock --check
uv sync                          # (re)create .venv with dev deps
```
Add deps with `uv add <pkg>` / `uv add --dev <pkg>`.

## 2. Django 5.x

```bash
docker compose exec web python manage.py check
docker compose exec web python manage.py makemigrations --check --dry-run   # "No changes detected"
```
- `SECRET_KEY` and `DATABASE_URL` are required env vars (no defaults). Compose builds `DATABASE_URL` from the `POSTGRES_*` values in `.env`.
- Locale `fr-ch`, timezone `Europe/Zurich`.
- Prod: `ALLOWED_HOSTS` mandatory, secure cookies, trusts `X-Forwarded-Proto` (needs the Caddy proxy in front).
- `check --deploy` on prod settings leaves 3 expected warnings: W004 HSTS (opt-in via `SECURE_HSTS_SECONDS`, set only once HTTPS is confirmed, it is hard to undo), W008 SSL redirect (Caddy does the redirect), W009 (only if `SECRET_KEY` is weak; use a long random one in prod).

## 3. Wagtail 6.x

Dev URLs: `/admin/` (Wagtail), `/django-admin/`, `/healthz`, `/robots.txt`, `/sitemap.xml`.
```bash
docker compose exec web python manage.py createsuperuser     # first login
```
Home page comes from migration `apps/pages/migrations/0002_create_homepage.py`.
Search backend is the database one (no Elasticsearch).

## 4. PostgreSQL 16

Container (`db`): image `postgres:16`, volume `pgdata`, `pg_isready` healthcheck, port 5432 not published (no clash with the Homebrew instance).
```bash
docker compose exec db psql -U bkpolok -Atc "select version();"
docker compose ps                # db should be (healthy)
```
Local Homebrew instance (optional, for running outside Docker): `pg_isready`, `brew services start postgresql@16`.
Rules: pytest-django uses its own `test_*` database. Never run `manage.py flush` or touch the production DB.

## 5. Docker Compose + Colima

Colima is the container runtime (no Docker Desktop). It does not start at login by default.
```bash
colima start                      # after a reboot; check with: colima status
docker compose up --build         # or -d
docker compose exec web pytest
docker compose exec web python manage.py makemigrations && \
  docker compose exec web python manage.py migrate
docker compose down               # keeps the pgdata volume; add -v to wipe the dev DB
```
Optional autostart: `brew services start colima`.
If `docker compose` says "unknown command": re-create the plugin link
`ln -sfn /opt/homebrew/opt/docker-compose/bin/docker-compose ~/.docker/cli-plugins/docker-compose`.

Notes:
- `web` bind-mounts `.:/app` (hot reload), target `dev`, runs `migrate` then `runserver`.
- Dockerfile has a `prod` target (gunicorn, no dev deps); compose only uses `dev`.
  Check it: `docker build --target prod -t bkpolok-prod .`

## 6. Caddy  ← installed, needs a config decision

`caddy version` → 2.11.4. Nothing in the repo uses it yet: no Caddyfile, no `deploy/`, no proxy
service in compose. `deploy/` may not be modified without your explicit request, so it was not created.

Reference config (syntax validated with `caddy validate`; `example.ch` is a placeholder, and
`/srv/media` needs a volume shared with the `web` container):
```caddyfile
example.ch {
    encode zstd gzip

    handle_path /media/* {
        root * /srv/media
        file_server
    }

    reverse_proxy web:8000    # Caddy sets X-Forwarded-Proto automatically
}
```
Prod env to set: `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS=https://example.ch`,
`WAGTAILADMIN_BASE_URL=https://example.ch`, later `SECURE_HSTS_SECONDS`.
Static files are served by WhiteNoise (run `collectstatic` in the prod image, works today).
Do not run the Homebrew `caddy` service on a laptop unless you want it on ports 80/443.

## 7. Dev tooling

```bash
docker compose exec web ruff check .
docker compose exec web ruff format .
docker compose exec web pytest
```
Outside Docker: `uv run pytest` needs `SECRET_KEY` and `DATABASE_URL` (e.g. a `DATABASE_URL` line in `.env` pointing at Homebrew Postgres, after `createdb bkpolok`).

## Open items

1. Decide the Caddy deployment layout (Caddyfile location, prod compose file); needs your OK for anything under `deploy/`.
2. Commit the changes (`Dockerfile`, `config/settings/base.py`, `docs/`); nothing is committed yet.
3. Create a superuser to log into `/admin/`.
