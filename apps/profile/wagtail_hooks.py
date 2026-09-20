from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup

from .models import Education, Experience, Language, MediaAppearance, Publication


class ExperienceViewSet(SnippetViewSet):
    model = Experience
    icon = "history"
    list_display = ["title", "organisation", "category", "start_date", "end_date"]
    list_filter = ["category"]
    search_fields = ["title", "organisation"]


class PublicationViewSet(SnippetViewSet):
    model = Publication
    icon = "doc-full"
    list_display = ["title", "journal", "year", "pmid", "sort_order"]
    search_fields = ["title", "authors", "journal"]


class EducationViewSet(SnippetViewSet):
    model = Education
    icon = "doc-empty"
    list_display = ["degree", "institution", "year", "sort_order"]


class MediaAppearanceViewSet(SnippetViewSet):
    model = MediaAppearance
    icon = "media"
    list_display = ["title", "outlet", "kind", "date", "sort_order"]
    list_filter = ["kind"]
    search_fields = ["title", "outlet"]


class LanguageViewSet(SnippetViewSet):
    model = Language
    icon = "site"
    list_display = ["english_name", "native_name", "code", "level", "sort_order"]


class ProfileViewSetGroup(SnippetViewSetGroup):
    items = (
        ExperienceViewSet,
        PublicationViewSet,
        EducationViewSet,
        MediaAppearanceViewSet,
        LanguageViewSet,
    )
    menu_label = "Profile"
    menu_icon = "user"
    menu_order = 200


register_snippet(ProfileViewSetGroup)
