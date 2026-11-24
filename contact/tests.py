from io import StringIO
from smtplib import SMTPAuthenticationError
from unittest.mock import patch

from django.core import mail
from django.core.management import call_command
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from .models import ContactSubmission


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='website@example.com',
    CONTACT_INBOX='contact@example.com',
)
class ContactEmailTests(APITestCase):
    def setUp(self):
        self.url = reverse('contact:submit-contact')
        self.inquiry = {
            'name': 'Sample Visitor',
            'email': 'visitor@example.com',
            'phone': '+44 1234 567890',
            'message': 'Please share details about university admissions.',
            'type': 'university',
        }

    def test_valid_submission_persists_and_emails_inbox(self):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(self.url, self.inquiry, format='json')

        self.assertEqual(response.status_code, 201)
        submission = ContactSubmission.objects.get(pk=response.data['data']['id'])
        self.assertFalse(submission.email_notification_pending)
        self.assertEqual(len(mail.outbox), 1)
        notification = mail.outbox[0]
        self.assertEqual(notification.to, ['contact@example.com'])
        self.assertEqual(notification.from_email, 'website@example.com')
        self.assertEqual(notification.reply_to, [self.inquiry['email']])
        self.assertIn('University', notification.subject)
        for line in (
            f"Name: {self.inquiry['name']}",
            f"Email: {self.inquiry['email']}",
            f"Phone: {self.inquiry['phone']}",
            'Inquiry type: University',
            f'Inquiry ID: {submission.pk}',
            self.inquiry['message'],
        ):
            self.assertIn(line, notification.body)

    def test_invalid_submission_does_not_save_or_send(self):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(self.url, {**self.inquiry, 'email': 'invalid'}, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertFalse(ContactSubmission.objects.exists())
        self.assertEqual(mail.outbox, [])

    def test_smtp_failure_preserves_inquiry_and_retry_sends_once(self):
        with patch.object(mail.EmailMessage, 'send', side_effect=SMTPAuthenticationError(535, b'denied')):
            with self.assertLogs('contact.notifications', level='ERROR') as logs:
                with self.captureOnCommitCallbacks(execute=True):
                    response = self.client.post(self.url, self.inquiry, format='json')

        self.assertEqual(response.status_code, 201)
        submission = ContactSubmission.objects.get(pk=response.data['data']['id'])
        self.assertTrue(submission.email_notification_pending)
        self.assertIn(str(submission.pk), logs.output[0])
        self.assertNotIn(self.inquiry['email'], logs.output[0])
        self.assertEqual(mail.outbox, [])

        # The retry only picks up records that were queued for email delivery.
        ContactSubmission.objects.create(**self.inquiry)
        call_command('retry_contact_emails', stdout=StringIO())
        call_command('retry_contact_emails', stdout=StringIO())
        submission.refresh_from_db()
        self.assertFalse(submission.email_notification_pending)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(str(submission.pk), mail.outbox[0].body)
