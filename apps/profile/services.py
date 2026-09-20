import json
import unicodedata
from dataclasses import dataclass, field
from datetime import date

from .models import (
    Education,
    Experience,
    Language,
    MediaAppearance,
    Publication,
    SiteProfile,
)

MONTHS = ("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC")
PRESENT = "PRESENT"
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


def _join_names(names: list[str]) -> str:
    if len(names) <= 2:
        return " & ".join(names)
    return f"{', '.join(names[:-1])} & {names[-1]}"


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


@dataclass(frozen=True)
class TimelineEntry:
    experience: Experience
    period: str
    org_line: str
    achievements: list[str] = field(default_factory=list)
    images: list[TimelineImage] = field(default_factory=list)


def format_period(start: date, end: date | None, precision: str) -> str:
    """« DEC 2022 — PRESENT », « JAN — MAR 2010 », « SEP 2006 — SEP 2009 », « 2000 — 2006 »."""
    if precision == Experience.DatePrecision.YEAR:
        if end is None:
            return f"{start.year} {DASH} {PRESENT}"
        if end.year == start.year:
            return str(start.year)
        return f"{start.year} {DASH} {end.year}"

    start_month = MONTHS[start.month - 1]
    if end is None:
        return f"{start_month} {start.year} {DASH} {PRESENT}"
    end_month = MONTHS[end.month - 1]
    if (start.year, start.month) == (end.year, end.month):
        return f"{start_month} {start.year}"
    if start.year == end.year:
        return f"{start_month} {DASH} {end_month} {end.year}"
    return f"{start_month} {start.year} {DASH} {end_month} {end.year}"


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


def publication_link_label(publication: Publication) -> str:
    """« Kotkamp et al., 2014 » depuis « Kotkamp K, Kur E, … »."""
    first_author = publication.authors.split(",")[0].split()[0] if publication.authors else ""
    return f"{first_author} et al., {publication.year}".strip()


def _timeline_image(image, profile: SiteProfile | None) -> TimelineImage:
    label, url = image.link_label, image.link_url
    publication = image.publication
    if publication is not None:
        label = label or publication_link_label(publication)
        page = profile.publications_page if profile else None
        if page is not None:
            url = f"{page.url or ''}#{publication_anchor(publication)}"
    return TimelineImage(
        image=image.image,
        alt_text=image.alt_text,
        caption=image.caption,
        link_label=label or "Link",
        link_url=url,
        external=url.startswith(("http://", "https://")),
    )


def list_timeline(category: str, profile: SiteProfile | None = None) -> list[TimelineEntry]:
    experiences = (
        Experience.objects.filter(category=category)
        .prefetch_related("achievements", "images__image", "images__publication")
        .order_by("-start_date", "-id")
    )
    return [
        TimelineEntry(
            experience=experience,
            period=format_period(
                experience.start_date, experience.end_date, experience.date_precision
            ),
            org_line=format_org_line(experience),
            achievements=[a.text for a in experience.achievements.all()],
            images=[_timeline_image(i, profile) for i in experience.images.all()],
        )
        for experience in experiences
    ]


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
    return list(Education.objects.all())


# ---------------------------------------------------------------- publications et médias


@dataclass(frozen=True)
class PublicationEntry:
    publication: Publication
    number: str
    anchor: str
    pubmed_url: str


def pubmed_article_url(pmid: str) -> str:
    return f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ""


def list_publications() -> list[PublicationEntry]:
    return [
        PublicationEntry(
            publication=publication,
            number=f"{index:02d}",
            anchor=publication_anchor(publication),
            pubmed_url=pubmed_article_url(publication.pmid),
        )
        for index, publication in enumerate(Publication.objects.all(), start=1)
    ]


def list_media(kind: str) -> list[MediaAppearance]:
    return list(MediaAppearance.objects.filter(kind=kind))
