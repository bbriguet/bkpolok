import smtplib
from unittest import mock

import pytest
from django.core import mail
from django.test import Client
from django.urls import reverse

from apps.contact.models import ContactMessage
from apps.pages.models import ContactPage

pytestmark = pytest.mark.django_db

VALID = {
    "name": "Marie Curie",
    "email": "marie@example.org",
    "subject": "A question",
    "message": "Hello,\nCould we talk about a project?",
    "website": "",
}


@pytest.fixture
def contact_page(home, profile):
    page = home.add_child(instance=ContactPage(title="Contact", slug="contact"))
    page.save_revision().publish()
    return page


def test_get_renders_a_real_form_with_csrf_token(client, contact_page):
    response = client.get(contact_page.url)
    html = response.content.decode()

    assert response.status_code == 200
    assert '<form class="contact-form" method="post"' in html
    assert 'name="csrfmiddlewaretoken"' in html
    for field in ("name", "email", "subject", "message", "website"):
        assert f'name="{field}"' in html
    assert html.count("<h1") == 1


def test_valid_submission_is_saved_emailed_and_confirmed(client, contact_page, profile):
    response = client.post(contact_page.url, VALID)

    assert response.status_code == 302
    assert response.url == "/contact/thank-you/"
    saved = ContactMessage.objects.get()
    assert (saved.name, saved.email, saved.subject) == (
        "Marie Curie",
        "marie@example.org",
        "A question",
    )
    assert saved.message == VALID["message"]
    assert saved.emailed_at is not None and saved.email_error == ""

    (email,) = mail.outbox
    assert email.to == ["jane@example.ch"]  # e-mail du profil du site
    assert email.reply_to == ["marie@example.org"]
    assert email.subject == "[Website] A question"
    assert "Could we talk about a project?" in email.body

    confirmation = client.get(response.url)
    html = confirmation.content.decode()
    assert confirmation.status_code == 200
    assert "<h1>Thank you</h1>" in html
    assert '<meta name="robots" content="noindex, follow">' in html


def test_page_email_overrides_the_profile_email(client, contact_page):
    contact_page.email = "office@example.ch"
    contact_page.save_revision().publish()

    client.post(contact_page.url, VALID)

    assert mail.outbox[0].to == ["office@example.ch"]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("name", ""),
        ("email", ""),
        ("email", "not-an-email"),
        ("subject", ""),
        ("subject", "Line one\nBcc: victim@example.org"),
        ("message", ""),
        ("message", "x" * 5001),
        ("name", "x" * 121),
    ],
)
def test_invalid_submission_is_rejected_with_errors(client, contact_page, field, value):
    response = client.post(contact_page.url, {**VALID, field: value})
    html = response.content.decode()

    assert response.status_code == 422
    assert 'class="form-error"' in html
    assert "could not be sent" in html
    assert f'id="id_{field}_error"' in html
    assert 'aria-invalid="true"' in html
    assert ContactMessage.objects.count() == 0
    assert mail.outbox == []


def test_rejected_form_keeps_what_was_typed(client, contact_page):
    response = client.post(contact_page.url, {**VALID, "email": "nope"})

    assert 'value="Marie Curie"' in response.content.decode()


def test_honeypot_submission_is_silently_dropped(client, contact_page):
    response = client.post(contact_page.url, {**VALID, "website": "https://spam.example"})

    assert response.status_code == 302  # le robot ne sait pas qu'il a été repéré
    assert ContactMessage.objects.count() == 0
    assert mail.outbox == []


def test_post_without_csrf_token_is_refused(contact_page):
    strict = Client(enforce_csrf_checks=True)

    response = strict.post(contact_page.url, VALID)

    assert response.status_code == 403
    assert ContactMessage.objects.count() == 0


def test_post_with_csrf_token_is_accepted(contact_page):
    strict = Client(enforce_csrf_checks=True)
    html = strict.get(contact_page.url).content.decode()
    token = html.split('name="csrfmiddlewaretoken" value="')[1].split('"')[0]

    response = strict.post(contact_page.url, {**VALID, "csrfmiddlewaretoken": token})

    assert response.status_code == 302
    assert ContactMessage.objects.count() == 1


def test_smtp_failure_keeps_the_message_and_still_confirms(client, contact_page):
    with mock.patch(
        "django.core.mail.EmailMessage.send", side_effect=smtplib.SMTPException("relay denied")
    ):
        response = client.post(contact_page.url, VALID)

    assert response.status_code == 302
    saved = ContactMessage.objects.get()
    assert saved.emailed_at is None
    assert "SMTPException: relay denied" in saved.email_error


def test_no_recipient_keeps_the_message_and_records_why(client, contact_page, profile):
    profile.email = ""
    profile.save()

    response = client.post(contact_page.url, VALID)

    assert response.status_code == 302
    assert ContactMessage.objects.get().email_error == "No recipient configured"
    assert mail.outbox == []


def test_thank_you_url_is_a_subpage_of_the_contact_page(contact_page):
    assert contact_page.url + contact_page.reverse_subpage("thank_you") == "/contact/thank-you/"


def test_messages_are_listed_in_the_admin(admin_client, contact_page, client):
    client.post(contact_page.url, VALID)

    response = admin_client.get(reverse("wagtailsnippets_contact_contactmessage:list"))

    assert response.status_code == 200
    assert "Marie Curie" in response.content.decode()
