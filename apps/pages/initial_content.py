"""Chargement du contenu initial (`content.yaml`) : pages Wagtail, objets du profil et images.

Règles :
- idempotent : un objet est retrouvé par sa clé naturelle (une image par l'empreinte de son
  fichier), une page dont le corps est déjà identique n'est pas retouchée ;
- jamais d'écrasement : une valeur déjà remplie n'est pas remplacée, l'écart est signalé
  (sauf avec `update=True`) ; rien n'est supprimé, les objets absents du YAML sont signalés ;
- toute valeur contenant « TODO » est importée telle quelle, puis listée avec son emplacement ;
- aucune valeur n'est inventée : ce que le YAML ne fournit pas reste vide, un fichier image
  manquant est signalé dans `Report.not_imported` ;
- les pages restent en brouillon : c'est à l'éditeur de les publier.
"""

import calendar
import html
import json
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import yaml
from django.core.files.images import ImageFile
from django.db import models, transaction
from wagtail.blocks import StreamValue, StructValue
from wagtail.blocks.list_block import ListValue
from wagtail.images import get_image_model
from wagtail.models import Page, Site
from wagtail.utils.file import hash_filelike

from apps.profile.models import (
    Education,
    Experience,
    ExperienceAchievement,
    ExperienceImage,
    Language,
    MediaAppearance,
    Publication,
    SiteProfile,
)
from apps.profile.services import (
    DASH,
    MONTHS,
    PRESENT,
    format_org_line,
    format_period,
    languages_caption,
    publication_link_label,
    pubmed_article_url,
    timeline_label,
    working_languages_line,
)

from .icons import ICONS
from .models import HomePage
from .services import create_site_pages

TODO_RE = re.compile(r"\bTODO\b", re.IGNORECASE)
MONTH_NUMBERS = {name: number for number, name in enumerate(MONTHS, start=1)}

# Ancre d'une section du YAML -> slug de la page qui la porte (voir `SITE_TREE`).
SECTION_PAGES = {
    "about": "about",
    "services": "services",
    "experience": "experience",
    "publications": "publications",
    "personal": "personal",
    "contact": "contact",
    "legal-notice": "legal-notice",
    "privacy": "privacy",
}


class ContentError(Exception):
    """Valeur du YAML impossible à importer ; le message donne son emplacement."""


@dataclass
class Todo:
    path: str  # chemin dans le YAML, ex. « pages.home.hero.role »
    location: str  # où la valeur atterrit sur le site
    value: str


@dataclass
class Report:
    pages_created: list[str] = field(default_factory=list)
    pages_filled: list[str] = field(default_factory=list)
    pages_unchanged: list[str] = field(default_factory=list)
    created: Counter = field(default_factory=Counter)
    updated: Counter = field(default_factory=Counter)
    unchanged: Counter = field(default_factory=Counter)
    notes: list[str] = field(default_factory=list)
    not_imported: list[str] = field(default_factory=list)
    todos: list[Todo] = field(default_factory=list)
    todo_comments: list[tuple[int, str]] = field(default_factory=list)

    def models(self) -> list[str]:
        return sorted({*self.created, *self.updated, *self.unchanged})


def load_initial_content(path: Path, *, update: bool = False, assets: Path | None = None) -> Report:
    """Charge le fichier dans une transaction : la moindre erreur annule tout.

    `assets` : dossier des images citées par le YAML (défaut : `../assets` à côté du dossier
    du fichier, soit `_artifact/assets` pour `_artifact/design/content.yaml`).
    """
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    assets = Path(assets) if assets is not None else path.parent.parent / "assets"
    with transaction.atomic():
        loader = _Loader(data, update=update, assets=assets)
        loader.run()
    loader.report.todo_comments = [
        (number, line.strip())
        for number, line in enumerate(text.splitlines(), start=1)
        if "#" in line and TODO_RE.search(line.split("#", 1)[1])
    ]
    return loader.report


# ---------------------------------------------------------------- analyse des valeurs


def _walk(node, path: str = ""):
    """(chemin, texte) de chaque valeur texte du YAML."""
    if isinstance(node, dict):
        for key, value in node.items():
            yield from _walk(value, f"{path}.{key}" if path else str(key))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _walk(value, f"{path}[{index}]")
    elif isinstance(node, str):
        yield path, node


def _year(value, path: str) -> int:
    if isinstance(value, int):
        return value
    raise ContentError(
        f"{path}: « {value} » n'est pas une année, impossible de l'importer telle quelle."
    )


def _paragraph(text: str) -> str:
    """Texte brut -> HTML de texte riche (seuls &, < et > sont échappés)."""
    return f"<p>{html.escape(text, quote=False)}</p>"


def _unwrap(text: str, prefix: str, suffix: str, path: str) -> str:
    """Retire les guillemets ou le tiret que le gabarit ajoute lui-même."""
    if not (text.startswith(prefix) and text.endswith(suffix)):
        raise ContentError(
            f"{path}: « {text} » devrait commencer par {prefix!r} et finir par {suffix!r}."
        )
    return text[len(prefix) : len(text) - len(suffix)]


def split_org_line(line: str) -> tuple[str, str, str]:
    """« Organisation — lieu · orientation » -> (organisation, lieu, orientation).

    Inverse de `format_org_line` ; sans « — », le « · » sépare l'organisation de l'orientation.
    """
    head, separator, rest = line.partition(f" {DASH} ")
    if separator:
        scope, _, focus = rest.partition(" · ")
        return head, scope, focus
    organisation, _, focus = head.partition(" · ")
    return organisation, "", focus


