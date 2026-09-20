import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"
DESIGN_TOKENS = ROOT / "_artifact" / "design" / "tokens.css"
COMPONENT_STYLESHEETS = tuple(
    f"css/components/{path.name}" for path in sorted((STATIC / "css" / "components").glob("*.css"))
)
SITE_STYLESHEETS = (
    "css/base.css",
    "css/site.css",
    "css/demo.css",  # page temporaire /_composants
    *COMPONENT_STYLESHEETS,
)


def _read(name: str) -> str:
    return (STATIC / name).read_text(encoding="utf-8")


def _strip_comments(css: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


@pytest.mark.parametrize("name", SITE_STYLESHEETS)
def test_every_variable_used_is_defined_in_tokens_or_locally(name):
    css = _strip_comments(_read(name))
    defined = set(re.findall(r"(--[a-z0-9-]+)\s*:", _read("css/tokens.css")))
    defined |= set(re.findall(r"(--[a-z0-9-]+)\s*:", css))
    used = set(re.findall(r"var\((--[a-z0-9-]+)", css))

    assert used - defined == set()


@pytest.mark.parametrize("name", SITE_STYLESHEETS)
def test_stylesheets_have_no_hard_coded_colors(name):
    assert re.findall(r"#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(", _strip_comments(_read(name))) == []


def test_tokens_keep_every_value_of_the_design():
    def declarations(css: str) -> dict[str, list[str]]:
        found: dict[str, list[str]] = {}
        for name, value in re.findall(r"(--[a-z0-9-]+)\s*:\s*([^;]+);", _strip_comments(css)):
            found.setdefault(name, []).append(" ".join(value.split()))
        return found

    design = declarations(DESIGN_TOKENS.read_text(encoding="utf-8"))
    ours = declarations(_read("css/tokens.css"))

    assert {
        name: (design[name], ours.get(name)) for name in design if design[name] != ours.get(name)
    } == {}


def test_fonts_are_self_hosted():
    css = _read("css/fonts.css")
    files = re.findall(r'url\("\.\./fonts/([^"]+)"\)', css)

    assert files
    assert "http" not in _strip_comments(css)
    for name in set(files):
        assert (STATIC / "fonts" / name).is_file(), name
    assert (STATIC / "fonts" / "LICENSES.txt").is_file()


def test_fonts_cover_polish_characters():
    assert "latin-ext" in _read("css/fonts.css")


# Valeurs exactes du design : ces deux couleurs n'atteignent pas 4,5:1 sur --surface-tint.
# strict=True : le test échoue si quelqu'un les modifie (voir docs/site-architecture.md).
BELOW_AA_ON_TINT = {
    "ink-faint": pytest.mark.xfail(strict=True, reason="design value #647268: 4.26:1"),
    "accent-2": pytest.mark.xfail(strict=True, reason="design value #9c5c1b: 4.46:1"),
}


@pytest.mark.parametrize(
    "name",
    [
        pytest.param(n, marks=BELOW_AA_ON_TINT.get(n, ()))
        for n in ("ink", "ink-muted", "ink-faint", "accent", "accent-2")
    ],
)
def test_text_colors_reach_wcag_aa_on_the_tinted_background(name):
    def luminance(hex_color: str) -> float:
        channels = [int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
        lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
        return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]

    def contrast(a: str, b: str) -> float:
        hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
        return (hi + 0.05) / (lo + 0.05)

    light = _strip_comments(_read("css/tokens.css")).split("@media")[0]
    color = lambda n: re.search(rf"--{n}:\s*(#[0-9a-f]{{6}})", light).group(1)  # noqa: E731

    assert contrast(color(name), color("surface-tint")) >= 4.5
