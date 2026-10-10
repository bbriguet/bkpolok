from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from .models import ContactMessage


class ContactMessageViewSet(SnippetViewSet):
    model = ContactMessage
    icon = "mail"
    menu_label = "Messages"
    menu_order = 210
    add_to_admin_menu = True
    inspect_view_enabled = True
    list_display = ["name", "email", "subject", "created_at", "emailed_at"]
    list_filter = ["created_at"]
    search_fields = ["name", "email", "subject", "message"]


register_snippet(ContactMessageViewSet)
