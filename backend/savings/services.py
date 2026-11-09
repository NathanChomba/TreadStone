"""Business rules for savings groups and contributions.

Views stay thin and call these functions; tests exercise them directly.

Money flow: a contribution is collected by mobile money straight away and marked
RECEIVED. The group's received money is pooled and turned into metal once, on the
group's due date (`buy_due_gold`), at that day's price. Until then the app shows
an estimate.
"""

import random
import uuid
from decimal import Decimal

from django.db import transaction
from django.db.models import Max, Sum

from config.errors import DomainError
from integrations import mobile_money
from members.models import Notification
from members.notify import notify
from metals import custodian
from metals.prices import latest_price

from . import dues
from .models import Contribution, Membership, SavingsGroup


class SavingsError(DomainError):
    pass


def _receipt_reference():
    """TS-yymm-dd-nnnn, the receipt number shown to members."""
    d = dues.today()
    for _ in range(20):
        ref = f"TS-{d:%y%m}-{d:%d}-{random.randint(0, 9999):04d}"
        if not Contribution.objects.filter(reference=ref).exists():
            return ref
    return f"TS-{d:%y%m}-{d:%d}-{uuid.uuid4().hex[:6].upper()}"


@transaction.atomic
def create_group(*, creator, **fields):
    group = SavingsGroup.objects.create(created_by=creator, **fields)
    if group.group_type == SavingsGroup.Type.ANNUITY:
        group.status = SavingsGroup.Status.ACTIVE
        group.started_at = dues.today()
        group.save(update_fields=["status", "started_at"])
    Membership.objects.create(group=group, member=creator, position=1, is_admin=True)
    return group


@transaction.atomic
def join_group(*, member, invite_code):
    try:
        group = SavingsGroup.objects.select_for_update().get(invite_code=invite_code.strip().upper())
    except SavingsGroup.DoesNotExist:
        raise SavingsError("No group has that invite code") from None
    if group.status == SavingsGroup.Status.CLOSED:
        raise SavingsError("This group is closed")
    if group.is_rotating and group.status != SavingsGroup.Status.OPEN:
        raise SavingsError("This rotating group has already started")
    if group.memberships.filter(member=member).exists():
        raise SavingsError("You are already in this group")
    if group.memberships.count() >= group.max_members:
        raise SavingsError("This group is full")
    last = group.memberships.aggregate(p=Max("position"))["p"] or 0
    return Membership.objects.create(group=group, member=member, position=last + 1)


@transaction.atomic
def start_group(*, group, by):
    group = SavingsGroup.objects.select_for_update().get(pk=group.pk)
    if not group.memberships.filter(member=by, is_admin=True).exists():
        raise SavingsError("Only a group admin can start the group")
    if group.status != SavingsGroup.Status.OPEN:
        raise SavingsError("The group is not open")
    if group.memberships.count() < 2:
        raise SavingsError("A group needs at least two members to start")
    group.status = SavingsGroup.Status.ACTIVE
    group.started_at = dues.today()
    group.save(update_fields=["status", "started_at"])
    for ms in group.memberships.select_related("member").exclude(member=by):
        notify(ms.member, kind=Notification.Kind.GROUP, title=f"{group.name} has started",
               body=f"{group.name} has started. Your first K{group.contribution_amount} is due {dues.next_due(group):%a %d %b}.",
               link=f"/groups/{group.pk}")
    return group


def paid_this_period(group, member):
    """Has the member paid for the period in progress (rotating: this cycle)?"""
    qs = group.contributions.filter(member=member, status__in=Contribution.PAID)
    if group.is_rotating:
        return qs.filter(cycle=group.current_cycle).exists()
    return qs.filter(created_at__date__gte=dues.period_start(group)).exists()


def _wallet_for(member, wallet_id):
    if wallet_id:
        wallet = member.wallets.filter(pk=wallet_id).first()
        if wallet is None:
            raise SavingsError("That mobile money number isn't on your account")
        return wallet.provider, wallet.number
    wallet = member.wallets.filter(is_default=True).first()
    if wallet:
        return wallet.provider, wallet.number
    from members.models import provider_for

    return provider_for(member.phone), member.phone


def contribute(*, member, group, amount, wallet_id=None):
    """Collect ZMW by mobile money and hold it until the due date's gold purchase.

    Requires a live connection; the PWA never queues this offline.
    """
    amount = Decimal(amount).quantize(Decimal("0.01"))
    if not group.memberships.filter(member=member).exists():
        raise SavingsError("You are not a member of this group")
    if group.status != SavingsGroup.Status.ACTIVE:
        raise SavingsError("The group is not active")
    if group.is_rotating:
        if amount != group.contribution_amount:
            raise SavingsError(f"This group's contribution is exactly K{group.contribution_amount}")
        if paid_this_period(group, member):
            raise SavingsError("You have already contributed for this cycle")
    elif amount < group.contribution_amount:
        raise SavingsError(f"The minimum deposit is K{group.contribution_amount}")

    provider, number = _wallet_for(member, wallet_id)
    contribution = Contribution.objects.create(
        group=group, member=member, cycle=group.current_cycle, amount=amount,
        provider=provider, wallet_number=number,
    )

    result = mobile_money.get_provider().collect(number, amount, f"Treadstone: {group.name}")
    if not result.success:
        contribution.status = Contribution.Status.FAILED
        contribution.failure_reason = result.message
        contribution.save(update_fields=["status", "failure_reason"])
        raise SavingsError(f"Payment failed: {result.message}")

    contribution.status = Contribution.Status.RECEIVED
    contribution.payment_reference = result.reference
    contribution.reference = _receipt_reference()
    contribution.save(update_fields=["status", "payment_reference", "reference"])

    buy_on = dues.next_due(group)
    est, _, _ = custodian.quote(group.metal, amount)
    notify(member, kind=Notification.Kind.PAYMENT, title=f"K{amount} received for {group.name}",
           body=f"K{amount} received for {group.name} (ref {contribution.reference}). "
                f"About {est}g {group.get_metal_display().lower()} will be bought on {buy_on:%d %b} at that day's price.",
           link=f"/groups/{group.pk}")
    return contribution


