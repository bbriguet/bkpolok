# Hostinger VPS deployment

This deployment uses public Docker images from GHCR, Docker Hub, and the official Caddy image.
The application image is built by GitHub Actions; Hostinger only pulls and runs it. It is intended
for a Hostinger VPS with Docker Compose, not shared hosting.

The production Compose file has no local `build`, custom `command`, or in-container healthcheck.
The app's default image command starts Gunicorn. Static files are collected while GitHub Actions
builds the image. Migrations and initial content are separate commands to run from Hostinger's
client after the services start.

## Before deployment

- Configure the apex domain and `www` A records to point to the VPS IPv4 address. Remove stale
  AAAA records unless IPv6 is configured.
- Allow inbound TCP ports 80 and 443 in the Hostinger and VPS firewalls.
- Push changes to `design/import-artifact` to trigger the image workflow.
- After the first successful workflow, GHCR creates the package as private by default. Make it
  public at <https://github.com/users/bbriguet/packages/container/bkpolok/settings> before
  deploying. GitHub does not let a public package become private again.
- Copy `.env.production.example` to `.env` on the VPS, or enter those values in Hostinger's
  environment-variable settings. Replace all examples with your domain and generated secrets;
  `SITE_DOMAIN` must be the bare domain (for example, `example.ch`), without `https://` or `www`.

Generate the secret values on the VPS:

```sh
python3 -c 'import secrets; print(secrets.token_urlsafe(64))'
openssl rand -hex 32
```

Use the first value as `SECRET_KEY` and the second as `POSTGRES_PASSWORD`. Keep the database
password hex-only because Compose interpolates it into `DATABASE_URL`. Configure SMTP values if
the contact form should send email. Never commit the populated `.env`.

## Start the stack

From the cloned repository's deployment branch, run in the Hostinger client:

```sh
git clone --branch design/import-artifact --single-branch https://github.com/bbriguet/bkpolok.git
cd bkpolok
cp .env.production.example .env
```

After configuring `.env` and confirming DNS resolves to the VPS:

```sh
docker compose -f compose.production.yml pull
docker compose -f compose.production.yml up -d
```

The app image is `ghcr.io/bbriguet/bkpolok:latest`. PostgreSQL and Caddy are pulled from public
registries. PostgreSQL is not published on a host port; Caddy exposes ports 80 and 443 and obtains
HTTPS certificates automatically.

## After launch

In Hostinger's command client, apply the database migrations:

```sh
docker compose -f compose.production.yml exec web python manage.py migrate --noinput
```

Create the Wagtail administrator:

```sh
docker compose -f compose.production.yml exec web python manage.py createsuperuser
```

For a new, empty site only, import the prepared pages and editorial content:

```sh
docker compose -f compose.production.yml exec web python manage.py charger_contenu_initial
```

Then sign in at `https://YOUR_DOMAIN/admin/`, review and publish the draft pages, and verify the
contact form and email settings. Once HTTPS works, change `SECURE_HSTS_SECONDS=0` to
`SECURE_HSTS_SECONDS=2592000` in `.env` and restart the web service.

## Updates and backups

Push a new commit to `design/import-artifact`; GitHub Actions rebuilds the `latest` image. Then run
in the Hostinger client:

```sh
docker compose -f compose.production.yml pull
docker compose -f compose.production.yml up -d
```

Back up PostgreSQL and the `media_data` volume off the VPS. Named volumes survive image updates,
but not VPS or disk loss. Do not remove production volumes when recreating the stack.