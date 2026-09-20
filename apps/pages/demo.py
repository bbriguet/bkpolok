"""Données fictives de la page de démonstration des composants (/_composants, DEBUG uniquement).

Temporaire : à supprimer avec `templates/dev/`, `static/css/demo.css`, `static/demo/` et la route
`components_demo` une fois les composants validés. Aucun contenu réel du site ici.
"""

from datetime import date

from django.templatetags.static import static

from .icons import ICONS

LOREM = "Short placeholder text that shows how a paragraph wraps inside the component."


def get_context() -> dict:
    photo = {"url": static("demo/portrait.svg"), "width": 408, "height": 408}

    def thumb(caption, link_label="", link_url="", external=False):
        return {
            "thumb": photo,
            "alt_text": "Placeholder portrait",
            "caption": caption,
            "link_label": link_label,
            "link_url": link_url,
            "external": external,
        }

    def entry(period, title, org, description="", summary=LOREM, achievements=(), images=()):
        return {
            "period": period,
            "experience": {
                "title": title,
                "organisation_description": description,
                "summary": summary,
            },
            "org_line": org,
            "achievements": list(achievements),
            "images": list(images),
        }

    cards = [
        {"icon": name, "title": f"Card title {n}", "text": LOREM, "wide": False}
        for n, name in enumerate(["compass", "document", "chat", "network", "flask", "globe"], 1)
    ]
    off_cards = [
        {"icon": name, "title": f"Off the clock {n}", "text": LOREM, "wide": n == 5}
        for n, name in enumerate(["fish", "target", "ballet", "camera", "flame"], 1)
    ]

    return {
        "photo": photo,
        "nav_items": [
            {"label": "About", "href": "#nav", "current": True},
            {"label": "Expertise", "href": "#nav"},
            {"label": "Experience", "href": "#nav"},
            {"label": "Personal", "disabled": True},
            {"label": "Contact", "href": "#nav"},
        ],
        "pills": ["Alpha area", "Beta area", "Gamma area", "Delta area"],
        "languages": [
            {"native_name": "Polski", "code": "pl"},
            {"native_name": "Français", "code": "fr"},
            {"native_name": "English", "code": "en"},
        ],
        "language_codes": ["PL", "FR", "EN"],
        "hero_buttons": [
            {"label": "Get in touch", "href": "#buttons", "variant": "primary", "external": False},
            {
                "label": "External ↗",
                "href": "https://example.org",
                "variant": "ghost",
                "external": True,
            },
            {"label": "See more", "href": "#buttons", "variant": "ghost", "external": False},
        ],
        "cards": cards,
        "off_cards": off_cards,
        "notes": [
            {"icon": "clock", "text": "A short aside note with a teal icon."},
            {"icon": "search", "text": "A second note sits beside the first one."},
        ],
        "offers": [
            {"title": "First offer", "href": "#offers", "summary": LOREM},
            {"title": "Second offer", "href": "#offers", "summary": LOREM},
            {"title": "Third offer", "href": "#offers", "summary": LOREM},
        ],
        "timeline_industry": [
            entry(
                "DEC 2022 — PRESENT",
                "Senior role title",
                "Example Corp — Global · Focus area",
                "One-line description of the organisation.",
                achievements=["First achievement of the role", "Second achievement of the role"],
            ),
            entry("JAN 2015 — NOV 2022", "Previous role title", "Another Corp — Europe"),
        ],
        "timeline_research": [
            entry(
                "2003 — 2006",
                "Research role with photos",
                "Example Institute — Lab",
                "One-line description of the institute.",
                images=[thumb("FIG. 1", "Author et al., 2006", "#pub-02")],
            ),
        ],
        "thumbs": [
            thumb("FIG. 1", "Author et al., 2014", "#publications"),
            thumb("FIG. 2"),
        ],
        "education": [
            {"degree": "PhD, Example Discipline", "institution": "University of Example"},
            {"degree": "MSc, Another Discipline", "institution": "Example Institute of Technology"},
        ],
        "publications": [
            {
                "number": "01",
                "anchor": "pub-01",
                "pubmed_url": "https://example.org/pubmed/1",
                "publication": {
                    "title": "A placeholder title for a paper with a PubMed link",
                    "authors": "Doe J, Roe R, et al.",
                    "journal": "Journal of Examples",
                    "year": 2014,
                    "pmid": "1234567",
                },
            },
            {
                "number": "02",
                "anchor": "pub-02",
                "pubmed_url": "",
                "publication": {
                    "title": "A placeholder title for a paper without a link",
                    "authors": "Doe J, et al.",
                    "journal": "Older Journal",
                    "year": 2002,
                    "pmid": "",
                },
            },
        ],
        "media": [
            {
                "date": date(2009, 1, 14),
                "outlet": "Channel",
                "title": "A linked item",
                "url": "https://example.org",
            },
            {
                "date": None,
                "outlet": "Newspaper",
                "title": "An item without link or date",
                "url": "",
            },
        ],
        "media_note": (
            '<p>Video not available online — <a href="https://example.org">see the archive</a>.</p>'
        ),
        "faq": [
            {
                "question": "A first question?",
                "answer": '<p>The answer, with <a href="#faq">a link</a>.</p>',
            },
            {
                "question": "A second question?",
                "answer": "<p>Another answer.</p><ul><li>One</li><li>Two</li></ul>",
            },
            {"question": "A third question?", "answer": "<p>Yet another answer.</p>"},
        ],
        "icons": [(name, label) for name, label in ICONS.items()] + [("chevron", "Chevron (UI)")],
    }
