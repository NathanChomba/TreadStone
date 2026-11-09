"""In-app notifications, with an SMS copy through Africa's Talking.

Every service that used to call `queue_sms` directly now calls `notify`, so the
bell in the app and the SMS always say the same thing.
"""

from integrations.sms import queue_sms

from .models import Notification


def notify(member, *, kind, title, body, link="", sms=True):
    note = Notification.objects.create(member=member, kind=kind, title=title, body=body, link=link)
    if sms:
        queue_sms(member.default_wallet_number(), f"Treadstone: {body}")
    return note
