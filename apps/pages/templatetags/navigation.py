from django import template
from wagtail.models import Site

from apps.pages.services import get_main_menu, get_nav_items

register = template.Library()


@register.simple_tag(takes_context=True)
def main_menu(context):
    return get_main_menu(Site.find_for_request(context["request"]))


@register.simple_tag(takes_context=True)
def nav_items(context):
    """Paramètre `items` de includes/nav.html ; la page courante est celle du contexte."""
    request = context["request"]
    return get_nav_items(Site.find_for_request(request), context.get("page"), request)
