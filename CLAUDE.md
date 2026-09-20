# Projet : site de service <bkpolok>

## Stack
Django 5.x, Wagtail 6.x, PostgreSQL 16, Docker Compose, Caddy, déploiement Infomaniak VPS.
Gestion des dépendances : uv. Lint/format : ruff. Tests : pytest + pytest-django.

## Conventions
- Toute modification de modèle => migration commitée dans le même commit.
- Pas de logique métier dans les templates ni dans les vues : services dans `apps/<app>/services.py`.
- Contenu éditorial = pages Wagtail. Données structurées (produits, tendances) = modèles Django classiques.
- Textes du site en anglais (en). Formats de dates et prix suisses (CHF).
- Secrets uniquement via variables d'environnement, jamais en dur, jamais commités.

## Commandes
- Dev : `docker compose up`
- Tests : `docker compose exec web pytest`
- Migrations : `docker compose exec web python manage.py makemigrations && ... migrate`

## Interdits
- Ne pas modifier `deploy/` ou `.github/workflows/` sans me le demander explicitement.
- Ne jamais lancer `manage.py flush` ou toucher à la base de production.