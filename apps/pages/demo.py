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

    def entry(start, end, title, org, parallel_role="", summary=LOREM, achievements=()):
        return {
            "period_start": start,
            "period_end": end,
            "experience": {
                "title": title,
                "parallel_role": parallel_role,
                "summary": summary,
            },
            "org_line": org,
            "achievements": [
                {"parts": (a, "", "")} if isinstance(a, str) else a for a in achievements
            ],
        }

    def row(*entries, images=()):
        return {"entries": list(entries), "images": list(images), "is_pair": len(entries) == 2}

    def image(alt):
        return {**photo, "alt": alt}

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
        "figure": {
            "images": [image("Placeholder one"), image("Placeholder two")],
            "title": "Figure title",
            "caption": "A caption that explains the two images.",
        },
        "gallery": [image(f"Placeholder photo {n}") for n in range(1, 4)],
        "accessibility": '<p>A short statement with <a href="#footer">a link</a>.</p>',
        "legal_links": [
            {"label": "Legal notice", "href": "#footer"},
            {"label": "Privacy statement", "href": "#footer"},
        ],
        "offers": [
            {"title": "First offer", "href": "#offers", "summary": LOREM},
            {"title": "Second offer", "href": "#offers", "summary": LOREM},
            {"title": "Third offer", "href": "#offers", "summary": LOREM},
        ],
        "timeline_industry": [
            row(
                entry(
                    "Dec 2022",
                    "present",
                    "Senior role title",
                    "Example Corp — Global · Focus area",
                    parallel_role="Second hat",
                    achievements=[
                        "First achievement of the role",
                        {
                            "parts": ("Led to ", "Doe et al. (2022)", " on a topic"),
                            "link_url": "#publications",
                        },
                    ],
                )
            ),
            row(
                entry("Jan 2015", "Nov 2022", "Previous role title", "Another Corp — Europe"),
                images=[thumb("Device", "Maker", "https://example.org", external=True)],
            ),
        ],
        "timeline_research": [
            row(
                entry("Sep 2006", "Sep 2009", "Research role", "Example Institute — Lab"),
                entry("2000", "2006", "PhD, Example Discipline", "University of Example"),
                images=[
                    thumb("FIG. 1", "Author et al., 2006", "#pub-02"),
                    thumb("FIG. 5", "Author et al., 2006", "#pub-02"),
                ],
            ),
        ],
        "thumbs": [
            thumb("FIG. 1", "Author et al., 2014", "#publications"),
            thumb("FIG. 2"),
        ],
        "education": [
            {
                "degree": "MSc, Another Discipline",
                "institution": "Example Institute of Technology",
                "description": LOREM,
            },
        ],
        "featured_publications": [
            {
                "number": "01",
                "anchor": "pub-ma",
                "pubmed_url": "https://example.org/pubmed/3",
                "publication": {
                    "title": "A placeholder title for a highlighted paper",
                    "authors": "Roe R, Doe J",
                    "journal": "Journal of Examples",
                    "year": 2022,
                    "pmid": "7654321",
                    "note": "One sentence on where the paper came from.",
                },
            },
        ],
        "more_publications": [
            {
                "number": "03",
                "anchor": "pub-03",
                "pubmed_url": "",
                "publication": {
                    "title": "A placeholder title hidden under show more",
                    "authors": "Doe J",
                    "journal": "Older Journal",
                    "year": 2001,
                    "pmid": "",
                },
            },
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
        "icons": [(name, label) for name, label in ICONS.items()]
        + [("chevron", "Chevron (UI)"), ("settings", "Settings (UI)")],
    }
