from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.contrib.sitemaps.views import sitemap
from wagtail.documents import urls as wagtaildocs_urls

from apps.pages import views as pages_views

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("admin/", include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
    path("healthz", pages_views.healthz, name="healthz"),
    path("robots.txt", pages_views.robots_txt, name="robots_txt"),
    path("sitemap.xml", sitemap),
    # Page temporaire de validation des composants ; la vue répond 404 hors DEBUG.
    re_path(r"^_composants/?$", pages_views.components_demo, name="components_demo"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Wagtail sert toutes les autres URLs : doit rester en dernier.
urlpatterns += [path("", include(wagtail_urls))]
