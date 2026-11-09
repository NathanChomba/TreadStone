"""Django-Q2 tasks for metal prices. Scheduled by `manage.py setup_schedules`."""

import logging
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from .history import change_since
from .models import Metal
from .prices import fetch_and_store

logger = logging.getLogger("treadstone.prices")

ALERT_PERCENT = Decimal("3")


def fetch_prices():
    stored = []
    for metal in Metal.values:
        try:
            stored.append(str(fetch_and_store(metal)))
        except Exception:
            logger.exception("Price fetch failed for %s", metal)
    try:
        send_price_alerts()
    except Exception:
        logger.exception("Price alerts failed")
    return stored


def send_price_alerts():
    """Tell members who opted in when gold moves 3% or more in a day (at most once a day each)."""
    from members.models import Member, Notification
    from members.notify import notify

    move = change_since(Metal.GOLD, hours=24)
    if move is None or abs(move) < ALERT_PERCENT:
        return 0
    direction = "up" if move > 0 else "down"
    pct = f"{abs(move):.1f}"
    since = timezone.now() - timedelta(hours=24)
    sent = 0
    for member in Member.objects.filter(price_alerts=True, is_active=True):
        if member.notifications.filter(kind=Notification.Kind.PRICE, created_at__gte=since).exists():
            continue
        notify(member, kind=Notification.Kind.PRICE, title=f"Gold is {direction} {pct}% today",
               body=f"Gold is {direction} {pct}% in the last 24 hours. Your savings in gold move with it.",
               link="/vault")
        sent += 1
    return sent
