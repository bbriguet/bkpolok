from urllib.parse import urljoin

from django.apps import apps as django_apps
from django.db import connection
from django.utils.text import Truncator
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


def iter_blocks(stream):
    """Blocs d'un StreamField, y compris ceux du contenu des sections."""
    for child in stream:
        yield child
        if child.block_type == "section":
            yield from iter_blocks(child.value["content"])


def count_heroes(stream) -> int:
    """Nombre de bandeaux d'accueil : chacun porte le <h1> de la page, il n'en faut qu'un."""
    return sum(1 for child in iter_blocks(stream) if child.block_type == "hero")


def build_seo(page, request, profile) -> dict:
    """Métadonnées de <head> d'une page : description, image de partage, canonique, noindex.

    La description suit : champ « description » de l'onglet Promote, puis le résumé/l'intro de la
    page, puis la description du profil du site. L'image de partage suit : image de la page,
    puis celle du profil.
    """
    if page is None:
        return {}
    description = (
        page.search_description
        or getattr(page, "summary", "")
        or getattr(page, "intro", "")
        or profile.meta_description
    )
    image = getattr(page, "og_image", None) or profile.share_image
    share_image = None
    site = page.get_site()
    if image is not None and site is not None:
        # Même hôte que l'URL canonique (celui du site Wagtail), pas celui de la requête.
        rendition = image.get_rendition("fill-1200x630")
        share_image = {
            "url": urljoin(site.root_url, rendition.url),
            "width": rendition.width,
            "height": rendition.height,
            "alt": image.default_alt_text,
        }
    return {
        "description": Truncator(" ".join(description.split())).chars(300),
        "image": share_image,
        "canonical": page.get_full_url(request),
    }


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
