from django.core.management.base import BaseCommand, CommandError

from contact.models import ContactSubmission
from contact.notifications import deliver_contact_email


class Command(BaseCommand):
    help = 'Retry up to 25 pending contact inquiry emails.'

    def handle(self, *args, **options):
        pending_ids = list(ContactSubmission.objects.filter(
            email_notification_pending=True,
        ).order_by('created_at', 'id').values_list('id', flat=True)[:25])

        failed = sum(not deliver_contact_email(submission_id) for submission_id in pending_ids)
        if failed:
            raise CommandError(f'{failed} contact email(s) still pending. See application logs.')

        self.stdout.write(f'Processed {len(pending_ids)} pending contact email(s).')
