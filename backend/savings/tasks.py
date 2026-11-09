"""Daily Django-Q2 job: buy the gold that's due, then send reminders."""

import logging

from .services import buy_due_gold, send_due_reminders

logger = logging.getLogger("treadstone.savings")


def daily():
    bought = buy_due_gold()
    reminded = send_due_reminders()
    logger.info("Daily savings job: gold bought for %s contributions, %s reminders sent", bought, reminded)
    return {"bought": bought, "reminded": reminded}
