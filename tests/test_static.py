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

    # Aucun écart : la version 2026-10 du design atteint elle-même les contrastes AA
    # (tests/test_tokens_contrast.py).
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


def test_text_sizes_are_in_rem_so_the_text_size_control_scales_them():
    sizes = re.findall(r"--fs-[a-z0-9-]+:\s*([^;]+);", _read("css/tokens.css"))

    assert sizes and all("px" not in size for size in sizes)


@pytest.mark.parametrize("name", SITE_STYLESHEETS)
def test_font_sizes_go_through_tokens(name):
    css = _strip_comments(_read(name))

    assert re.findall(r"font-size:\s*\d+(?:\.\d+)?(?:px|rem)", css) == []
