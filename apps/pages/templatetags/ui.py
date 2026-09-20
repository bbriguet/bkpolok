from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from apps.pages.icons import ICONS

register = template.Library()


@register.simple_tag
def icon(name):
    """SVG de ligne du jeu d'icônes ; chaîne vide si le nom est inconnu."""
    entry = ICONS.get(name)
    if entry is None:
        return ""
    return format_html(
        '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke-width="1.6" '
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">'
        "{}</svg>",
        mark_safe(entry[1]),
    )
