"""Mobile money adapter.

`collect` pulls money from a member's wallet (contributions, loan repayments);
`disburse` pushes money to it (payouts, loan disbursements).

Only the simulated provider is implemented. A real sandbox (MTN MoMo, Airtel
Money) is asynchronous: it returns PENDING and confirms later via a callback.
The simulated provider confirms immediately so the rest of the flow can be
built and demonstrated; swap in a real provider by adding a class with the
same two methods and selecting it with MOBILE_MONEY_PROVIDER.
"""

import logging
import uuid
from dataclasses import dataclass
from decimal import Decimal

from django.conf import settings

from config.errors import DomainError

logger = logging.getLogger("treadstone.mobile_money")


class PaymentError(DomainError):
    pass


@dataclass
class PaymentResult:
    success: bool
    reference: str
    message: str = ""


class SimulatedProvider:
    """Always succeeds, except for test numbers ending in 0000 (insufficient funds)."""

    def _ref(self, prefix):
        return f"{prefix}-{uuid.uuid4().hex[:12].upper()}"

    def collect(self, phone: str, amount: Decimal, description: str) -> PaymentResult:
        if phone.endswith("0000"):
            logger.info("SIM collect FAILED %s ZMW %s (%s)", phone, amount, description)
            return PaymentResult(False, "", "Insufficient funds (simulated)")
        ref = self._ref("COL")
        logger.info("SIM collect %s ZMW %s (%s) -> %s", phone, amount, description, ref)
        return PaymentResult(True, ref, "Collected")

    def disburse(self, phone: str, amount: Decimal, description: str) -> PaymentResult:
        ref = self._ref("DIS")
        logger.info("SIM disburse %s ZMW %s (%s) -> %s", phone, amount, description, ref)
        return PaymentResult(True, ref, "Disbursed")


_PROVIDERS = {"simulated": SimulatedProvider}


def get_provider():
    name = settings.MOBILE_MONEY_PROVIDER
    try:
        return _PROVIDERS[name]()
    except KeyError:
        raise PaymentError(f"Unknown MOBILE_MONEY_PROVIDER '{name}'") from None
