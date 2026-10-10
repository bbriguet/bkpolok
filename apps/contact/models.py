from django.db import models


class ContactMessage(models.Model):
    """Message envoyé depuis le formulaire de contact, conservé même si l'email échoue."""

    name = models.CharField("Name", max_length=120)
    email = models.EmailField("Email address")
    subject = models.CharField("Subject", max_length=150)
    message = models.TextField("Message", max_length=5000)
    created_at = models.DateTimeField("Received", auto_now_add=True)
    emailed_at = models.DateTimeField("Emailed", null=True, blank=True)
    email_error = models.CharField("Email error", max_length=250, blank=True)

    class Meta:
        verbose_name = "message de contact"
        verbose_name_plural = "messages de contact"
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"{self.name} — {self.subject}"
