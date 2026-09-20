import re
from pathlib import Path

STATIC = Path(__file__).resolve().parent.parent / "static"


def _read(name: str) -> str:
    return (STATIC / name).read_text(encoding="utf-8")


def _strip_comments(css: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def test_every_variable_used_by_site_css_is_defined_in_tokens():
    defined = set(re.findall(r"(--[a-z0-9-]+)\s*:", _read("css/tokens.css")))
    used = set(re.findall(r"var\((--[a-z0-9-]+)", _strip_comments(_read("css/site.css"))))

    assert used - defined == set()


def test_site_css_has_no_hard_coded_colors():
    assert re.findall(r"#[0-9a-fA-F]{3,8}\b", _strip_comments(_read("css/site.css"))) == []


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


def test_text_colors_reach_wcag_aa_on_the_tinted_background():
    def luminance(hex_color: str) -> float:
        channels = [int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
        lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
        return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]

    def contrast(a: str, b: str) -> float:
        hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
        return (hi + 0.05) / (lo + 0.05)

    light = _strip_comments(_read("css/tokens.css")).split("@media")[0]
    color = lambda name: re.search(rf"--{name}:\s*(#[0-9a-f]{{6}})", light).group(1)  # noqa: E731

    for name in ("ink", "ink-muted", "ink-faint", "accent", "accent-2"):
        assert contrast(color(name), color("surface-tint")) >= 4.5, name