@transaction.atomic
def buy_gold_for_group(group, *, upto=None):
    """Pool every RECEIVED contribution and buy metal for all of them at one price.

    `upto`: only contributions received on or before this date (the due date).
    Returns the number of contributions bought for.
    """
    group = SavingsGroup.objects.select_for_update().get(pk=group.pk)
    pending = group.contributions.filter(status=Contribution.Status.RECEIVED).select_related("member")
    if upto:
        pending = pending.filter(created_at__date__lte=upto)
    pending = list(pending)
    if not pending:
        return 0
    price = latest_price(group.metal)
    batch = f"ZGCL-B-{uuid.uuid4().hex[:8].upper()}"
    for c in pending:
        txn = custodian.buy(group=group, member=c.member, amount_zmw=c.amount, price=price, batch=batch)
        c.status = Contribution.Status.COMPLETED
        c.custodian_transaction = txn
        c.save(update_fields=["status", "custodian_transaction"])
        notify(c.member, kind=Notification.Kind.GOLD, title=f"Gold bought for {group.name}",
               body=f"{txn.grams}g {group.get_metal_display().lower()} bought for your K{c.amount} in {group.name} "
                    f"at K{price.price_per_gram}/g (ref {txn.reference}).",
               link=f"/groups/{group.pk}", sms=False)
    return len(pending)


def buy_due_gold(on=None):
    """Daily job: buy metal for every group whose due date has arrived."""
    on = on or dues.today()
    bought = 0
    for group in SavingsGroup.objects.filter(status=SavingsGroup.Status.ACTIVE):
        due = dues.last_due(group, on)
        if group.contributions.filter(status=Contribution.Status.RECEIVED, created_at__date__lte=due).exists():
            bought += buy_gold_for_group(group, upto=due)
    return bought


def unpaid_members(group):
    return [ms for ms in group.memberships.select_related("member") if not paid_this_period(group, ms.member)]


def remind(*, group, by=None, member_ids=None, automatic=False):
    """SMS + notification to members who haven't paid this period. Returns who was reminded."""
    if by is not None and not group.memberships.filter(member=by, is_admin=True).exists():
        raise SavingsError("Only a group admin can send reminders")
    if group.status != SavingsGroup.Status.ACTIVE:
        raise SavingsError("The group is not active")
    due = dues.next_due(group)
    sent = []
    for ms in unpaid_members(group):
        m = ms.member
        if member_ids and m.pk not in member_ids:
            continue
        if automatic and not m.sms_reminders:
            continue
        notify(m, kind=Notification.Kind.REMINDER, title=f"K{group.contribution_amount} due {due:%a %d %b}",
               body=f"Your K{group.contribution_amount} for {group.name} is due {due:%a %d %b}. Pay in the app.",
               link=f"/contribute/{group.pk}")
        sent.append(m)
    return sent


def send_due_reminders(on=None):
    """Daily job: remind unpaid members two days before each due date."""
    on = on or dues.today()
    total = 0
    for group in SavingsGroup.objects.filter(status=SavingsGroup.Status.ACTIVE):
        if (dues.next_due(group, on) - on).days == 2:
            total += len(remind(group=group, automatic=True))
    return total


def cycle_status(group):
    """Who has and hasn't paid in the current cycle of a rotating group."""
    paid_ids = set(
        group.contributions.filter(cycle=group.current_cycle, status__in=Contribution.PAID)
        .values_list("member_id", flat=True)
    )
    memberships = list(group.memberships.select_related("member"))
    awaiting_gold = group.contributions.filter(cycle=group.current_cycle, status=Contribution.Status.RECEIVED).exists()
    return {
        "cycle": group.current_cycle,
        "paid": [m for m in memberships if m.member_id in paid_ids],
        "unpaid": [m for m in memberships if m.member_id not in paid_ids],
        "recipient": next((m for m in memberships if m.position == group.current_cycle), None),
        "awaiting_gold": awaiting_gold,
    }


def received_total(group, member=None):
    qs = group.contributions.filter(status=Contribution.Status.RECEIVED)
    if member is not None:
        qs = qs.filter(member=member)
    return qs.aggregate(s=Sum("amount"))["s"] or Decimal("0.00")

