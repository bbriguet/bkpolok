import json
import unicodedata
from dataclasses import dataclass, field
from datetime import date

from django.utils.translation import get_language_info

from .models import (
    Education,
    Experience,
    ExperienceAchievement,
    Language,
    MediaAppearance,
    Publication,
    SiteProfile,
)

MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
PRESENT = "present"
DASH = "—"


# ---------------------------------------------------------------- profil du site


def get_site_profile(request) -> SiteProfile:
    """Profil du site courant (créé vide au premier accès, comme tout réglage de site Wagtail)."""
    return SiteProfile.for_request(request)


def display_url(url: str) -> str:
    """« https://www.linkedin.com/in/x » -> « linkedin.com/in/x »."""
    for prefix in ("https://", "http://"):
        url = url.removeprefix(prefix)
    return url.removeprefix("www.").rstrip("/")


def build_footer(profile: SiteProfile, request) -> dict:
    """Paramètres de includes/footer.html : coordonnées, langues, liens légaux, copyright."""
    legal_links = []
    for page in (profile.legal_notice_page, profile.privacy_page):
        url = page.get_url(request) if page is not None and page.live else None
        if url:
            legal_links.append({"label": page.title, "href": url})
    return {
        "heading": profile.footer_heading,
        "lede": profile.footer_lede,
        "email": profile.email,
        "linkedin_url": profile.linkedin_url,
        "linkedin_label": display_url(profile.linkedin_url),
        "languages_line": working_languages_line(),
        "accessibility": profile.accessibility_statement,
        "legal_links": legal_links,
        "notice": profile.copyright_notice,
    }


def list_languages() -> list[Language]:
    return list(Language.objects.all())


def language_codes() -> list[str]:
    return [language.code.upper() for language in list_languages()]


def languages_caption(languages: list[Language] | None = None) -> str:
    """« Polish (mother tongue) · French, English & German (full professional) · … ».

    Les langues consécutives de même niveau sont regroupées.
    """
    languages = list_languages() if languages is None else languages
    groups: list[tuple[str, list[str]]] = []
    for language in languages:
        label = Language.Level(language.level).label.lower()
        if groups and groups[-1][0] == label:
            groups[-1][1].append(language.english_name)
        else:
            groups.append((label, [language.english_name]))
    return " · ".join(f"{_join_names(names)} ({label})" for label, names in groups)


def _join_names(names: list[str], conjunction: str = "&") -> str:
    if len(names) <= 2:
        return f" {conjunction} ".join(names)
    return f"{', '.join(names[:-1])} {conjunction} {names[-1]}"


def working_languages_line(languages: list[Language] | None = None) -> str:
    """« Working in Polish, French, English, German and Italian » (pied de page)."""
    languages = list_languages() if languages is None else languages
    if not languages:
        return ""
    return f"Working in {_join_names([language.english_name for language in languages], 'and')}"


def language_name(code: str) -> str:
    """Nom anglais d'une langue d'après son code ISO 639-1 (« fr » -> « French »)."""
    if not code:
        return ""
    try:
        return get_language_info(code)["name"]
    except KeyError:
        return code


