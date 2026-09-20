"""Jeu d'icônes du design (ligne, viewBox 24×24). Les valeurs sont le contenu interne du <svg>."""
# ruff: noqa: E501  (chemins SVG : données, pas du code)

ICONS: dict[str, tuple[str, str]] = {
    "compass": (
        "Compass",
        '<circle cx="12" cy="12" r="9"/><path d="M14.5 9.5 10 10l-0.5 4.5L14 14z"/>',
    ),
    "document": (
        "Document",
        '<path d="M4 19V6a2 2 0 0 1 2-2h8l6 6v9a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2Z"/>'
        '<path d="M14 4v6h6M8 13h8M8 17h5"/>',
    ),
    "chat": (
        "Speech bubble",
        '<path d="M21 15a2 2 0 0 1-2 2H8l-5 4V6a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    ),
    "network": (
        "Network",
        '<circle cx="6" cy="6" r="2.4"/><circle cx="18" cy="6" r="2.4"/>'
        '<circle cx="12" cy="18" r="2.4"/><path d="M8 7.3 10.3 16M16 7.3 13.7 16M8.4 6h7.2"/>',
    ),
    "flask": (
        "Flask",
        '<path d="M9 3h6M10 3v4.5L5.5 16a2 2 0 0 0 1.8 3h9.4a2 2 0 0 0 1.8-3L14 7.5V3"/>'
        '<path d="M7.5 14h9"/>',
    ),
    "globe": (
        "Globe",
        '<circle cx="12" cy="12" r="9"/>'
        '<path d="M3 12h18M12 3c2.5 2.6 3.8 5.8 3.8 9s-1.3 6.4-3.8 9c-2.5-2.6-3.8-5.8-3.8-9S9.5 5.6 12 3Z"/>',
    ),
    "flag": ("Flag", '<path d="M4 4v16M4 4h11l-2 4 2 4H4"/>'),
    "fish": (
        "Fish",
        '<path d="M4 12c3-4 6-5 9-5 3.5 0 6 2.2 7 5-1 2.8-3.5 5-7 5-3 0-6-1-9-5Z"/>'
        '<path d="M13 7c1-1.5 3-2 4-1M13 17c1 1.5 3 2 4 1M4 12l-2-1.5M4 12l-2 1.5"/>',
    ),
    "target": (
        "Target",
        '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/>'
        '<path d="M12 2v3M12 19v3M2 12h3M19 12h3"/>',
    ),
    "ballet": (
        "Dancer",
        '<path d="M9 3c0 3-2 4-2 7 0 2.5 1.8 4 3.5 5L9 20h6l-1.5-5c1.7-1 3.5-2.5 3.5-5 0-3-2-4-2-7"/>'
        '<path d="M9 3h6"/>',
    ),
    "camera": (
        "Camera",
        '<path d="M4 8h3l2-2.5h6L17 8h3a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1Z"/>'
        '<circle cx="12" cy="13.5" r="3.3"/>',
    ),
    "flame": (
        "Flame",
        '<path d="M12 3c-3 3-4 6-4 8.5a4 4 0 0 0 8 0c0-2.5-1-5.5-4-8.5Z"/>'
        '<path d="M12 15.5V21M8.5 21h7"/>',
    ),
    "clock": ("Clock", '<circle cx="12" cy="12" r="9"/><path d="M12 8v4l3 2"/>'),
    "search": (
        "Magnifier",
        '<circle cx="10" cy="10" r="6"/><line x1="14.5" y1="14.5" x2="20" y2="20"/>',
    ),
}


def icon_choices() -> list[tuple[str, str]]:
    return [(name, label) for name, (label, _) in ICONS.items()]
