"""Contrastes WCAG des tokens de couleur (static/css/tokens.css) : thèmes clair, sombre, et
contraste élevé (clair et sombre)."""

import re
from pathlib import Path

import pytest

TOKENS = Path(__file__).resolve().parent.parent / "static" / "css" / "tokens.css"


def _declarations(block: str) -> dict[str, str]:
    return dict(re.findall(r"--([\w-]+):\s*(#[0-9a-fA-F]{6})\s*;", block))


def _block(css: str, selector: str) -> str:
    """Corps du premier bloc `selector { … }` (sans bloc imbriqué)."""
    start = css.index(selector + " {") + len(selector) + 2
    return css[start : css.index("}", start)]


def _themes() -> dict[str, dict[str, str]]:
    css = TOKENS.read_text()
    light = _declarations(_block(css, ":root"))
    dark = _declarations(_block(css, ':root[data-theme="dark"]'))
    media = _declarations(_block(css, ':root:not([data-theme="light"])'))
    assert media == dark, "dark theme: media query and forced block differ"
    high = _declarations(_block(css, ':root[data-contrast="high"]'))
    high_dark = _declarations(_block(css, ':root[data-contrast="high"][data-theme="dark"]'))
    return {
        "light": light,
        "dark": {**light, **dark},
        "high": {**light, **high},
        "high-dark": {**light, **dark, **high, **high_dark},
    }


def _luminance(hex_color: str) -> float:
    channels = [int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    r, g, b = (c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    hi, lo = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


THEMES = _themes()
NAMES = list(THEMES)
# Jetons de texte, et les fonds sur lesquels ils sont réellement posés.
TEXT = ("ink", "ink-muted", "ink-faint", "accent", "accent-2")
SURFACES = ("bg", "surface", "surface-tint")


@pytest.mark.parametrize("theme", NAMES)
@pytest.mark.parametrize("surface", SURFACES)
@pytest.mark.parametrize("token", TEXT)
def test_text_tokens_reach_aa_on_every_surface(theme, surface, token):
    colors = THEMES[theme]

    assert contrast(colors[token], colors[surface]) >= 4.5


@pytest.mark.parametrize("surface", SURFACES)
@pytest.mark.parametrize("token", TEXT)
def test_high_contrast_theme_reaches_aaa(surface, token):
    for theme in ("high", "high-dark"):
        colors = THEMES[theme]

        assert contrast(colors[token], colors[surface]) >= 7


@pytest.mark.parametrize("theme", NAMES)
def test_ink_on_soft_backgrounds_reaches_aa(theme):
    colors = THEMES[theme]

    assert contrast(colors["ink"], colors["accent-soft"]) >= 4.5
    assert contrast(colors["ink"], colors["accent-2-soft"]) >= 4.5


@pytest.mark.parametrize("theme", NAMES)
def test_button_and_focus_ring_reach_non_text_contrast(theme):
    colors = THEMES[theme]

    assert contrast(colors["bg"], colors["accent"]) >= 4.5  # --on-accent sur .btn-primary
    assert contrast(colors["accent"], colors["bg"]) >= 3  # anneau de focus, WCAG 1.4.11


@pytest.mark.parametrize("theme", NAMES)
def test_borders_of_controls_reach_non_text_contrast(theme):
    """Champs de formulaire, boutons fantômes et boutons d'affichage : --line-strong."""
    colors = THEMES[theme]

    assert contrast(colors["line-strong"], colors["surface"]) >= 3
    assert contrast(colors["line-strong"], colors["bg"]) >= 3


@pytest.mark.parametrize("theme", NAMES)
def test_pressed_settings_button_is_readable(theme):
    """Bouton d'affichage enfoncé : texte --bg sur fond --ink."""
    colors = THEMES[theme]

    assert contrast(colors["bg"], colors["ink"]) >= 7
