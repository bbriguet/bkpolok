from django.conf import settings
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET
from django.views.generic import TemplateView

from . import demo
from .services import check_database


@require_GET
def healthz(request: HttpRequest) -> JsonResponse:
    if check_database():
        return JsonResponse({"status": "ok"})
    return JsonResponse({"status": "error", "detail": "database"}, status=503)


class RobotsTxtView(TemplateView):
    template_name = "robots.txt"
    content_type = "text/plain; charset=utf-8"


robots_txt = RobotsTxtView.as_view()


@require_GET
def components_demo(request: HttpRequest) -> HttpResponse:
    """Page temporaire listant tous les composants (DEBUG uniquement ; 404 sinon)."""
    if not settings.DEBUG:
        raise Http404
    return render(request, "dev/components_demo.html", demo.get_context())
