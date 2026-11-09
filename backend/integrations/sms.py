"""SMS through Africa's Talking.

With no AT_API_KEY set, messages are printed to the log instead of sent.
Call `queue_sms` from request code so sending happens on the Django-Q worker.
"""

import json
import logging
import urllib.parse
import urllib.request

from django.conf import settings

logger = logging.getLogger("treadstone.sms")

SANDBOX_URL = "https://api.sandbox.africastalking.com/version1/messaging"
LIVE_URL = "https://api.africastalking.com/version1/messaging"


def send_sms(phone: str, message: str) -> bool:
    if not settings.AT_API_KEY:
        logger.info("SMS (console) to %s: %s", phone, message)
        return True

    url = SANDBOX_URL if settings.AT_USERNAME == "sandbox" else LIVE_URL
    data = {"username": settings.AT_USERNAME, "to": phone, "message": message}
    if settings.AT_SENDER_ID:
        data["from"] = settings.AT_SENDER_ID
    req = urllib.request.Request(
        url,
        data=urllib.parse.urlencode(data).encode(),
        headers={
            "apiKey": settings.AT_API_KEY,
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read())
        logger.info("SMS sent to %s: %s", phone, body)
        return True
    except Exception:
        logger.exception("SMS to %s failed", phone)
        return False


def queue_sms(phone: str, message: str):
    """Send on the background worker so a slow SMS gateway never blocks a request."""
    from django_q.tasks import async_task

    async_task("integrations.sms.send_sms", phone, message)
