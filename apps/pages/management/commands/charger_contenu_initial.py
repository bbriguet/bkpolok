from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.pages.initial_content import ContentError, Report, load_initial_content

DEFAULT_FILE = Path(settings.BASE_DIR) / "_artifact" / "design" / "content.yaml"


class Command(BaseCommand):
    help = (
        "Charge content.yaml : pages Wagtail (StreamField) et objets du profil. Idempotent : "
        "ne remplace jamais une valeur déjà remplie, sauf avec --update. "
        "Les pages restent en brouillon."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--file", type=Path, default=DEFAULT_FILE, help="Fichier YAML à charger."
        )
        parser.add_argument(
            "--update",
            action="store_true",
            help="Remplace aussi les valeurs déjà remplies par celles du YAML.",
        )

    def handle(self, *args, **options):
        path = options["file"]
        if not path.is_file():
            raise CommandError(f"Fichier introuvable : {path}")
        try:
            report = load_initial_content(path, update=options["update"])
        except ContentError as error:
            raise CommandError(f"Import annulé (rien n'a été écrit) — {error}") from error
        self.write_report(report, path)

    def write_report(self, report: Report, path: Path) -> None:
        out = self.stdout.write
        out(self.style.MIGRATE_HEADING(f"Contenu chargé depuis {path}"))

        out("\nPages (brouillons, à publier dans l'admin Wagtail)")
        out(f"  créées : {len(report.pages_created)}")
        for where in report.pages_created:
            out(f"    {where}")
        out(f"  remplies : {len(report.pages_filled)}")
        for where in report.pages_filled:
            out(f"    {where}")
        out(f"  déjà à jour : {len(report.pages_unchanged)}")

        out("\nObjets par modèle")
        for name in report.models():
            out(
                f"  {name} : {report.created[name]} créé(s), {report.updated[name]} complété(s), "
                f"{report.unchanged[name]} inchangé(s)"
            )

        if report.notes:
            out("\nÉcarts et valeurs non écrasées")
            for note in report.notes:
                out(f"  - {note}")

        if report.not_imported:
            out("\nNon importé (absent du YAML ou fichier manquant)")
            for item in report.not_imported:
                out(f"  - {item}")

        total = len(report.todos) + len(report.todo_comments)
        style = self.style.WARNING if total else self.style.SUCCESS
        out(style(f"\nTODO restants : {total}"))
        for todo in report.todos:
            out(f"  - {todo.path}\n      -> {todo.location}\n      valeur : {todo.value!r}")
        for number, line in report.todo_comments:
            out(f"  - ligne {number} du YAML (commentaire, non importable) : {line}")
