import os
import sys
import logging
from django.apps import AppConfig

logger = logging.getLogger(__name__)

class StaffManagementConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "staff_management"

    def ready(self):
        # 1. Import signals (This must be indented 8 spaces total)
        import staff_management.signals  # noqa

        # 2. Block scheduler for management commands
        blocked_commands = {
            "makemigrations",
            "migrate",
            "collectstatic",
            "shell",
            "createsuperuser",
        }

        if any(cmd in sys.argv for cmd in blocked_commands):
            return

        # 3. Only run scheduler in the main thread
        if os.environ.get("RUN_MAIN") != "true":
            return

        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from django_apscheduler.jobstores import DjangoJobStore
            from staff_management.scheduler_jobs import fetch_website_bookings_job
            from staff_management.jobs import send_due_checkin_reminders

            scheduler = BackgroundScheduler(timezone="Asia/Kolkata")
            scheduler.add_jobstore(DjangoJobStore(), "default")

            scheduler.add_job(
                fetch_website_bookings_job,
                trigger="interval",
                minutes=5,
                id="fetch_website_bookings",
                replace_existing=True,
            )

            scheduler.add_job(
                send_due_checkin_reminders,
                trigger="interval",
                minutes=5,
                id="checkin_reminders",
                replace_existing=True,
            )

            scheduler.start()
            logger.info("🚀 Background scheduler started successfully")

        except Exception as e:
            logger.error(f"❌ Failed to start scheduler: {str(e)}")

# import os
# import sys
# from django.apps import AppConfig


# class StaffManagementConfig(AppConfig):
#     default_auto_field = "django.db.models.BigAutoField"
#     name = "staff_management"

#     def ready(self):
#         import staff_management.signals  # noqa

#         blocked_commands = {
#             "makemigrations",
#             "migrate",
#             "collectstatic",
#             "shell",
#             "createsuperuser",
#         }

#         if any(cmd in sys.argv for cmd in blocked_commands):
#             return

#         if os.environ.get("RUN_MAIN") != "true":
#             return

#         from apscheduler.schedulers.background import BackgroundScheduler
#         from django_apscheduler.jobstores import DjangoJobStore
#         from staff_management.scheduler_jobs import fetch_website_bookings_job
#         from staff_management.jobs import send_due_checkin_reminders

#         scheduler = BackgroundScheduler(timezone="Asia/Kolkata")
#         scheduler.add_jobstore(DjangoJobStore(), "default")

#         scheduler.add_job(
#             fetch_website_bookings_job,
#             trigger="interval",
#             minutes=5,
#             id="fetch_website_bookings",
#             replace_existing=True,
#         )

#         scheduler.add_job(
#             send_due_checkin_reminders,
#             trigger="interval",
#             minutes=5,
#             id="checkin_reminders",
#             replace_existing=True,
#         )

#         scheduler.start()
