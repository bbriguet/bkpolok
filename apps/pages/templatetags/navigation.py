from django import template
from wagtail.models import Site

from apps.pages.services import get_main_menu

register = template.Library()


@register.simple_tag(takes_context=True)
def main_menu(context):
    return get_main_menu(Site.find_for_request(context["request"]))
