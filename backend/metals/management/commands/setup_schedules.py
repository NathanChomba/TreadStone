from datetime import datetime, time, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django_q.models import Schedule


class Command(BaseCommand):
    help = "Create or update the Django-Q2 schedules (safe to run repeatedly)."

    def handle(self, *args, **options):
        Schedule.objects.update_or_create(
            name="fetch-metal-prices",
            defaults={
                "func": "metals.tasks.fetch_prices",
                "schedule_type": Schedule.MINUTES,
                "minutes": 15,
                "repeats": -1,
            },
        )
        # 06:00 Lusaka time every day: buy gold for groups whose due date has come, then send reminders.
        now = timezone.localtime()
        six = timezone.make_aware(datetime.combine(now.date(), time(6, 0)))
        if six <= now:
            six += timedelta(days=1)
        Schedule.objects.update_or_create(
            name="daily-savings",
            defaults={
                "func": "savings.tasks.daily",
                "schedule_type": Schedule.DAILY,
                "repeats": -1,
                "next_run": six,
            },
        )
        self.stdout.write(self.style.SUCCESS("Schedules: fetch-metal-prices every 15 min, daily-savings at 06:00"))
