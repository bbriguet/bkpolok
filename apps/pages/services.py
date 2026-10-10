from urllib.parse import urljoin, urlsplit

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


def image_alt(image) -> str:
    """Texte alternatif d'une image : celui du bloc (ImageBlock), vide si elle est décorative,
    sinon celui de l'image."""
    if getattr(image, "decorative", False):
        return ""
    return getattr(image, "contextual_alt_text", None) or image.default_alt_text


def image_props(image, spec: str) -> dict:
    """Paramètres d'image des includes : {url, width, height, alt} d'une rendition."""
    rendition = image.get_rendition(spec)
    return {
        "url": rendition.url,
        "width": rendition.width,
        "height": rendition.height,
        "alt": image_alt(image),
    }


def offer_items(pages, request) -> list[dict]:
    """Éléments de `includes/offer_note.html` pour des pages de service."""
    return [
        {"title": page.title, "href": page.get_url(request) or "", "summary": page.summary}
        for page in pages
    ]


CONTAINER_BLOCKS = ("section", "more")


def iter_blocks(stream):
    """Blocs d'un StreamField, y compris ceux du contenu des sections et des « voir plus »."""
    for child in stream:
        yield child
        if child.block_type in CONTAINER_BLOCKS:
            yield from iter_blocks(child.value["content"])


def has_block(stream, block_type: str) -> bool:
    """Vrai si le StreamField contient un bloc de ce type, y compris dans une section."""
    return any(child.block_type == block_type for child in iter_blocks(stream))


def is_legal_page(page, profile) -> bool:
    """Vrai pour la page « Legal notice » ou « Privacy statement » choisie dans le profil."""
    return page.pk is not None and page.pk in (
        profile.legal_notice_page_id,
        profile.privacy_page_id,
    )


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


# (titre, slug, modèle, [(titre, slug) des ServicePage enfants], dans le menu)
SITE_TREE = [
    ("About", "about", "pages.StandardPage", [], True),
    (
        "Services",
        "services",
        "services.ServiceIndexPage",
        [
            ("Medical affairs consulting", "medical-affairs-consulting"),
            ("Patient programs & advocacy", "patient-programs-advocacy"),
            ("Coaching", "coaching"),
        ],
        True,
    ),
    ("Experience", "experience", "pages.StandardPage", [], True),
    ("Publications", "publications", "pages.StandardPage", [], True),
    ("Personal", "personal", "pages.StandardPage", [], True),
    ("Contact", "contact", "pages.ContactPage", [], True),
    # Liées depuis le pied de page (profil du site), pas depuis le menu.
    ("Legal notice (Impressum)", "legal-notice", "pages.StandardPage", [], False),
    ("Privacy statement", "privacy", "pages.StandardPage", [], False),
]


def create_site_pages(home: Page) -> list[Page]:
    """Crée sous l'accueil les pages du site, en brouillon (non publiées) et vides.

    Idempotent : une page dont le slug existe déjà sous son parent est laissée telle quelle.
    Retourne les pages créées. Les pages « dans le menu » y apparaissent une fois publiées ;
    les services enfants et les pages légales n'y apparaissent pas.
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

    for title, slug, model_label, children, in_menu in SITE_TREE:
        parent = ensure(home, title, slug, model_label, in_menu=in_menu)
        for child_title, child_slug in children:
            ensure(parent, child_title, child_slug, "services.ServicePage", in_menu=False)
    return created


def configure_site(site: Site, base_url: str, site_name: str) -> None:
    """Aligne le site Wagtail sur son URL publique (sitemap, liens canoniques, og:url)."""
    parts = urlsplit(base_url)
    if not parts.hostname:
        raise ValueError(f"URL sans nom d'hôte : {base_url!r}")
    site.hostname = parts.hostname
    site.port = parts.port or (443 if parts.scheme == "https" else 80)
    site.site_name = site_name
    site.save()


def publish_drafts(home: Page) -> list[Page]:
    """Publie la dernière révision de chaque page non publiée sous l'accueil.

    Idempotent : les pages déjà en ligne ne sont pas touchées. Retourne les pages publiées.
    """
    published: list[Page] = []
    for page in home.get_descendants().not_live().specific():
        revision = page.get_latest_revision() or page.save_revision()
        revision.publish()
        published.append(page)
    return published