def parse_period(text: str, path: str) -> tuple[date, date | None, str]:
    """« Dec 2022 — present », « Jan — Mar 2010 », « 2000 — 2006 » -> (début, fin, précision).

    Le début est le 1er du mois (ou le 1er janvier), la fin le dernier jour du mois (ou le
    31 décembre) : seule la période affichée compte. La conversion est vérifiée à l'aller-retour.
    """
    head, separator, tail = text.partition(f" {DASH} ")
    left, right = head.split(), tail.split()
    error = ContentError(
        f"{path}: période « {text} » illisible, impossible de l'importer en dates."
    )
    if not separator or not left or not right:
        raise error

    month_precision = any(token in MONTH_NUMBERS for token in left)
    precision = Experience.DatePrecision.MONTH if month_precision else Experience.DatePrecision.YEAR
    try:
        end_year_token = right[-1]
        start_month = MONTH_NUMBERS[left[0]] if month_precision else 1
        start_year = int(left[-1]) if left[-1].isdigit() else None
        if right == [PRESENT]:
            end = None
        else:
            end_year = int(end_year_token)
            end_month = MONTH_NUMBERS[right[0]] if month_precision else 12
            end = date(end_year, end_month, calendar.monthrange(end_year, end_month)[1])
            start_year = start_year or end_year
        if start_year is None:
            raise error
        start = date(start_year, start_month, 1)
    except (KeyError, ValueError) as exc:
        raise error from exc

    if format_period(start, end, precision) != text:
        raise error
    return start, end, precision


def parse_media_date(text: str, path: str) -> date | None:
    """« 19 May 2008 » -> date ; « — » (date inconnue) -> None."""
    if text == DASH:
        return None
    match = re.fullmatch(r"(\d{1,2}) ([A-Z][a-z]{2}) (\d{4})", text)
    try:
        if match is None or match.group(2) not in MONTH_NUMBERS:
            raise ValueError(text)
        return date(int(match.group(3)), MONTH_NUMBERS[match.group(2)], int(match.group(1)))
    except ValueError as exc:
        raise ContentError(
            f"{path}: date « {text} » illisible (attendu « 19 May 2008 » ou —)."
        ) from exc


def parse_language_levels(caption: str, path: str) -> dict[str, str]:
    """« Polish (mother tongue) · French & English (full professional) · … » -> {nom: niveau}."""
    levels = {label.lower(): value for value, label in Language.Level.choices}
    result: dict[str, str] = {}
    for group in caption.split(" · "):
        match = re.fullmatch(r"(.+) \((.+)\)", group)
        if match is None or match.group(2) not in levels:
            raise ContentError(f"{path}: niveau de langue illisible dans « {group} ».")
        for name in re.split(r", | & ", match.group(1)):
            result[name] = levels[match.group(2)]
    return result


def parse_position(text: str, path: str) -> tuple[float, float]:
    """« 50% 20% » (object-position CSS) -> (0.5, 0.2)."""
    match = re.fullmatch(r"(\d{1,3})% (\d{1,3})%", text or "50% 50%")
    if match is None:
        raise ContentError(f"{path}: position « {text} » illisible (attendu « 50% 20% »).")
    x, y = (int(part) / 100 for part in match.groups())
    if not (0 <= x <= 1 and 0 <= y <= 1):
        raise ContentError(f"{path}: position « {text} » hors de l'image.")
    return x, y


def _same(current, value) -> bool:
    """Égalité de deux valeurs de champ ; deux instances de modèle se comparent par leur pk
    (`Page` et `StandardPage` désignant la même page ne sont pas `==`)."""
    if isinstance(current, models.Model) and isinstance(value, models.Model):
        return current.pk == value.pk
    return current == value


def _strip_ids(node):
    """Retire les identifiants de blocs, aléatoires, pour comparer deux corps de page."""
    if isinstance(node, dict):
        return {key: _strip_ids(value) for key, value in node.items() if key != "id"}
    if isinstance(node, list):
        return [_strip_ids(value) for value in node]
    return node


def _force(value) -> None:
    """Convertit en profondeur les blocs encore « bruts » d'un StreamValue.

    Un corps relu en base ou construit depuis du JSON brut garde ses blocs imbriqués sous forme
    brute ; les deux côtés d'une comparaison doivent passer par la même normalisation.
    """
    if isinstance(value, StreamValue):
        for child in value:
            _force(child.value)
    elif isinstance(value, StructValue):
        for child in value.values():
            _force(child)
    elif isinstance(value, ListValue):
        for child in value:
            _force(child)


def _body_json(stream_value) -> str:
    _force(stream_value)
    return json.dumps(_strip_ids(stream_value.get_prep_value()), sort_keys=True)


# ---------------------------------------------------------------- chargeur


