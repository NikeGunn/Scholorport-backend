import logging
from uuid import UUID

from django.conf import settings
from django.core.mail import EmailMessage
from django.db import transaction

from .models import ContactSubmission


logger = logging.getLogger(__name__)



@transaction.atomic
def deliver_contact_email(submission_id: UUID) -> bool:
    # Lock the row so a scheduled retry and the API cannot both send it.
    submission = ContactSubmission.objects.select_for_update().filter(
        pk=submission_id, email_notification_pending=True,
    ).first()
    if submission is None:
        return True

    if not settings.DEFAULT_FROM_EMAIL:
        logger.error('Contact email sender is unconfigured. Inquiry %s is pending.', submission_id)
        return False

    email = EmailMessage(
        subject=f'ScholarPort website inquiry: {submission.get_type_display()}',
        body='\n'.join([
            f'Name: {submission.name}',
            f'Email: {submission.email}',
            f'Phone: {submission.phone or "Not provided"}',
            f'Inquiry type: {submission.get_type_display()}',
            f'Inquiry ID: {submission_id}',
            '',
            submission.message,
        ]),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.CONTACT_INBOX],
        reply_to=[submission.email],
    )

    try:
        sent = email.send()
    except (OSError, ValueError) as error:
        logger.error('Contact email failed for inquiry %s (%s).', submission_id, type(error).__name__)
        return False

    if not sent:
        logger.error('Mail backend did not send contact inquiry %s.', submission_id)
        return False

    submission.email_notification_pending = False
    submission.save(update_fields=['email_notification_pending'])
    return True
