from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_GET
from django.views.generic import TemplateView

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
