import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone

from .forms import ContactForm
from .models import ContactMessage

logger = logging.getLogger(__name__)

SUBJECT_PREFIX = "[Website]"


def send_notification(message: ContactMessage, recipient: str) -> None:
    """Envoie le message à `recipient` ; l'adresse de l'expéditeur est en Reply-To."""
    body = (
        f"From: {message.name} <{message.email}>\nSubject: {message.subject}\n\n{message.message}\n"
    )
    EmailMessage(
        subject=f"{SUBJECT_PREFIX} {message.subject}",
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL or None,
        to=[recipient],
        reply_to=[message.email],
    ).send(fail_silently=False)


def submit_contact_form(form: ContactForm, recipient: str) -> ContactMessage | None:
    """Traite un formulaire valide : enregistre le message puis l'envoie par email.

    Le message est enregistré avant l'envoi : si le SMTP échoue, il n'est pas perdu et l'erreur
    est consultable dans l'admin. Un formulaire dont le honeypot est rempli est ignoré sans
    rien enregistrer (retourne None) ; l'appelant répond comme pour un succès.
    """
    if form.is_spam:
        logger.info("Contact form: honeypot filled, submission dropped")
        return None
    message = form.save()
    if not recipient:
        message.email_error = "No recipient configured"
        message.save(update_fields=["email_error"])
        logger.error("Contact form: message %s saved but no recipient is configured", message.pk)
        return message
    try:
        send_notification(message, recipient)
    except Exception as error:  # SMTP indisponible, adresse refusée… : le message reste enregistré
        message.email_error = f"{type(error).__name__}: {error}"[:250]
        message.save(update_fields=["email_error"])
        logger.exception("Contact form: message %s saved but email failed", message.pk)
    else:
        message.emailed_at = timezone.now()
        message.save(update_fields=["emailed_at"])
    return message
