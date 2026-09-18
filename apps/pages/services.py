from django.db import connection
from wagtail.models import Page, Site


def check_database() -> bool:
    """Retourne True si la base de données répond."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        return False
    return True


def get_main_menu(site: Site | None) -> list[Page]:
    """Pages live, marquées « afficher dans les menus », enfants directs de la racine du site."""
    if site is None:
        return []
    return list(site.root_page.get_children().live().in_menu().specific())
