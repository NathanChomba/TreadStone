from decimal import Decimal

from django.db import transaction
from django.db.models import Sum

from config.errors import DomainError
from integrations import mobile_money
from members.models import Notification
from members.notify import notify
from loans.services import available_grams
from metals import custodian
from savings.models import Contribution, SavingsGroup
from savings import dues
from savings.services import cycle_status

from .models import Payout


class PayoutError(DomainError):
    pass


def _disburse_or_fail(member, amount, description):
    result = mobile_money.get_provider().disburse(member.default_wallet_number(), amount, description)
    if not result.success:
        # Raising inside the atomic block rolls back the custodian sale too.
        raise PayoutError(f"Disbursement failed: {result.message}")
    return result.reference


@transaction.atomic
def run_rotation_payout(*, group, by):
    """Pay the current cycle's pot to the member whose turn it is, then advance the cycle."""
    group = SavingsGroup.objects.select_for_update().get(pk=group.pk)
    if not group.is_rotating:
        raise PayoutError("Rotation payouts only apply to rotating groups")
    if group.status != SavingsGroup.Status.ACTIVE:
        raise PayoutError("The group is not active")
    if not group.memberships.filter(member=by, is_admin=True).exists():
        raise PayoutError("Only a group admin can run the payout")

    status = cycle_status(group)
    if status["unpaid"]:
        names = ", ".join(m.member.get_full_name() or m.member.phone for m in status["unpaid"])
        raise PayoutError(f"Still waiting on contributions from: {names}")
    if status["awaiting_gold"]:
        raise PayoutError(
            f"This cycle's gold is bought on {dues.next_due(group):%a %d %b}. The pot can be paid out after that."
        )
    recipient = status["recipient"]

    pot = Contribution.objects.filter(
        group=group, cycle=group.current_cycle, status=Contribution.Status.COMPLETED
    ).aggregate(g=Sum("custodian_transaction__grams"))["g"] or Decimal("0")
    if pot <= 0:
        raise PayoutError("Nothing to pay out this cycle")

    txn = custodian.sell(group=group, member=recipient.member, grams=pot)
    net = txn.gross_zmw - txn.fee_zmw
    ref = _disburse_or_fail(recipient.member, net, f"Treadstone {group.name} cycle {group.current_cycle}")
    payout = Payout.objects.create(
        group=group, member=recipient.member, kind=Payout.Kind.ROTATION, cycle=group.current_cycle,
        grams=pot, amount_zmw=net, payment_reference=ref, custodian_transaction=txn,
    )

    if group.current_cycle >= group.memberships.count():
        group.status = SavingsGroup.Status.CLOSED
    else:
        group.current_cycle += 1
    group.save(update_fields=["current_cycle", "status"])

    notify(recipient.member, kind=Notification.Kind.PAYOUT, title=f"Your {group.name} payout: K{net}",
           body=f"Your {group.name} payout of K{net} ({pot}g sold) has been sent to {recipient.member.default_wallet_number()}.",
           link="/ledger")
    return payout


@transaction.atomic
def withdraw(*, member, group, grams):
    """Annuity withdrawal: sell some of the member's own metal and pay them in ZMW."""
    grams = Decimal(grams).quantize(Decimal("0.0001"))
    if group.is_rotating:
        raise PayoutError("Rotating groups pay out by turn, not by withdrawal")
    if not group.memberships.filter(member=member).exists():
        raise PayoutError("You are not a member of this group")
    if grams <= 0:
        raise PayoutError("Grams must be positive")
    available = available_grams(member, group)
    if grams > available:
        raise PayoutError(f"You can withdraw at most {available}g (some may be locked as loan collateral)")

    txn = custodian.sell(group=group, member=member, grams=grams)
    net = txn.gross_zmw - txn.fee_zmw
    ref = _disburse_or_fail(member, net, f"Treadstone {group.name} withdrawal")
    payout = Payout.objects.create(
        group=group, member=member, kind=Payout.Kind.WITHDRAWAL,
        grams=grams, amount_zmw=net, payment_reference=ref, custodian_transaction=txn,
    )
    notify(member, kind=Notification.Kind.PAYOUT, title=f"Withdrawal: K{net}",
           body=f"{grams}g sold for K{net} and sent to {member.default_wallet_number()}.", link="/ledger")
    return payout
