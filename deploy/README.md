# Hostinger VPS deployment

This deployment uses Docker Compose, PostgreSQL, Gunicorn, and Caddy. It is for a Hostinger VPS
with Docker support, not shared hosting. The repository's current `design/import-artifact` branch
is 10 commits ahead of `main`; the commands below deliberately clone that branch. Deploy `main`
instead after merging the site changes there.

## VPS prerequisites

- A Hostinger VPS with Docker Engine and the Docker Compose plugin installed.
- A domain whose A records (apex and `www`) point to the VPS IPv4 address. Remove stale AAAA
  records unless IPv6 is configured on the VPS.
- Inbound TCP ports 80 and 443 allowed by both the Hostinger firewall and the VPS firewall.

## First deployment

SSH into the VPS, then run:

```sh
git clone --branch design/import-artifact --single-branch \
  https://github.com/bbriguet/bkpolok.git
cd bkpolok
cp .env.production.example .env
```

Edit `.env`: replace `example.ch` with your domain in every relevant setting. Generate values on
the VPS and paste them into `.env`:

```sh
python3 -c 'import secrets; print(secrets.token_urlsafe(64))'
openssl rand -hex 32
chmod 600 .env
```

Use the first output for `SECRET_KEY`, the second for `POSTGRES_PASSWORD`. Keep the database
password hex-only so it is safe in the `DATABASE_URL`. Configure SMTP values if the contact form
should send email. Do not put secrets in GitHub or commit `.env`.

After DNS resolves to the VPS, start the site:

```sh
docker compose -f compose.production.yml up -d --build
docker compose -f compose.production.yml ps
docker compose -f compose.production.yml logs -f caddy web
```

Caddy obtains and renews HTTPS certificates automatically. The app runs migrations and collects
static files when it starts. PostgreSQL is only reachable on the private Compose network; Caddy
is the only service exposing ports.

Create the production Wagtail administrator:

```sh
docker compose -f compose.production.yml exec web python manage.py createsuperuser
```

If this is a new, empty site, load the prepared editorial content and publish the pages in Wagtail:

```sh
docker compose -f compose.production.yml exec web python manage.py charger_contenu_initial
```

Confirm the site and `/admin/` work over HTTPS before enabling HSTS by changing
`SECURE_HSTS_SECONDS=0` to `SECURE_HSTS_SECONDS=2592000` in `.env`, then recreate the web service:

```sh
docker compose -f compose.production.yml up -d --force-recreate web
```

## Deploy updates

```sh
git pull --ff-only
docker compose -f compose.production.yml up -d --build
```

## Operations

```sh
docker compose -f compose.production.yml logs -f web caddy
docker compose -f compose.production.yml exec -T db sh -c \
  'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' > bkpolok-$(date +%F).sql
```

Back up the PostgreSQL dump and the `media_data` volume off the VPS regularly. Named volumes
survive container rebuilds, but do not protect data if the VPS or its disk is lost. Do not run
`docker compose down -v` on production.