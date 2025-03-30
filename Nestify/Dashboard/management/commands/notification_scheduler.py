import os
import time
import schedule
import threading
from django.core.management.base import BaseCommand
from django.utils import timezone
from Inventory.models import ItemOperation
from Family.models import Notification

# Define locks for thread-safe task execution
task_locks = {
    "run_notification_task_safely": threading.Lock(),
}

class Command(BaseCommand):
    help = 'Run notification scheduled tasks'

    def handle(self, *args, **options):
        # Ensure single instance with a lock file
        if not self.ensure_single_instance():
            self.stdout.write(self.style.WARNING("Another instance is already running. Exiting."))
            return

        self.stdout.write(self.style.SUCCESS("Starting notification scheduler..."))
        
        # Schedule tasks directly in the main thread
        schedule.every(5).minutes.do(self.run_notification_task_safely)

        # Keep this management command alive
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS("Stopping notification scheduler..."))
            # Clean up the flag file
            flag_file = '/tmp/django_scheduler_started.flag' if os.name != 'nt' else 'django_scheduler_started.flag'
            try:
                if os.path.exists(flag_file):
                    os.remove(flag_file)
            except Exception:
                pass

    def ensure_single_instance(self):
        """
        Creates a PID file so that only one instance of this command can run at a time.
        Adjust for your environment if checking /proc/<pid> is not reliable.
        """
        lock_file = '/tmp/django_task_scheduler.lock' if os.name != 'nt' else 'django_task_scheduler.lock'
        try:
            if os.path.exists(lock_file):
                # If the file exists, check if the process is alive
                with open(lock_file, 'r') as f:
                    pid = int(f.read())
                # On Unix-based systems, /proc/<pid> will exist if process is alive
                if os.name != 'nt' and os.path.exists(f"/proc/{pid}"):
                    return False
                else:
                    os.remove(lock_file)
            # Create or overwrite the lock file with the current process ID
            with open(lock_file, 'w') as f:
                f.write(str(os.getpid()))
            return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error creating lock file: {e}"))
            return False

    def run_notification_task_safely(self):
        """
        Thread-safe wrapper for the notification task
        """
        lock = task_locks.get("run_notification_task_safely")
        if lock and lock.acquire(blocking=False):
            try:
                self.stdout.write(self.style.SUCCESS("Executing notification task..."))
                self.notification_task()
            finally:
                lock.release()
        else:
            self.stdout.write(self.style.WARNING("Task is already running, skipping."))

    def notification_task(self):
        """
        Check for expiring items and create notifications
        """
        today = timezone.now().date()

        # Get all items with expiration dates
        items = ItemOperation.objects.filter(exp_date__isnull=False)

        for item in items:
            family = item.item.family
            days_until_expiry = (item.exp_date - today).days

            # Skip if already expired
            if days_until_expiry < 0:
                # Check if we already notified about this expired item
                if not Notification.objects.filter(
                    family=family,
                    notification_type='inventory_expired',
                    related_object_id=item.id
                ).exists():
                    Notification.create_notification(
                        family=family,
                        recipient=family.creator,  # Notify family creator
                        notification_type='inventory_expired',
                        title=f'Produktas pasibaigė: {item.item.name}',
                        message=f'{item.item.name} ({item.qty} vnt.) galiojimo laikas baigėsi {abs(days_until_expiry)} dienų atgal.',
                        related_object_id=item.id
                    )

            # Check for items expiring in 3 days
            elif days_until_expiry <= 3 or days_until_expiry > 1:
                if not Notification.objects.filter(
                    family=family,
                    notification_type='inventory_expiring',
                    related_object_id=item.id
                ).exists():
                    Notification.create_notification(
                        family=family,
                        recipient=family.creator,
                        notification_type='inventory_expiring',
                        title=f'Produktas baigiasi: {item.item.name}',
                        message=f'{item.item.name} ({item.qty} vnt.) galiojimo laikas baigsis po 3 dienų.',
                        related_object_id=item.id
                    )

            # Check for items expiring in 1 day
            elif days_until_expiry == 1:
                if not Notification.objects.filter(
                    family=family,
                    notification_type='inventory_expiring',
                    related_object_id=item.id
                ).exists():
                    Notification.create_notification(
                        family=family,
                        recipient=family.creator,
                        notification_type='inventory_expiring',
                        title=f'Produktas baigiasi: {item.item.name}',
                        message=f'{item.item.name} ({item.qty} vnt.) galiojimo laikas baigsis rytoj.',
                        related_object_id=item.id
                    )
                    self.stdout.write(self.style.WARNING(f"Created 1-day notification for {item.item.name}"))
