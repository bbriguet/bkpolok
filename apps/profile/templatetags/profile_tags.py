from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from apps.profile import services

register = template.Library()


@register.simple_tag(takes_context=True)
def site_profile(context):
    return services.get_site_profile(context["request"])


@register.simple_tag(takes_context=True)
def site_footer(context):
    """Paramètres de includes/footer.html, tirés du profil du site et des langues."""
    request = context["request"]
    return services.build_footer(services.get_site_profile(request), request)


@register.filter
def display_url(url):
    return services.display_url(url or "")


@register.filter
def language_name(code):
    return services.language_name(code or "")


@register.simple_tag
def language_codes():
    return services.language_codes()


@register.simple_tag(takes_context=True)
def person_jsonld(context):
    profile = services.get_site_profile(context["request"])
    payload = services.person_jsonld_json(profile)
    return format_html('<script type="application/ld+json">{}</script>', mark_safe(payload))
