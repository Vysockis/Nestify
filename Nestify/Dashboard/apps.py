from django.apps import AppConfig
import threading
from django.core.management import call_command
import sys
import os
import tempfile

TEMP_DIR = tempfile.gettempdir()

def is_scheduler_running():
    """Check if scheduler is already running using a file-based flag"""
    flag_file = os.path.join(TEMP_DIR, 'django_scheduler_started.flag')
    try:
        if os.path.exists(flag_file):
            with open(flag_file, 'r') as f:
                pid = int(f.read())
            # On Unix-based systems, check if process is alive
            if os.name != 'nt' and os.path.exists(f"/proc/{pid}"):
                return True
            else:
                os.remove(flag_file)
        return False
    except Exception as e:
        print(f"Error checking scheduler status: {e}")
        return False


def mark_scheduler_running():
    """Mark scheduler as running using a file-based flag"""
    flag_file = os.path.join(TEMP_DIR, 'django_scheduler_started.flag')
    try:
        with open(flag_file, 'w') as f:
            f.write(str(os.getpid()))
        return True
    except Exception as e:
        print(f"Error marking scheduler as running: {e}")
        return False


class DashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Dashboard'

    def ready(self):
        # Only start the scheduler when running as a server, not when running
        # management commands
        if 'runserver' in sys.argv and not is_scheduler_running():
            # Start the scheduler when the server starts
            thread = threading.Thread(
                target=call_command, args=(
                    'notification_scheduler',))
            thread.daemon = True
            thread.start()
            mark_scheduler_running()
