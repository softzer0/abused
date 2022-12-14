from django.core.management.base import BaseCommand
from django.utils import timezone
from member import models


class Command(BaseCommand):
    help = "Cleans piled up inactive users, sessions and expired blocks from the database"

    def add_arguments(self, parser):
        parser.add_argument('--session_minimum_days_old', '-s', type=int, default=30, help="Remove all sessions older than X days.")
        parser.add_argument('--user_minimum_days_inactive', '-u', type=int, default=60, help="Remove all generated users which are inactive more than X days.")

    def handle(self, *args, **options):
        self.stdout.write("Cleaning blocklist...")
        deleted_count = models.Blocklist.objects.filter(expires__lte=timezone.now()).delete()[0]
        self.stdout.write("Cleaning users...")
        deleted_count += models.User.objects.filter(blocklist=None, is_password_custom=False, last_login__lte=timezone.now() - timezone.timedelta(days=options['user_minimum_days_inactive'])).delete()[0]
        self.stdout.write("Cleaning sessions...")
        deleted_count += models.Session.objects.filter(blocklist=None, created__lte=timezone.now() - timezone.timedelta(days=options['session_minimum_days_old'])).delete()[0]
        self.stdout.write(self.style.SUCCESS("Cleaned up %d entries from the database" % deleted_count) if deleted_count > 0 else "No entries have been cleaned")

