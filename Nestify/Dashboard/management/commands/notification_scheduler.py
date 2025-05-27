import os
import time
import schedule
import threading
import tempfile
from django.core.management.base import BaseCommand
from django.utils import timezone
from Inventory.models import ItemOperation
from Family.models import Notification, FamilySettings

task_locks = {
    "run_notification_task_safely": threading.Lock(),
}

TEMP_DIR = tempfile.gettempdir()

class Command(BaseCommand):
    help = 'Run notification scheduled tasks'

    def handle(self, *args, **options):
        # Ensure single instance with a lock file
        if not self.ensure_single_instance():
            self.stdout.write(self.style.WARNING(
                "Another instance is already running. Exiting."))
            return

        self.stdout.write(self.style.SUCCESS(
            "Starting notification scheduler..."))

        # Schedule tasks directly in the main thread
        schedule.every(5).minutes.do(self.run_notification_task_safely)

        # Keep this management command alive
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS(
                "Stopping notification scheduler..."))
            flag_file = os.path.join(TEMP_DIR, 'django_scheduler_started.flag')
            try:
                if os.path.exists(flag_file):
                    os.remove(flag_file)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error removing flag file: {e}"))

    def ensure_single_instance(self):
        """
        Creates a PID file so that only one instance of this command can run at a time.
        Adjust for your environment if checking /proc/<pid> is not reliable.
        """
        lock_file = os.path.join(TEMP_DIR, 'django_task_scheduler.lock')
        try:
            if os.path.exists(lock_file):
                with open(lock_file, 'r') as f:
                    pid = int(f.read())
                if os.name != 'nt' and os.path.exists(f"/proc/{pid}"):
                    return False
                else:
                    os.remove(lock_file)
            with open(lock_file, 'w') as f:
                f.write(str(os.getpid()))
            return True
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f"Error creating lock file: {e}"))
            return False

    def run_notification_task_safely(self):
        """
        Thread-safe wrapper for the notification task
        """
        lock = task_locks.get("run_notification_task_safely")
        if lock and lock.acquire(blocking=False):
            try:
                self.stdout.write(self.style.SUCCESS(
                    "Executing notification task..."))
                self.notification_task()
            finally:
                lock.release()
        else:
            self.stdout.write(self.style.WARNING(
                "Task is already running, skipping."))

    def notification_task(self):
        """
        Check for expiring items and create notifications
        """
        today = timezone.now().date()

        items = ItemOperation.objects.filter(exp_date__isnull=False)

        for item in items:
            family = item.item.family
            settings = FamilySettings.get_or_create_settings(family)
            recipients = settings.get_notification_recipients('inventory')

            if not recipients:
                continue

            days_until_expiry = (item.exp_date - today).days

            if days_until_expiry < 0:
                if not Notification.objects.filter(
                    family=family,
                    notification_type='inventory_expired',
                    related_object_id=item.id
                ).exists():
                    for recipient in recipients:
                        Notification.create_notification(
                            family=family,
                            recipient=recipient,
                            notification_type='inventory_expired',
                            title=f'Produktas pasibaigė: {item.item.name}',
                            message=f'{item.item.name} ({item.qty} vnt.) galiojimas baigėsi.',
                            related_object_id=item.id)

            elif days_until_expiry <= 3 and days_until_expiry > 1:
                if not Notification.objects.filter(
                    family=family,
                    notification_type='inventory_expiring',
                    related_object_id=item.id
                ).exists():
                    for recipient in recipients:
                        Notification.create_notification(
                            family=family,
                            recipient=recipient,
                            notification_type='inventory_expiring',
                            title=f'Produktas baigiasi: {item.item.name}',
                            message=f'{item.item.name} ({item.qty} vnt.) galiojimo laikas baigsis po {days_until_expiry} dienų.',
                            related_object_id=item.id)

            elif days_until_expiry == 1:
                if not Notification.objects.filter(
                    family=family,
                    notification_type='inventory_expiring',
                    related_object_id=item.id
                ).exists():
                    for recipient in recipients:
                        Notification.create_notification(
                            family=family,
                            recipient=recipient,
                            notification_type='inventory_expiring',
                            title=f'Produktas baigiasi: {item.item.name}',
                            message=f'{item.item.name} ({item.qty} vnt.) galiojimo laikas baigsis rytoj.',
                            related_object_id=item.id)
                    self.stdout.write(self.style.WARNING(
                        f"Created 1-day notification for {item.item.name}"))
