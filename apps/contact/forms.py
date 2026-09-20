from django import forms
from django.core.exceptions import ValidationError

from .models import ContactMessage

HONEYPOT_FIELD = "website"


def validate_single_line(value: str) -> None:
    if "\n" in value or "\r" in value:
        raise ValidationError("Line breaks are not allowed here.")


class ContactForm(forms.ModelForm):
    """Formulaire public. `website` est un piège à robots : un humain ne le voit pas."""

    website = forms.CharField(
        required=False,
        label="Leave this field empty",
        widget=forms.TextInput(attrs={"tabindex": "-1", "autocomplete": "off"}),
    )

    class Meta:
        model = ContactMessage
        fields = ["name", "email", "subject", "message"]
        widgets = {
            "name": forms.TextInput(attrs={"autocomplete": "name"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "message": forms.Textarea(attrs={"rows": 7}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["subject"].validators.append(validate_single_line)
        self.fields["name"].validators.append(validate_single_line)

    @property
    def is_spam(self) -> bool:
        return bool(self.cleaned_data.get(HONEYPOT_FIELD))

    def full_clean(self):
        super().full_clean()
        # Relie chaque champ en erreur à son message (voir includes/contact_form.html).
        for name in self.errors:
            if name in self.fields:
                self.fields[name].widget.attrs["aria-describedby"] = f"{self[name].auto_id}_error"
