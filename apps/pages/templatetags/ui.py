import re

from django import template
from django.template.loader import get_template

from apps.pages.icons import TEMPLATE_PATH

register = template.Library()

ICON_NAME = re.compile(r"[a-z0-9-]+")


@register.simple_tag
def icon(name):
    """SVG de ligne `templates/includes/icons/<name>.svg` ; chaîne vide si l'icône n'existe pas."""
    if not name or not ICON_NAME.fullmatch(name):
        return ""
    try:
        return get_template(TEMPLATE_PATH.format(name=name)).render()
    except template.TemplateDoesNotExist:
        return ""
