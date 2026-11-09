from decimal import ROUND_DOWN, ROUND_UP, Decimal

from django.conf import settings
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from config.errors import DomainError
from integrations import mobile_money
from members.models import Notification
from members.notify import notify
from metals import custodian
from metals.prices import latest_price

from .models import Loan, LoanRepayment

TWO_DP = Decimal("0.01")
FOUR_DP = Decimal("0.0001")
LOCKING = [Loan.Status.PENDING, Loan.Status.ACTIVE]


class LoanError(DomainError):
    pass


def locked_grams(member, group):
    total = Loan.objects.filter(member=member, group=group, status__in=LOCKING).aggregate(
        g=Sum("collateral_grams")
    )["g"]
    return total or Decimal("0")


def available_grams(member, group):
    """Grams the member can withdraw or pledge: their balance minus locked collateral."""
    return max(Decimal("0"), custodian.member_grams(member, group) - locked_grams(member, group))


def max_loan(member, group):
    grams = available_grams(member, group)
    price = latest_price(group.metal).price_per_gram
    return (grams * price * settings.LOAN_TO_VALUE).quantize(TWO_DP, ROUND_DOWN)


@transaction.atomic
def request_loan(*, member, group, amount):
    amount = Decimal(amount).quantize(TWO_DP)
    if amount <= 0:
        raise LoanError("Amount must be positive")
    if not group.memberships.filter(member=member).exists():
        raise LoanError("You are not a member of this group")
    if group.is_rotating:
        # Every gram in a rotating group is destined for someone's pot, so none can be pledged.
        raise LoanError("Loans are only available against annuity group balances")
    if member.kyc_status != member.KYC.VERIFIED:
        raise LoanError("Your identity (KYC) must be verified before you can borrow")
    limit = max_loan(member, group)
    if amount > limit:
        raise LoanError(f"You can borrow at most K{limit} against your metal in this group")
    price = latest_price(group.metal).price_per_gram
    collateral = (amount / (price * settings.LOAN_TO_VALUE)).quantize(FOUR_DP, ROUND_UP)
    interest = settings.LOAN_INTEREST_PERCENT
    return Loan.objects.create(
        member=member,
        group=group,
        principal=amount,
        interest_percent=interest,
        total_due=(amount * (1 + interest / 100)).quantize(TWO_DP),
        collateral_grams=collateral,
    )


@transaction.atomic
def approve_loan(*, loan, by):
    loan = Loan.objects.select_for_update().get(pk=loan.pk)
    if loan.status != Loan.Status.PENDING:
        raise LoanError("Only pending loans can be approved")
    result = mobile_money.get_provider().disburse(loan.member.default_wallet_number(), loan.principal, f"Treadstone loan #{loan.pk}")
    if not result.success:
        raise LoanError(f"Disbursement failed: {result.message}")
    loan.status = Loan.Status.ACTIVE
    loan.disbursement_reference = result.reference
    loan.reviewed_by = by
    loan.reviewed_at = timezone.now()
    loan.save()
    notify(loan.member, kind=Notification.Kind.LOAN, title=f"Loan approved: K{loan.principal}",
           body=f"Your loan of K{loan.principal} has been sent to {loan.member.default_wallet_number()}. Total to repay K{loan.total_due}.",
           link="/loans")
    return loan


@transaction.atomic
def reject_loan(*, loan, by):
    loan = Loan.objects.select_for_update().get(pk=loan.pk)
    if loan.status != Loan.Status.PENDING:
        raise LoanError("Only pending loans can be rejected")
    loan.status = Loan.Status.REJECTED
    loan.reviewed_by = by
    loan.reviewed_at = timezone.now()
    loan.save()
    notify(loan.member, kind=Notification.Kind.LOAN, title="Loan request not approved",
           body=f"Your loan request of K{loan.principal} was not approved. Your gold is no longer held for it.",
           link="/loans")
    return loan


def repay_loan(*, loan, member, amount):
    amount = Decimal(amount).quantize(TWO_DP)
    loan = Loan.objects.get(pk=loan.pk)  # never trust a caller's possibly stale copy
    if loan.member_id != member.pk:
        raise LoanError("This is not your loan")
    if loan.status != Loan.Status.ACTIVE:
        raise LoanError("This loan is not active")
    if amount <= 0 or amount > loan.outstanding:
        raise LoanError(f"Repay between K0.01 and K{loan.outstanding}")
    result = mobile_money.get_provider().collect(member.default_wallet_number(), amount, f"Treadstone loan #{loan.pk} repayment")
    if not result.success:
        raise LoanError(f"Payment failed: {result.message}")
    with transaction.atomic():
        loan = Loan.objects.select_for_update().get(pk=loan.pk)
        LoanRepayment.objects.create(loan=loan, amount=amount, payment_reference=result.reference)
        loan.amount_repaid += amount
        if loan.amount_repaid >= loan.total_due:
            loan.status = Loan.Status.REPAID
        loan.save(update_fields=["amount_repaid", "status"])
    return loan