def _ascii_fold(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()


def build_person_jsonld(profile: SiteProfile) -> dict:
    """Données structurées schema.org/Person, dérivées du profil, des langues et de la formation."""
    data: dict = {"@context": "https://schema.org", "@type": "Person"}
    name = profile.legal_name or f"{profile.first_name} {profile.last_name}".strip()
    if name:
        data["name"] = name
    display_name = profile.display_name
    alternate = _ascii_fold(display_name)
    if alternate and alternate != name:
        data["alternateName"] = alternate
    if profile.job_title:
        data["jobTitle"] = profile.job_title
    if profile.employer:
        data["worksFor"] = {"@type": "Organization", "name": profile.employer}
    if profile.email:
        data["email"] = f"mailto:{profile.email}"
    if profile.linkedin_url:
        data["sameAs"] = [profile.linkedin_url]
    codes = [language.code for language in list_languages()]
    if codes:
        data["knowsLanguage"] = codes
    institutions = list(dict.fromkeys(e.institution for e in Education.objects.all()))
    if institutions:
        data["alumniOf"] = [{"@type": "CollegeOrUniversity", "name": n} for n in institutions]
    if profile.meta_description:
        data["description"] = profile.meta_description
    return data


def person_jsonld_json(profile: SiteProfile) -> str:
    """JSON prêt à être placé dans <script type="application/ld+json"> (sans fermeture possible)."""
    payload = json.dumps(build_person_jsonld(profile), ensure_ascii=False)
    return payload.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


# ---------------------------------------------------------------- expérience


@dataclass(frozen=True)
class TimelineImage:
    image: object
    alt_text: str
    caption: str
    link_label: str
    link_url: str
    external: bool

    @property
    def thumb(self):
        """Rendition carrée de la vignette (url, width, height), prête pour les includes."""
        return self.image.get_rendition("fill-216x216")


@dataclass(frozen=True)
class Achievement:
    """Réalisation ; `link_text`, s'il existe, est un passage du texte lié à `link_url`."""

    text: str
    link_text: str = ""
    link_url: str = ""

    @property
    def parts(self) -> tuple[str, str, str]:
        """(avant, lien, après) ; sans lien : (texte, "", "")."""
        if not (self.link_text and self.link_url) or self.link_text not in self.text:
            return self.text, "", ""
        before, _, after = self.text.partition(self.link_text)
        return before, self.link_text, after


@dataclass(frozen=True)
class TimelineEntry:
    experience: Experience
    period: str
    org_line: str
    achievements: list[Achievement] = field(default_factory=list)
    images: list[TimelineImage] = field(default_factory=list)
    period_start: str = ""
    period_end: str = ""


@dataclass(frozen=True)
class TimelineRow:
    """Une entrée seule, ou une paire d'entrées qui partagent les images de la première."""

    entries: list[TimelineEntry]
    images: list[TimelineImage]

    @property
    def is_pair(self) -> bool:
        return len(self.entries) == 2


def period_parts(start: date, end: date | None, precision: str) -> tuple[str, str]:
    """(« Dec 2022 », « present »), (« Jan », « Mar 2010 »), (« 2000 », « 2006 ») ; une période
    d'un seul mois ou d'une seule année donne (« Mar 2010 », «  »).

    Le gabarit les sépare par un tiret masqué aux lecteurs d'écran, qui entendent « to ».
    """
    if precision == Experience.DatePrecision.YEAR:
        if end is None:
            return str(start.year), PRESENT
        if end.year == start.year:
            return str(start.year), ""
        return str(start.year), str(end.year)

    start_month = MONTHS[start.month - 1]
    if end is None:
        return f"{start_month} {start.year}", PRESENT
    end_month = MONTHS[end.month - 1]
    if (start.year, start.month) == (end.year, end.month):
        return f"{start_month} {start.year}", ""
    if start.year == end.year:
        return start_month, f"{end_month} {end.year}"
    return f"{start_month} {start.year}", f"{end_month} {end.year}"


def format_period(start: date, end: date | None, precision: str) -> str:
    """« Dec 2022 — present », « Jan — Mar 2010 », « Sep 2006 — Sep 2009 », « 2000 — 2006 »."""
    first, last = period_parts(start, end, precision)
    return f"{first} {DASH} {last}" if last else first


def format_org_line(experience: Experience) -> str:
    """« Organisation — lieu ou marchés · orientation »."""
    line = experience.organisation
    if experience.scope:
        line += f" {DASH} {experience.scope}"
    if experience.focus:
        line += f" · {experience.focus}"
    return line


def publication_anchor(publication: Publication) -> str:
    return f"pub-{publication.pk}"


def publication_url(publication: Publication, profile: SiteProfile | None) -> str:
    """« /publications/#pub-12 » ; vide sans page des publications dans le profil."""
    page = profile.publications_page if profile else None
    if page is None:
        return ""
    return f"{page.url or ''}#{publication_anchor(publication)}"


def publication_link_label(publication: Publication) -> str:
    """« Kotkamp et al., 2014 » depuis « Kotkamp K, Kur E, … »."""
    first_author = publication.authors.split(",")[0].split()[0] if publication.authors else ""
    return f"{first_author} et al., {publication.year}".strip()


def _timeline_image(image, profile: SiteProfile | None) -> TimelineImage:
    label, url = image.link_label, image.link_url
    publication = image.publication
    if publication is not None:
        label = label or publication_link_label(publication)
        url = publication_url(publication, profile) or url
    return TimelineImage(
        image=image.image,
        alt_text=image.alt_text,
        caption=image.caption,
        link_label=label or "Link",
        link_url=url,
        external=url.startswith(("http://", "https://")),
    )


def _achievement(achievement: ExperienceAchievement, profile: SiteProfile | None) -> Achievement:
    publication = achievement.publication
    if publication is None or not achievement.link_text:
        return Achievement(achievement.text)
    return Achievement(
        achievement.text, achievement.link_text, publication_url(publication, profile)
    )


def _timeline_entry(experience: Experience, profile: SiteProfile | None) -> TimelineEntry:
    first, last = period_parts(
        experience.start_date, experience.end_date, experience.date_precision
    )
    return TimelineEntry(
        experience=experience,
        period=f"{first} {DASH} {last}" if last else first,
        period_start=first,
        period_end=last,
        org_line=format_org_line(experience),
        achievements=[_achievement(a, profile) for a in experience.achievements.all()],
        images=[_timeline_image(i, profile) for i in experience.images.all()],
    )


def list_timeline(category: str, profile: SiteProfile | None = None) -> list[TimelineEntry]:
    experiences = (
        Experience.objects.filter(category=category)
        .prefetch_related("achievements__publication", "images__image", "images__publication")
        .order_by("-start_date", "-id")
    )
    return [_timeline_entry(experience, profile) for experience in experiences]


def timeline_rows(entries: list[TimelineEntry]) -> list[TimelineRow]:
    """Regroupe une entrée « partage ses images avec la suivante » et la suivante en une paire.

    Une paire sans image, ou sans entrée suivante, redevient une entrée seule.
    """
    rows: list[TimelineRow] = []
    index = 0
    while index < len(entries):
        entry = entries[index]
        has_next = index + 1 < len(entries)
        if entry.experience.pair_with_next and entry.images and has_next:
            rows.append(TimelineRow([entry, entries[index + 1]], entry.images))
            index += 2
        else:
            rows.append(TimelineRow([entry], entry.images))
            index += 1
    return rows


def timeline_label(category: str) -> str:
    """« Industry — 2011 to present », années déduites des données."""
    experiences = list(Experience.objects.filter(category=category))
    label = Experience.Category(category).label
    if not experiences:
        return label
    first_year = min(e.start_date.year for e in experiences)
    if any(e.end_date is None for e in experiences):
        last = "present"
    else:
        last = str(max(e.end_date.year for e in experiences))
    return f"{label} {DASH} {first_year} to {last}"


def list_education() -> list[Education]:
    """Formations affichées en cartes (les autres ne servent qu'aux données structurées)."""
    return list(Education.objects.filter(listed=True))


# ---------------------------------------------------------------- publications et médias


@dataclass(frozen=True)
class PublicationEntry:
    publication: Publication
    number: str
    anchor: str
    pubmed_url: str


def pubmed_article_url(pmid: str) -> str:
    return f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ""


def list_publications(category: str | None = None) -> list[PublicationEntry]:
    """Publications dans l'ordre d'affichage ; la numérotation repart à 01 dans chaque catégorie."""
    publications = Publication.objects.all()
    if category:
        publications = publications.filter(category=category)
    numbers: dict[str, int] = {}
    entries = []
    for publication in publications:
        numbers[publication.category] = numbers.get(publication.category, 0) + 1
        entries.append(
            PublicationEntry(
                publication=publication,
                number=f"{numbers[publication.category]:02d}",
                anchor=publication_anchor(publication),
                pubmed_url=pubmed_article_url(publication.pmid),
            )
        )
    return entries


def list_media(kind: str) -> list[MediaAppearance]:
    return list(MediaAppearance.objects.filter(kind=kind))
