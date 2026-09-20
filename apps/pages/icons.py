"""Jeu d'icônes du design (ligne, viewBox 24×24).

Le dessin de chaque icône est un fichier `templates/includes/icons/<nom>.svg`. Ce module ne
porte que la liste des icônes proposées à l'éditeur (nom -> libellé) ; l'ordre est celui du
sélecteur d'administration. Les icônes d'interface (ex. `chevron`) ne sont pas listées ici.
"""

ICONS: dict[str, str] = {
    "compass": "Compass",
    "document": "Document",
    "chat": "Speech bubble",
    "network": "Network",
    "flask": "Flask",
    "globe": "Globe",
    "flag": "Flag",
    "fish": "Fish",
    "target": "Target",
    "ballet": "Dancer",
    "camera": "Camera",
    "flame": "Flame",
    "clock": "Clock",
    "search": "Magnifier",
}

TEMPLATE_PATH = "includes/icons/{name}.svg"


def icon_choices() -> list[tuple[str, str]]:
    return list(ICONS.items())