class _Loader:
    def __init__(self, data: dict, *, update: bool, assets: Path):
        self.data = data
        self.update = update
        self.assets = assets
        self.report = Report()
        self.places: dict[str, str] = {}
        self.images: dict[str, object] = {}  # nom de fichier -> image Wagtail
        self.publications: dict[str, Publication] = {}  # ancre du YAML (« pub-02 ») -> objet

    # -- suivi

    def place(self, path: str, location: str) -> None:
        """Déclare où atterrit tout ce qui se trouve sous `path` (pour localiser les TODO)."""
        self.places[path] = location

    def _location(self, path: str) -> str:
        for prefix in sorted(self.places, key=len, reverse=True):
            if path == prefix or path.startswith((f"{prefix}.", f"{prefix}[")):
                return self.places[prefix]
        return "non importé (aucune destination)"

    def _collect_todos(self) -> None:
        for path, value in _walk(self.data):
            if TODO_RE.search(value):
                self.report.todos.append(Todo(path, self._location(path), value))

    def _count(self, model, outcome: str) -> None:
        counter = {"created": self.report.created, "updated": self.report.updated}.get(
            outcome, self.report.unchanged
        )
        counter[str(model._meta.verbose_name).capitalize()] += 1

    def _sync(self, obj, values: dict, label: str) -> bool:
        """Remplit les champs vides, signale (ou, avec `update`, écrase) les champs différents."""
        changed = False
        for name, value in values.items():
            current = getattr(obj, name)
            if current in ("", None):
                if value not in ("", None):
                    setattr(obj, name, value)
                    changed = True
            elif not _same(current, value):
                if self.update:
                    setattr(obj, name, value)
                    changed = True
                else:
                    self.report.notes.append(
                        f"{label}: « {name} » est déjà rempli ({current!r}), le YAML dit "
                        f"{value!r} — laissé tel quel (--update pour écraser)."
                    )
        if changed:
            obj.save()
        return changed

    def _ensure(self, model, lookup: dict, values: dict, label: str):
        """get_or_create sur la clé naturelle `lookup`, puis complète un objet déjà présent."""
        obj, created = model.objects.get_or_create(**lookup, defaults=values)
        if created:
            self._count(model, "created")
        else:
            self._count(model, "updated" if self._sync(obj, values, label) else "unchanged")
        return obj, created

    def _expect(self, condition: bool, path: str) -> None:
        if not condition:
            raise ContentError(f"{path}: valeur incohérente avec le reste du fichier.")

    # -- déroulé

    def run(self) -> None:
        site = Site.objects.filter(is_default_site=True).first()
        if site is None:
            raise ContentError("Aucun site par défaut : lancez d'abord les migrations.")
        home = HomePage.objects.get()
        self.home = home
        self.report.pages_created = [self._relative(p, home) for p in create_site_pages(home)]
        self.pages = {p.slug: p.specific for p in home.get_children()}
        self.source = self.data["pages"]["home"]

        self._load_site(site)
        self._load_profile(site)
        self._load_languages()
        self._load_education()
        self._load_publications()
        self._load_experiences()
        self._load_media()
        self._build_pages()
        self._report_stale()
        self._check_derived_texts()
        self._collect_todos()

    @staticmethod
    def _relative(page: Page, home: Page) -> str:
        return "/" + page.url_path.removeprefix(home.url_path)

    # -- images

    def _image(self, spec: dict, path: str):
        """Image Wagtail du fichier `spec["file"]` (créée au premier passage, retrouvée ensuite
        par l'empreinte du fichier). None si le fichier manque : c'est signalé, pas une erreur."""
        name = spec["file"]
        if name in self.images:
            return self.images[name]
        file_path = self.assets / name
        if not file_path.is_file():
            self.report.not_imported.append(
                f"Image « {name} » ({path}, alt : « {spec.get('alt', '')} ») : fichier absent "
                f"de {self.assets}."
            )
            self.images[name] = None
            return None

        model = get_image_model()
        with file_path.open("rb") as handle:
            file_hash = hash_filelike(handle)
        image = model.objects.filter(file_hash=file_hash).first()
        values = {"title": file_path.stem, "description": spec.get("alt", "")}
        if image is None:
            with file_path.open("rb") as handle:
                image = model(file=ImageFile(handle, name=name), **values)
                image._set_image_file_metadata()
                self._set_focal_point(image, spec, path)
                image.save()
            self._count(model, "created")
        else:
            changed = self._sync(image, values, f"Image « {name} »")
            self._count(model, "updated" if changed else "unchanged")
        self.images[name] = image
        return image

    @staticmethod
    def _set_focal_point(image, spec: dict, path: str) -> None:
        """Le design recadre certaines vignettes (`object-position`) : un point focal Wagtail
        donne le même recadrage aux renditions « fill »."""
        if not spec.get("position"):
            return
        x, y = parse_position(spec["position"], f"{path}.position")
        size = max(1, min(image.width, image.height) // 10)
        image.focal_point_x = round(image.width * x)
        image.focal_point_y = round(image.height * y)
        image.focal_point_width = size
        image.focal_point_height = size

    def _image_value(self, spec: dict, path: str) -> dict | None:
        """Valeur brute d'un ImageBlock (image + texte alternatif propre à cet emploi)."""
        image = self._image(spec, path)
        if image is None:
            return None
        return {"image": image.pk, "decorative": False, "alt_text": spec["alt"]}

    # -- site, profil

    def _load_site(self, site: Site) -> None:
        self.place("site.title", "Site Wagtail › nom du site")
        if self._sync(site, {"site_name": self.data["site"]["title"]}, "Site Wagtail"):
            self._count(Site, "updated")
        else:
            self._count(Site, "unchanged")

    def _load_profile(self, site: Site) -> None:
        data, home = self.data["site"], self.source
        json_ld = data["json_ld"]
        contact = home["contact"]
        self._expect(
            json_ld["email"] == f"mailto:{contact['email']['label']}", "site.json_ld.email"
        )
        self._expect(contact["email"]["href"] == json_ld["email"], "pages.home.contact.email")
        self._expect(json_ld["same_as"][0] == contact["linkedin"]["href"], "site.json_ld.same_as")
        for path, location in (
            ("site.json_ld", "Profil du site (nom légal, poste, employeur, description)"),
            ("site.copyright", "Profil du site › mention de copyright (année et nom calculés)"),
            ("pages.home.nav.brand", "Profil du site › nom court"),
            ("pages.home.hero.h1", "Profil du site › prénom, nom et langue du nom"),
            ("pages.home.contact.email", "Profil du site › e-mail"),
            ("pages.home.contact.linkedin", "Profil du site › LinkedIn"),
            ("pages.home.contact.h2", "Profil du site › titre du pied de page"),
            ("pages.home.contact.lede", "Profil du site › chapeau du pied de page"),
            ("pages.home.contact.accessibility", "Profil du site › déclaration d'accessibilité"),
            ("pages.home.contact.legal_links", "Profil du site › pages légales"),
            ("pages.home.contact.languages_line", "Pied de page (calculé depuis les langues)"),
            ("pages.home.publications.pubmed_link", "Profil du site › lien PubMed"),
        ):
            self.place(path, location)

        legal_slugs = {}
        for index, link in enumerate(contact["legal_links"]):
            slug = SECTION_PAGES.get(link["href"].removeprefix("#"))
            if slug not in ("legal-notice", "privacy"):
                raise ContentError(
                    f"pages.home.contact.legal_links[{index}].href: ancre « {link['href']} » "
                    "sans page légale correspondante."
                )
            legal_slugs[slug] = self.pages[slug]

        values = {
            "first_name": home["hero"]["h1"]["first_name"],
            "last_name": home["hero"]["h1"]["last_name"],
            "name_language": home["hero"]["h1"].get("lang", ""),
            "short_name": home["nav"]["brand"],
            "legal_name": json_ld["name"],
            "job_title": json_ld["job_title"],
            "employer": json_ld["works_for"],
            "email": contact["email"]["label"],
            "linkedin_url": contact["linkedin"]["href"],
            "pubmed_url": home["publications"]["pubmed_link"]["href"],
            "publications_page": self.pages["publications"],
            "footer_heading": contact["h2"],
            "footer_lede": contact.get("lede", ""),
            "accessibility_statement": contact.get("accessibility", {}).get("text_html", ""),
            "legal_notice_page": legal_slugs.get("legal-notice"),
            "privacy_page": legal_slugs.get("privacy"),
            "copyright_notice": self._copyright_notice(data["copyright"], json_ld["name"]),
            "meta_description": json_ld["description"],
        }
        profile, created = SiteProfile.objects.get_or_create(site=site, defaults=values)
        if created:
            self._count(SiteProfile, "created")
        else:
            self._count(
                SiteProfile,
                "updated" if self._sync(profile, values, "Profil du site") else "unchanged",
            )

    @staticmethod
    def _copyright_notice(text: str, legal_name: str) -> str:
        """« © 2026 Nom. Phrase. » -> « Phrase. » (le pied de page calcule l'année et le nom)."""
        match = re.fullmatch(rf"© \d{{4}} {re.escape(legal_name)}\.\s*(.*)", text)
        if match is None:
            raise ContentError(
                f"site.copyright: « {text} » devrait commencer par « © <année> {legal_name}. »."
            )
        return match.group(1)

    # -- langues, formation

    def _load_languages(self) -> None:
        about = self.source["about"]
        caption_path = "pages.home.about.languages_caption"
        levels = parse_language_levels(about["languages_caption"], caption_path)
        english_names = list(levels)
        native_names = about["languages"]
        codes = self.data["site"]["json_ld"]["knows_language"]
        if not (len(english_names) == len(native_names) == len(codes)):
            raise ContentError(
                f"{caption_path}: le nombre de langues diffère entre la légende, la liste "
                "et json_ld."
            )

        self.place("pages.home.about.languages", "Langues › nom natif")
        self.place(caption_path, "Langues › niveaux")
        self.place("site.json_ld.knows_language", "Langues › code")
        for order, (code, native, english) in enumerate(
            zip(codes, native_names, english_names, strict=True), start=1
        ):
            self._ensure(
                Language,
                {"code": code},
                {
                    "native_name": native,
                    "english_name": english,
                    "level": levels[english],
                    "sort_order": order,
                },
                f"Langue {code}",
            )

    def _load_education(self) -> None:
        path = "pages.home.experience.more.education"
        self.place(path, "Formation")
        cards = self.source["experience"]["more"]["education"]["cards"]
        self.education = []
        for order, card in enumerate(cards, start=1):
            education, _ = self._ensure(
                Education,
                {"degree": card["degree"], "institution": card["institution"]},
                {
                    "description": card.get("description", ""),
                    "listed": card.get("listed", True),
                    "sort_order": order,
                },
                f"Formation « {card['degree']} »",
            )
            self.education.append(education)

    # -- publications

    def _load_publications(self) -> None:
        source = self.source["publications"]
        groups = (
            ("medical_affairs", Publication.Category.MEDICAL_AFFAIRS),
            ("research", Publication.Category.RESEARCH),
        )
        self.publication_objects = []
        for key, category in groups:
            for index, paper in enumerate(source[key]["papers"]):
                path = f"pages.home.publications.{key}.papers[{index}]"
                self.place(path, f"Publication « {paper['title'][:50]} »")
                number = paper.get("number", f"{index + 1:02d}")
                if not str(number).isdigit():
                    raise ContentError(f"{path}.number: « {number} » n'est pas un numéro.")
                pmid = str(paper["pmid"]) if paper.get("pmid") else ""
                year = _year(paper["year"], f"{path}.year")
                if paper.get("url") and paper["url"] != pubmed_article_url(pmid):
                    self.report.notes.append(
                        f"Publication « {paper['title'][:50]} » : l'URL du YAML n'est pas celle "
                        f"construite depuis le PMID ({pmid!r}) ; elle n'est pas importée."
                    )
                values = {
                    "category": category,
                    "title": paper["title"],
                    "authors": paper["authors"],
                    "journal": paper["journal"],
                    "year": year,
                    "pmid": pmid,
                    "note": paper.get("note", ""),
                    "sort_order": int(number),
                }
                lookup = {"pmid": pmid} if pmid else {"title": paper["title"], "year": year}
                publication, _ = self._ensure(
                    Publication, lookup, values, f"Publication « {paper['title'][:50]} »"
                )
                self.publication_objects.append(publication)
                if paper.get("id"):
                    self.publications[paper["id"]] = publication

    def _publication_for(self, href: str, path: str) -> Publication:
        publication = self.publications.get(href.removeprefix("#"))
        if not href.startswith("#") or publication is None:
            raise ContentError(f"{path}: « {href} » ne désigne aucune publication du fichier.")
        return publication

    # -- expériences

    def _experience_groups(self):
        experience = self.source["experience"]
        yield "pages.home.experience.groups", experience["groups"]
        yield "pages.home.experience.more.groups", experience["more"]["groups"]

    def _load_experiences(self) -> None:
        categories = {label.lower(): value for value, label in Experience.Category.choices}
        self.experience_objects = []
        for groups_path, groups in self._experience_groups():
            for g_index, group in enumerate(groups):
                group_path = f"{groups_path}[{g_index}]"
                key = group["label"].split(f" {DASH} ")[0].lower()
                if key not in categories:
                    raise ContentError(
                        f"{group_path}.label: catégorie « {key} » inconnue (industry ou research)."
                    )
                self.place(f"{group_path}.label", "Expérience › libellé du groupe (calculé)")
                for i_index, item in enumerate(group["items"]):
                    self._load_experience(item, categories[key], f"{group_path}.items[{i_index}]")

    def _load_experience(self, item: dict, category: str, path: str) -> None:
        self.place(path, f"Expérience « {item['role']} — {item['org'].split(f' {DASH} ')[0]} »")
        start, end, precision = parse_period(item["date"], f"{path}.date")
        organisation, scope, focus = split_org_line(item["org"])
        if (
            format_org_line(Experience(organisation=organisation, scope=scope, focus=focus))
            != item["org"]
        ):
            raise ContentError(f"{path}.org: « {item['org']} » ne se découpe pas sans perte.")

        paired = item.get("paired_images", [])
        values = {
            "organisation": organisation,
            "scope": scope,
            "focus": focus,
            "parallel_role": item.get("parallel_role", ""),
            "organisation_description": item.get("org_desc", ""),
            "summary": item.get("summary", ""),
            "end_date": end,
            "date_precision": precision,
            "pair_with_next": bool(paired),
        }
        lookup = {"category": category, "title": item["role"], "start_date": start}
        label = f"Expérience « {item['role']} »"
        experience, created = Experience.objects.get_or_create(
            **lookup, organisation=organisation, defaults=values
        )
        self.experience_objects.append(experience)
        achievements = [
            self._achievement(a, f"{path}.achievements[{i}]")
            for i, a in enumerate(item.get("achievements", []))
        ]
        images = [
            self._experience_image(spec, f"{path}.{key}")
            for key, specs in (
                ("image", [item["image"]] if item.get("image") else []),
                ("paired_images", paired),
            )
            for spec in specs
        ]
        images = [image for image in images if image is not None]
        if created:
            self._count(Experience, "created")
            self._set_children(experience, "achievements", achievements, ExperienceAchievement)
            self._set_children(experience, "images", images, ExperienceImage)
        else:
            changed = self._sync(experience, values, label)
            for relation, rows, model in (
                ("achievements", achievements, ExperienceAchievement),
                ("images", images, ExperienceImage),
            ):
                current = self._child_rows(experience, relation, model)
                if current == rows:
                    continue
                if self.update or not current:
                    changed |= self._set_children(experience, relation, rows, model)
                else:
                    self.report.notes.append(
                        f"{label}: les {model._meta.verbose_name_plural} diffèrent du YAML — "
                        "laissées telles quelles (--update pour les remplacer)."
                    )
            self._count(Experience, "updated" if changed else "unchanged")

    def _achievement(self, value, path: str) -> dict:
        if isinstance(value, str):
            return {"text": value, "publication": None, "link_text": ""}
        link = value["link"]
        if link["text"] not in value["text"]:
            raise ContentError(f"{path}.link.text: « {link['text']} » absent du texte.")
        return {
            "text": value["text"],
            "publication": self._publication_for(link["href"], f"{path}.link.href"),
            "link_text": link["text"],
        }

    def _experience_image(self, spec: dict, path: str) -> dict | None:
        image = self._image(spec, path)
        if image is None:
            return None
        link = spec.get("link") or {}
        row = {
            "image": image,
            "alt_text": spec["alt"],
            "caption": spec.get("caption", ""),
            "publication": None,
            "link_label": link.get("label", ""),
            "link_url": "",
        }
        href = link.get("href", "")
        if href.startswith("#"):
            row["publication"] = self._publication_for(href, f"{path}.link.href")
            # Libellé calculé depuis la publication quand il est identique.
            if row["link_label"] == publication_link_label(row["publication"]):
                row["link_label"] = ""
        else:
            row["link_url"] = href
        return row

    @staticmethod
    def _child_rows(experience: Experience, relation: str, model) -> list[dict]:
        fields = [
            f.name
            for f in model._meta.concrete_fields
            if f.name not in ("id", "sort_order", "experience")
        ]
        return [
            {name: getattr(child, name) for name in fields}
            for child in getattr(experience, relation).all()
        ]

    def _set_children(self, experience: Experience, relation: str, rows: list[dict], model) -> bool:
        """Remplace les réalisations ou les images d'une expérience par celles du YAML."""
        if self._child_rows(experience, relation, model) == rows:
            return False
        getattr(experience, relation).all().delete()
        for order, row in enumerate(rows):
            model.objects.create(experience=experience, sort_order=order, **row)
            self._count(model, "created")
        return True

    # -- médias

    def _load_media(self) -> None:
        media = self.source["publications"]["media"]
        kinds = {"television": MediaAppearance.Kind.TELEVISION, "press": MediaAppearance.Kind.PRESS}
        order = 0
        self.media_objects = []
        for key, kind in kinds.items():
            for index, item in enumerate(media[key]["items"]):
                path = f"pages.home.publications.media.{key}.items[{index}]"
                self.place(path, f"Apparition médiatique « {item['title'][:50]} »")
                order += 1
                values = {
                    "date": parse_media_date(item["date"], f"{path}.date"),
                    "url": item.get("url", ""),
                    "language": item.get("language", ""),
                    "title_language": item.get("title_language", ""),
                    "sort_order": order,
                }
                lookup = {"kind": kind, "outlet": item["source"], "title": item["title"]}
                obj, _ = self._ensure(MediaAppearance, lookup, values, f"Média « {item['title']} »")
                self.media_objects.append(obj)

    def _report_stale(self) -> None:
        """Objets présents en base mais absents du YAML : signalés, jamais supprimés."""
        for model, kept in (
            (Education, self.education),
            (Experience, self.experience_objects),
            (Publication, self.publication_objects),
            (MediaAppearance, self.media_objects),
        ):
            for obj in model.objects.exclude(pk__in=[o.pk for o in kept]):
                self.report.notes.append(
                    f"{str(model._meta.verbose_name).capitalize()} « {obj} » : en base mais "
                    "absent du YAML — laissé tel quel (à supprimer dans l'admin si besoin)."
                )

    # -- pages

    def _build_pages(self) -> None:
        self._anchors = SECTION_PAGES
        builders = {
            "home": (self.home, self._home_body),
            "about": (self.pages["about"], self._about_body),
            "services": (self.pages["services"], self._services_body),
            "experience": (self.pages["experience"], self._experience_body),
            "publications": (self.pages["publications"], self._publications_body),
            "personal": (self.pages["personal"], self._personal_body),
        }
        for key, (page, build) in builders.items():
            self.place(
                f"pages.home.{'hero' if key == 'home' else key}",
                f"Page « {page.title} » ({self._relative(page, self.home)})",
            )
            self._sync_page(page, {}, build())
        self.place("pages.home.pull_quote", f"Page « {self.home.title} » (/) › citation")
        for key in ("legal_notice", "privacy"):
            source = self.data["pages"][key]
            page = self.pages[SECTION_PAGES[source["id"]]]
            self.place(f"pages.{key}", f"Page « {page.title} » ({self._relative(page, self.home)})")
            self._sync_page(page, {"title": source["title"]}, self._legal_body(source))
        self._load_services()

    def _load_services(self) -> None:
        services = self.pages["services"]
        children = {p.title.casefold(): p.specific for p in services.get_children()}
        for index, item in enumerate(self.source["services"]["offers"]):
            page = children.get(item["title"].casefold())
            if page is None:
                raise ContentError(
                    f"pages.home.services.offers[{index}].title: "
                    f"aucune page de service « {item['title']} »."
                )
            self.place(
                f"pages.home.services.offers[{index}]",
                f"Page « {page.title} » ({self._relative(page, self.home)}) › titre et résumé",
            )
            self._sync_page(page, {"title": item["title"], "summary": item["text"]}, None)

    def _sync_page(self, page: Page, values: dict, body: list | None) -> None:
        label = f"Page {self._relative(page, self.home)}"
        changed = self._sync_fields(page, values, label)
        if body is not None:
            changed |= self._fill_body(page, body, label)
        where = self._relative(page, self.home)
        if changed:
            page.save()
            page.save_revision()
            self.report.pages_filled.append(where)
        else:
            self.report.pages_unchanged.append(where)

    def _sync_fields(self, page: Page, values: dict, label: str) -> bool:
        """Comme `_sync`, sans enregistrer : l'enregistrement se fait une fois pour la page."""
        changed = False
        for name, value in values.items():
            current = getattr(page, name)
            if current in ("", None):
                setattr(page, name, value)
                changed = True
            elif not _same(current, value):
                if self.update:
                    setattr(page, name, value)
                    changed = True
                else:
                    self.report.notes.append(
                        f"{label}: « {name} » est déjà rempli, le YAML dit {value!r} "
                        "— laissé tel quel."
                    )
        return changed

    def _fill_body(self, page: Page, raw: list, label: str) -> bool:
        new = page._meta.get_field("body").to_python(raw)
        _force(new)
        if not page.body:
            page.body = new
            return True
        if _body_json(page.body) == _body_json(new):
            return False
        if self.update:
            page.body = new
            return True
        self.report.notes.append(
            f"{label}: le corps est déjà rempli et diffère du YAML — laissé tel quel "
            "(--update pour le remplacer)."
        )
        return False

    # -- corps des pages (valeurs brutes de StreamField)

    def _page_id(self, slug: str) -> int:
        return self.pages[slug].pk

    def _link(self, href: str, path: str) -> tuple[int | None, str]:
        """(page, url) d'un lien du YAML : une ancre de section devient la page qui la porte."""
        if href.startswith("#"):
            slug = self._anchors.get(href[1:])
            if slug is None:
                raise ContentError(f"{path}.href: ancre « {href} » sans page correspondante.")
            return self._page_id(slug), ""
        return None, href

    def _button(self, button: dict, path: str) -> dict:
        page, url = self._link(button["href"], path)
        return {"label": button["label"], "page": page, "url": url, "variant": button["variant"]}

    @staticmethod
    def _section(anchor: str, background: str, content: list) -> dict:
        return {
            "type": "section",
            "value": {"anchor": anchor, "background": background, "content": content},
        }

    @staticmethod
    def _more(summary: str, content: list) -> dict:
        return {"type": "more", "value": {"summary": summary, "content": content}}

    @staticmethod
    def _heading(
        eyebrow: str, text: str, *, level="h2", lede="", pills=(), image=None, figure=None
    ) -> dict:
        return {
            "type": "heading",
            "value": {
                "eyebrow": eyebrow,
                "text": text,
                "level": level,
                "lede": lede,
                "pills": list(pills),
                "image": image,
                "figure": figure or {"images": [], "title": "", "caption": ""},
            },
        }

    def _subhead(self, text: str) -> dict:
        return self._heading("", text, level="subhead")

    def _cards(self, cards: list, variant: str, heading_level: str, path: str) -> dict:
        for index, card in enumerate(cards):
            if card.get("icon") and card["icon"] not in ICONS:
                raise ContentError(f"{path}[{index}].icon: icône « {card['icon']} » inconnue.")
        return {
            "type": "cards",
            "value": {
                "variant": variant,
                "heading_level": heading_level,
                "cards": [
                    {
                        "icon": card.get("icon", ""),
                        "title": card["title"],
                        "text": card["text"],
                        "wide": bool(card.get("wide")),
                    }
                    for card in cards
                ],
            },
        }

    def _home_body(self) -> list:
        hero, quote = self.source["hero"], self.source["pull_quote"]
        buttons = [
            self._button(button, f"pages.home.hero.buttons[{i}]")
            for i, button in enumerate(hero["buttons"])
        ]
        return [
            {
                "type": "hero",
                "value": {
                    "eyebrow": hero["eyebrow"],
                    "role": hero["role"],
                    "badge_text": hero.get("status_badge", ""),
                    "thesis": hero["thesis"],
                    "now": hero.get("now", ""),
                    "buttons": buttons,
                    "image": self._image_value(hero["image"], "pages.home.hero.image"),
                },
            },
            {
                "type": "quote",
                "value": {
                    "text": _unwrap(quote["text"], "“", "”", "pages.home.pull_quote.text"),
                    "author": _unwrap(quote["cite"], "— ", "", "pages.home.pull_quote.cite"),
                    "note": quote.get("note", ""),
                },
            },
        ]

    def _about_body(self) -> list:
        about = self.source["about"]
        figure = about.get("figure") or {}
        images = [
            self._image_value(spec, f"pages.home.about.figure.images[{i}]")
            for i, spec in enumerate(figure.get("images", []))
        ]
        content = [
            self._heading(
                about["eyebrow"],
                about["h2"],
                figure={
                    "images": [image for image in images if image],
                    "title": figure.get("title", ""),
                    "caption": figure.get("caption", ""),
                },
            )
        ]
        content += [
            {"type": "paragraph", "value": _paragraph(text)} for text in about["paragraphs"]
        ]
        content.append({"type": "languages", "value": None})
        return [self._section(about["id"], "default", content)]

    def _services_body(self) -> list:
        services = self.source["services"]
        bring = services["what_i_bring"]
        cta = services["cta"]
        button = self._button(cta["button"], "pages.home.services.cta.button")
        content = [
            self._heading(services["eyebrow"], services["h2"], lede=services["lede"]),
            {
                "type": "offers",
                "value": {"lead": "", "index_page": self._page_id("services")},
            },
            self._subhead(bring["h3"]),
            {
                "type": "tag_line",
                "value": {
                    "label": bring.get("therapeutic_areas_label", ""),
                    "items": bring["therapeutic_areas"],
                },
            },
            self._cards(bring["cards"], "service", "h4", "pages.home.services.what_i_bring.cards"),
            {
                "type": "call_to_action",
                "value": {
                    "title": cta["text"],
                    "text": "",
                    "button_label": button["label"],
                    "page": button["page"],
                    "url": button["url"],
                    "variant": button["variant"],
                },
            },
        ]
        return [self._section(services["id"], "tint", content)]

    def _experience_body(self) -> list:
        experience = self.source["experience"]
        more = experience["more"]
        education = more["education"]

        def timelines(groups):
            return [
                {
                    "type": "timeline",
                    "value": {"category": group["label"].split(f" {DASH} ")[0].lower()},
                }
                for group in groups
            ]

        content = [self._heading(experience["eyebrow"], experience["h2"])]
        content += timelines(experience["groups"])
        content.append(
            self._more(
                more["summary"],
                timelines(more["groups"])
                + [
                    {
                        "type": "education",
                        "value": {"eyebrow": education["eyebrow"], "heading": education["h3"]},
                    }
                ],
            )
        )
        return [self._section(experience["id"], "default", content)]

    def _publications_body(self) -> list:
        publications = self.source["publications"]
        medical, research = publications["medical_affairs"], publications["research"]
        media = publications["media"]
        television, press = media["television"], media["press"]
        content = [
            self._heading(publications["eyebrow"], publications["h2"], lede=publications["lede"]),
            self._subhead(medical["h3"]),
            {
                "type": "publications",
                "value": {
                    "category": Publication.Category.MEDICAL_AFFAIRS,
                    "visible": 0,
                    "more_label": "",
                    "show_pubmed_link": False,
                },
            },
            self._subhead(research["h3"]),
            {
                "type": "publications",
                "value": {
                    "category": Publication.Category.RESEARCH,
                    "visible": research.get("visible", 0),
                    "more_label": research.get("more_label", ""),
                    "show_pubmed_link": True,
                },
            },
            self._more(
                media["summary"],
                [
                    {
                        "type": "media",
                        "value": {
                            "kind": MediaAppearance.Kind.TELEVISION,
                            "eyebrow": television.get("eyebrow", ""),
                            "heading": television["h3"],
                            "note": television.get("note_html", ""),
                        },
                    },
                    {
                        "type": "media",
                        "value": {
                            "kind": MediaAppearance.Kind.PRESS,
                            "eyebrow": press.get("eyebrow", ""),
                            "heading": press["h3"],
                            "note": press.get("note_html", ""),
                        },
                    },
                ],
            ),
        ]
        return [self._section(publications["id"], "tint", content)]

    def _personal_body(self) -> list:
        personal = self.source["personal"]
        gallery = personal["gallery"]
        images = [
            self._image_value(spec, f"pages.home.personal.gallery.images[{i}]")
            for i, spec in enumerate(gallery["images"])
        ]
        notes = [
            {"title": aside.get("title", ""), "icon": aside.get("icon", ""), "text": aside["text"]}
            for aside in personal["asides"]
        ]
        content = [
            self._heading(
                personal["eyebrow"],
                personal["h2"],
                lede=personal["lede"],
                image=self._image_value(personal["image"], "pages.home.personal.image"),
            ),
            self._cards(personal["cards"], "off_duty", "h3", "pages.home.personal.cards"),
            {
                "type": "gallery",
                "value": {
                    "heading": gallery.get("h3", ""),
                    "images": [image for image in images if image],
                    "note": gallery.get("note", ""),
                    "protect": True,
                },
            },
            {"type": "aside_notes", "value": {"notes": notes}},
        ]
        return [self._section(personal["id"], "default", content)]

    @staticmethod
    def _legal_body(source: dict) -> list:
        """Texte juridique en un bloc de texte riche ; les titres de section deviennent des h2
        (la page porte son propre h1)."""
        parts = [source["intro_html"]] if source.get("intro_html") else []
        for section in source["sections"]:
            parts.append(f"<h2>{html.escape(section['h3'], quote=False)}</h2>")
            parts += section["paragraphs_html"]
        return [{"type": "paragraph", "value": "".join(parts)}]

    # -- vérifications de cohérence

    def _check_derived_texts(self) -> None:
        """Textes que le site calcule au lieu de les stocker : signale les écarts avec le YAML."""
        for _, groups in self._experience_groups():
            for group in groups:
                category = group["label"].split(f" {DASH} ")[0].lower()
                computed = timeline_label(category)
                if computed != group["label"]:
                    self.report.notes.append(
                        f"Libellé de groupe calculé « {computed} » ≠ YAML « {group['label']} »."
                    )
        institutions = list(dict.fromkeys(e.institution for e in Education.objects.all()))
        alumni = self.data["site"]["json_ld"]["alumni_of"]
        if institutions != alumni:
            self.report.notes.append(
                f"Données structurées : alumniOf calculé {institutions} ≠ YAML {alumni} "
                "(calculé depuis les formations)."
            )
        caption = languages_caption()
        yaml_caption = self.source["about"]["languages_caption"]
        if caption != yaml_caption:
            self.report.notes.append(
                f"Légende des langues calculée « {caption} » ≠ YAML « {yaml_caption} » "
                "(le site regroupe les niveaux identiques consécutifs)."
            )
        line = working_languages_line()
        yaml_line = self.source["contact"].get("languages_line", "")
        if yaml_line and line != yaml_line:
            self.report.notes.append(
                f"Pied de page : langues calculées « {line} » ≠ YAML « {yaml_line} »."
            )
