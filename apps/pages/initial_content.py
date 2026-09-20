"""Chargement du contenu initial (`content.yaml`) : pages Wagtail et objets du profil.

Règles :
- idempotent : un objet est retrouvé par sa clé naturelle, une page dont le corps est déjà
  identique n'est pas retouchée ;
- jamais d'écrasement : une valeur déjà remplie n'est pas remplacée, l'écart est signalé
  (sauf avec `update=True`) ;
- toute valeur contenant « TODO » est importée telle quelle, puis listée avec son emplacement ;
- aucune valeur n'est inventée : ce que le YAML ne fournit pas (images, icônes) reste vide et
  est signalé dans `Report.not_imported` ;
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
from django.db import models, transaction
from wagtail.blocks import StreamValue, StructValue
from wagtail.blocks.list_block import ListValue
from wagtail.models import Page, Site

from apps.profile.models import (
    Education,
    Experience,
    ExperienceAchievement,
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
    pubmed_article_url,
    timeline_label,
)

from .models import HomePage
from .services import create_site_pages

TODO_RE = re.compile(r"\bTODO\b", re.IGNORECASE)
MONTH_NUMBERS = {name: number for number, name in enumerate(MONTHS, start=1)}

# Section du YAML -> slug de la page qui la porte (voir `SITE_TREE`).
SECTION_PAGES = {
    "about": "about",
    "expertise": "expertise",
    "experience": "experience",
    "publications": "publications",
    "personal": "personal",
    "contact": "contact",
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


def load_initial_content(path: Path, *, update: bool = False) -> Report:
    """Charge le fichier dans une transaction : la moindre erreur annule tout."""
    text = Path(path).read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    with transaction.atomic():
        loader = _Loader(data, update=update)
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
    """« DEC 2022 — PRESENT », « JAN — MAR 2010 », « 2000 — 2006 » -> (début, fin, précision).

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
    """« 19.05.2008 » -> date ; « — » (date inconnue) -> None."""
    if text == DASH:
        return None
    match = re.fullmatch(r"(\d{2})\.(\d{2})\.(\d{4})", text)
    try:
        if match is None:
            raise ValueError(text)
        day, month, year = (int(part) for part in match.groups())
        return date(year, month, day)
    except ValueError as exc:
        raise ContentError(f"{path}: date « {text} » illisible (attendu JJ.MM.AAAA ou —).") from exc


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
    def __init__(self, data: dict, *, update: bool):
        self.data = data
        self.update = update
        self.report = Report()
        self.places: dict[str, str] = {}

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
        self._load_experiences()
        self._load_publications()
        self._load_media()
        self._build_pages()
        self._check_derived_texts()
        self._collect_todos()

    @staticmethod
    def _relative(page: Page, home: Page) -> str:
        return "/" + page.url_path.removeprefix(home.url_path)

    # -- site, profil

    def _load_site(self, site: Site) -> None:
        self.place("site.title", "Site Wagtail › nom du site")
        self._sync_site(site)

    def _sync_site(self, site: Site) -> None:
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
            ("site.copyright", "Pied de page (année et nom légal calculés)"),
            ("pages.home.nav.brand", "Profil du site › nom court"),
            ("pages.home.hero.h1", "Profil du site › prénom et nom"),
            ("pages.home.contact.email", "Profil du site › e-mail"),
            ("pages.home.contact.linkedin", "Profil du site › LinkedIn"),
            ("pages.home.contact.h2", "Profil du site › titre du pied de page"),
            ("pages.home.contact.language_codes", "Langues (codes du pied de page)"),
            ("pages.home.publications.pubmed_link", "Profil du site › lien PubMed"),
        ):
            self.place(path, location)

        values = {
            "first_name": home["hero"]["h1"]["first_name"],
            "last_name": home["hero"]["h1"]["last_name"],
            "short_name": home["nav"]["brand"],
            "legal_name": json_ld["name"],
            "job_title": json_ld["job_title"],
            "employer": json_ld["works_for"],
            "email": contact["email"]["label"],
            "linkedin_url": contact["linkedin"]["href"],
            "pubmed_url": home["publications"]["pubmed_link"]["href"],
            "publications_page": self.pages["publications"],
            "footer_heading": contact["h2"],
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

    def _expect(self, condition: bool, path: str) -> None:
        if not condition:
            raise ContentError(f"{path}: valeur incohérente avec le reste du fichier.")

    # -- langues, formation

    def _load_languages(self) -> None:
        about = self.source["about"]
        caption_path = "pages.home.about.languages_caption"
        levels = parse_language_levels(about["languages_caption"], caption_path)
        english_names = list(levels)
        native_names = about["languages"]
        codes = self.data["site"]["json_ld"]["knows_language"]
        footer_codes = self.source["contact"]["language_codes"]
        if not (len(english_names) == len(native_names) == len(codes)):
            raise ContentError(
                f"{caption_path}: le nombre de langues diffère entre la légende, la liste "
                "et json_ld."
            )
        if [code.upper() for code in codes] != footer_codes:
            raise ContentError(
                "pages.home.contact.language_codes: différent de site.json_ld.knows_language."
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
        self.place("pages.home.experience.education", "Formation")
        for order, card in enumerate(self.source["experience"]["education"]["cards"], start=1):
            self._ensure(
                Education,
                {"degree": card["degree"], "institution": card["institution"]},
                {"sort_order": order},
                f"Formation « {card['degree']} »",
            )

    # -- expériences

    def _load_experiences(self) -> None:
        categories = {label.lower(): value for value, label in Experience.Category.choices}
        self.experiences = []
        for g_index, group in enumerate(self.source["experience"]["groups"]):
            group_path = f"pages.home.experience.groups[{g_index}]"
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

        values = {
            "organisation": organisation,
            "scope": scope,
            "focus": focus,
            "organisation_description": item.get("org_desc", ""),
            "summary": item.get("summary", ""),
            "end_date": end,
            "date_precision": precision,
        }
        lookup = {"category": category, "title": item["role"], "start_date": start}
        label = f"Expérience « {item['role']} »"
        experience, created = Experience.objects.get_or_create(
            **lookup, organisation=organisation, defaults=values
        )
        achievements = item.get("achievements", [])
        if created:
            self._count(Experience, "created")
            self._set_achievements(experience, achievements)
        else:
            changed = self._sync(experience, values, label)
            if self.update:
                changed |= self._set_achievements(experience, achievements)
            self._count(Experience, "updated" if changed else "unchanged")

        for image in [item.get("image"), *item.get("paired_images", [])]:
            if image:
                self.report.not_imported.append(
                    f"Image « {image['caption']} » de l'expérience « {item['role']} » "
                    f"(alt : « {image['alt']} ») : aucun fichier image fourni."
                )

    def _set_achievements(self, experience: Experience, texts: list[str]) -> bool:
        """Crée les réalisations d'une expérience neuve ; avec `update`, remplace la liste."""
        current = [a.text for a in experience.achievements.all()]
        if current == texts:
            return False
        experience.achievements.all().delete()
        for order, text in enumerate(texts):
            ExperienceAchievement.objects.create(experience=experience, text=text, sort_order=order)
            self._count(ExperienceAchievement, "created")
        return True

    # -- publications, médias

    def _load_publications(self) -> None:
        for index, paper in enumerate(self.source["publications"]["papers"]):
            path = f"pages.home.publications.papers[{index}]"
            self.place(path, f"Publication n° {paper['number']} « {paper['title'][:50]} »")
            if not str(paper["number"]).isdigit():
                raise ContentError(f"{path}.number: « {paper['number']} » n'est pas un numéro.")
            pmid = str(paper["pmid"]) if paper.get("pmid") else ""
            year = _year(paper["year"], f"{path}.year")
            if paper.get("url") and paper["url"] != pubmed_article_url(pmid):
                self.report.notes.append(
                    f"Publication n° {paper['number']}: l'URL du YAML n'est pas celle construite "
                    f"depuis le PMID ({pmid!r}) ; elle n'est pas importée."
                )
            values = {
                "title": paper["title"],
                "authors": paper["authors"],
                "journal": paper["journal"],
                "year": year,
                "pmid": pmid,
                "sort_order": int(paper["number"]),
            }
            lookup = {"pmid": pmid} if pmid else {"title": paper["title"], "year": year}
            self._ensure(Publication, lookup, values, f"Publication n° {paper['number']}")

    def _load_media(self) -> None:
        media = self.source["publications"]["media"]
        kinds = {"television": MediaAppearance.Kind.TELEVISION, "press": MediaAppearance.Kind.PRESS}
        order = 0
        for key, kind in kinds.items():
            for index, item in enumerate(media[key]["items"]):
                path = f"pages.home.publications.media.{key}.items[{index}]"
                self.place(path, f"Apparition médiatique « {item['title'][:50]} »")
                order += 1
                values = {
                    "date": parse_media_date(item["date"], f"{path}.date"),
                    "url": item.get("url", ""),
                    "sort_order": order,
                }
                lookup = {"kind": kind, "outlet": item["source"], "title": item["title"]}
                self._ensure(MediaAppearance, lookup, values, f"Média « {item['title']} »")

    # -- pages

    def _build_pages(self) -> None:
        anchors = {self.source[key]["id"]: slug for key, slug in SECTION_PAGES.items()}
        self._anchors = anchors
        builders = {
            "home": (self.home, self._home_body, {}),
            "about": (self.pages["about"], self._about_body, {}),
            "expertise": (self.pages["expertise"], self._expertise_body, {}),
            "experience": (self.pages["experience"], self._experience_body, {}),
            "publications": (self.pages["publications"], self._publications_body, {}),
            "personal": (self.pages["personal"], self._personal_body, {}),
        }
        for slug, (page, build, values) in builders.items():
            self.place(
                f"pages.home.{'hero' if slug == 'home' else slug}",
                f"Page « {page.title} » ({self._relative(page, self.home)})",
            )
            self._sync_page(page, values, build())
        self.place("pages.home.pull_quote", f"Page « {self.home.title} » (/) › citation")
        self.place("pages.home.contact.copyright", "Pied de page (année et nom légal calculés)")
        self._load_services()

    def _load_services(self) -> None:
        expertise = self.pages["expertise"]
        offers = self.source["expertise"]["offer"]
        children = {p.title: p.specific for p in expertise.get_children()}
        for index, item in enumerate(offers["items"]):
            page = children.get(item["title"])
            if page is None:
                raise ContentError(
                    f"pages.home.expertise.offer.items[{index}].title: "
                    f"aucune page de service « {item['title']} »."
                )
            self.place(
                f"pages.home.expertise.offer.items[{index}]",
                f"Page « {page.title} » ({self._relative(page, self.home)}) › résumé",
            )
            self._sync_page(page, {"summary": item["text"]}, None)

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

    def _button(self, button: dict, path: str) -> dict:
        href = button["href"]
        if href.startswith("#"):
            slug = self._anchors.get(href[1:])
            if slug is None:
                raise ContentError(f"{path}.href: ancre « {href} » sans page correspondante.")
            return {
                "label": button["label"],
                "page": self._page_id(slug),
                "url": "",
                "variant": button["variant"],
            }
        return {"label": button["label"], "page": None, "url": href, "variant": button["variant"]}

    @staticmethod
    def _section(anchor: str, background: str, content: list) -> dict:
        return {
            "type": "section",
            "value": {"anchor": anchor, "background": background, "content": content},
        }

    @staticmethod
    def _heading(eyebrow: str, text: str, *, level="h2", lede="", pills=()) -> dict:
        return {
            "type": "heading",
            "value": {
                "eyebrow": eyebrow,
                "text": text,
                "level": level,
                "lede": lede,
                "pills": list(pills),
            },
        }

    def _home_body(self) -> list:
        hero, quote = self.source["hero"], self.source["pull_quote"]
        buttons = [
            self._button(button, f"pages.home.hero.buttons[{i}]")
            for i, button in enumerate(hero["buttons"])
        ]
        self.report.not_imported.append(
            f"Portrait du bandeau (alt : « {hero['image_alt']} ») : aucun fichier image fourni."
        )
        return [
            {
                "type": "hero",
                "value": {
                    "eyebrow": hero["eyebrow"],
                    "role": hero["role"],
                    "badge_text": hero["status_badge"],
                    "thesis": hero["thesis"],
                    "buttons": buttons,
                },
            },
            {
                "type": "quote",
                "value": {
                    "text": _unwrap(quote["text"], "“", "”", "pages.home.pull_quote.text"),
                    "author": _unwrap(quote["cite"], "— ", "", "pages.home.pull_quote.cite"),
                },
            },
        ]

    def _about_body(self) -> list:
        about = self.source["about"]
        content = [self._heading(about["eyebrow"], about["h2"])]
        content += [
            {"type": "paragraph", "value": _paragraph(text)} for text in about["paragraphs"]
        ]
        content.append({"type": "languages", "value": None})
        return [self._section(about["id"], "default", content)]

    def _expertise_body(self) -> list:
        expertise = self.source["expertise"]
        cards = [
            {"icon": "", "title": service["title"], "text": service["text"], "wide": False}
            for service in expertise["services"]
        ]
        self.report.not_imported.append(
            f"Icônes des {len(cards)} cartes d'expertise : le YAML n'en donne pas, "
            "champ laissé vide."
        )
        content = [
            self._heading(
                expertise["eyebrow"],
                expertise["h2"],
                lede=expertise["lede"],
                pills=expertise["therapeutic_areas"],
            ),
            {"type": "cards", "value": {"variant": "service", "cards": cards}},
            {
                "type": "offers",
                "value": {
                    "lead": expertise["offer"]["lead"],
                    "index_page": self._page_id("expertise"),
                },
            },
        ]
        return [self._section(expertise["id"], "tint", content)]

    def _experience_body(self) -> list:
        experience = self.source["experience"]
        education = experience["education"]
        content = [self._heading(experience["eyebrow"], experience["h2"])]
        for group in experience["groups"]:
            category = group["label"].split(f" {DASH} ")[0].lower()
            content.append({"type": "timeline", "value": {"category": category}})
        content.append(
            {
                "type": "education",
                "value": {"eyebrow": education["eyebrow"], "heading": education["h3"]},
            }
        )
        return [self._section(experience["id"], "default", content)]

    def _publications_body(self) -> list:
        publications = self.source["publications"]
        media = publications["media"]
        television, press = media["television"], media["press"]
        tv_note = television["note"]
        note_link = tv_note["link"]
        tv_html = (
            f"<p>{html.escape(tv_note['text'], quote=False)} "
            f'<a href="{html.escape(note_link["href"])}">'
            f"{html.escape(note_link['label'], quote=False)}</a></p>"
        )
        content = [
            self._heading(publications["eyebrow"], publications["h2"], lede=publications["lede"]),
            {"type": "publications", "value": None},
            {
                "type": "media",
                "value": {
                    "kind": MediaAppearance.Kind.TELEVISION,
                    "eyebrow": television["eyebrow"],
                    "heading": television["h3"],
                    "note": tv_html,
                },
            },
            {
                "type": "media",
                "value": {
                    "kind": MediaAppearance.Kind.PRESS,
                    "eyebrow": press.get("eyebrow", ""),
                    "heading": press["h3"],
                    "note": _paragraph(press["note"]["text"]),
                },
            },
        ]
        return [self._section(publications["id"], "tint", content)]

    def _personal_body(self) -> list:
        personal = self.source["personal"]
        cards = [
            {"icon": "", "title": c["title"], "text": c["text"], "wide": bool(c.get("wide"))}
            for c in personal["cards"]
        ]
        notes = [{"icon": "", "text": text} for text in personal["asides"]]
        self.report.not_imported += [
            f"Photo de la section « {personal['eyebrow']} » (alt : « {personal['image_alt']} ») : "
            "aucun fichier image fourni.",
            f"Icônes des {len(cards)} cartes « {personal['eyebrow']} » et des {len(notes)} notes : "
            "le YAML n'en donne pas, champ laissé vide.",
        ]
        content = [
            self._heading(personal["eyebrow"], personal["h2"], lede=personal["lede"]),
            {"type": "cards", "value": {"variant": "off_duty", "cards": cards}},
            {"type": "aside_notes", "value": {"notes": notes}},
        ]
        return [self._section(personal["id"], "default", content)]

    # -- vérifications de cohérence

    def _check_derived_texts(self) -> None:
        """Textes que le site calcule au lieu de les stocker : signale les écarts avec le YAML."""
        experience = self.source["experience"]
        for group in experience["groups"]:
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
