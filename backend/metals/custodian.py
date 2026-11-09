"""Simulated Zambia Gold Company Limited (ZGCL) custodian.

No real ZGCL API exists. This module behaves like one would: it buys or sells
metal at the latest stored price, charges a percentage fee, and issues a
reference for each deal. Every deal is written to CustodianTransaction, which
is the metal ledger used for all balances.
"""

import uuid
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal

from django.conf import settings
from django.db.models import Case, DecimalField, F, Sum, When

from config.errors import DomainError

from .models import CustodianTransaction
from .prices import latest_price

TWO_DP = Decimal("0.01")
FOUR_DP = Decimal("0.0001")


class CustodianError(DomainError):
    pass


def _fee(amount):
    return (amount * settings.CUSTODIAN_FEE_PERCENT / 100).quantize(TWO_DP, ROUND_HALF_UP)


def _reference():
    return f"ZGCL-{uuid.uuid4().hex[:10].upper()}"


def quote(metal, amount_zmw, price=None):
    """What `amount_zmw` would buy right now: (grams, fee, price object). Grams rounded down."""
    amount_zmw = Decimal(amount_zmw).quantize(TWO_DP)
    price = price or latest_price(metal)
    fee = _fee(amount_zmw)
    grams = ((amount_zmw - fee) / price.price_per_gram).quantize(FOUR_DP, ROUND_DOWN)
    return grams, fee, price


def buy(*, group, member, amount_zmw, price=None, batch=""):
    """Convert ZMW into grams of the group's metal. Grams are rounded down.

    Pass `price` (a MetalPrice) to buy a whole batch at one price, as the custodian
    does when a group's contributions are pooled on the due date.
    """
    amount_zmw = Decimal(amount_zmw).quantize(TWO_DP)
    if amount_zmw <= 0:
        raise CustodianError("Amount must be positive")
    grams, fee, price = quote(group.metal, amount_zmw, price)
    if grams <= 0:
        raise CustodianError("Amount too small to buy any metal")
    return CustodianTransaction.objects.create(
        batch=batch,
        kind=CustodianTransaction.Kind.BUY,
        metal=group.metal,
        grams=grams,
        price_per_gram=price.price_per_gram,
        gross_zmw=amount_zmw,
        fee_zmw=fee,
        group=group,
        member=member,
        reference=_reference(),
    )


def sell(*, group, member, grams):
    """Convert grams back to ZMW. Returns the transaction; net proceeds are gross - fee."""
    grams = Decimal(grams).quantize(FOUR_DP, ROUND_DOWN)
    if grams <= 0:
        raise CustodianError("Grams must be positive")
    if grams > group_grams(group):
        raise CustodianError("The group does not hold that much metal")
    price = latest_price(group.metal)
    gross = (grams * price.price_per_gram).quantize(TWO_DP, ROUND_DOWN)
    return CustodianTransaction.objects.create(
        kind=CustodianTransaction.Kind.SELL,
        metal=group.metal,
        grams=grams,
        price_per_gram=price.price_per_gram,
        gross_zmw=gross,
        fee_zmw=_fee(gross),
        group=group,
        member=member,
        reference=_reference(),
    )


_signed_grams = Sum(
    Case(
        When(kind=CustodianTransaction.Kind.BUY, then=F("grams")),
        default=-F("grams"),
        output_field=DecimalField(max_digits=14, decimal_places=4),
    )
)


def group_grams(group):
    total = CustodianTransaction.objects.filter(group=group).aggregate(g=_signed_grams)["g"]
    return (total or Decimal("0")).quantize(FOUR_DP)


def member_grams(member, group):
    """Net grams attributed to a member in a group.

    For a rotating group this can go negative after the member receives the pot
    early: it means they owe the group future contributions.
    """
    total = CustodianTransaction.objects.filter(group=group, member=member).aggregate(g=_signed_grams)["g"]
    return (total or Decimal("0")).quantize(FOUR_DP)


def value_zmw(grams, metal):
    return (Decimal(grams) * latest_price(metal).price_per_gram).quantize(TWO_DP, ROUND_HALF_UP)
