from django.apps import apps as django_apps
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


def get_nav_items(site: Site | None, current_page: Page | None, request) -> list[dict]:
    """Éléments de `includes/nav.html` : {label, href, current} pour chaque page du menu."""
    return [
        {
            "label": page.title,
            "href": page.get_url(request) or "",
            "current": current_page is not None and page.pk == current_page.pk,
        }
        for page in get_main_menu(site)
    ]


def resolve_link(page: Page | None, url: str, request) -> tuple[str, bool]:
    """(href, externe) d'un lien « page interne OU URL externe » (voir `_require_page_or_url`).

    Une page sans URL publique (brouillon, hors site) donne « # » : le lien reste un lien.
    """
    if page is not None:
        return page.get_url(request) or "#", False
    return url or "", bool(url)


def button_props(value, request, label_key: str = "label") -> dict:
    """Paramètres de `includes/button.html` pour un bloc bouton ou appel à l'action."""
    href, external = resolve_link(value.get("page"), value.get("url"), request)
    return {
        "label": value[label_key],
        "href": href,
        "variant": value["variant"],
        "external": external,
    }


def offer_items(pages, request) -> list[dict]:
    """Éléments de `includes/offer_note.html` pour des pages de service."""
    return [
        {"title": page.title, "href": page.get_url(request) or "", "summary": page.summary}
        for page in pages
    ]


def get_contact_details(page, request) -> dict:
    """Coordonnées affichées sur la page de contact : celles de la page, sinon celles du profil."""
    from apps.profile.services import get_site_profile

    profile = get_site_profile(request)
    return {
        "email": page.email or profile.email,
        "phone": page.phone,
        "address": page.address,
        "linkedin_url": profile.linkedin_url,
    }


# (titre, slug, modèle, [(titre, slug) des ServicePage enfants])
SITE_TREE = [
    ("About", "about", "pages.StandardPage", []),
    (
        "Expertise",
        "expertise",
        "services.ServiceIndexPage",
        [
            ("Medical Affairs Consulting", "medical-affairs-consulting"),
            ("Patient Programs & Advocacy", "patient-programs-advocacy"),
            ("Coaching", "coaching"),
        ],
    ),
    ("Experience", "experience", "pages.StandardPage", []),
    ("Publications", "publications", "pages.StandardPage", []),
    ("Personal", "personal", "pages.StandardPage", []),
    ("Contact", "contact", "pages.ContactPage", []),
]


def create_site_pages(home: Page) -> list[Page]:
    """Crée sous l'accueil les pages du site, en brouillon (non publiées) et vides.

    Idempotent : une page dont le slug existe déjà sous son parent est laissée telle quelle.
    Retourne les pages créées. Les pages de premier niveau apparaissent dans le menu une fois
    publiées ; les services enfants n'y apparaissent pas.
    """
    created: list[Page] = []

    def ensure(parent: Page, title: str, slug: str, model_label: str, in_menu: bool) -> Page:
        existing = parent.get_children().filter(slug=slug).first()
        if existing is not None:
            return existing
        model = django_apps.get_model(model_label)
        page = parent.add_child(
            instance=model(title=title, slug=slug, live=False, show_in_menus=in_menu)
        )
        created.append(page)
        return page

    for title, slug, model_label, children in SITE_TREE:
        parent = ensure(home, title, slug, model_label, in_menu=True)
        for child_title, child_slug in children:
            ensure(parent, child_title, child_slug, "services.ServicePage", in_menu=False)
    return created
