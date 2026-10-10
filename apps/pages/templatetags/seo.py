from django import template

from apps.pages.services import build_seo
from apps.profile.services import get_site_profile

register = template.Library()


@register.simple_tag(takes_context=True)
def page_seo(context):
    """Métadonnées SEO / Open Graph de la page du contexte (dict vide hors page Wagtail)."""
    request = context["request"]
    return build_seo(context.get("page"), request, get_site_profile(request))
