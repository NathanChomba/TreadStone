from django.conf import settings
from django.db import models
from django.utils import timezone


class Metal(models.TextChoices):
    GOLD = "XAU", "Gold"
    SILVER = "XAG", "Silver"


class MetalPrice(models.Model):
    """A spot price snapshot, in ZMW per gram."""

    metal = models.CharField(max_length=3, choices=Metal.choices)
    price_per_gram = models.DecimalField(max_digits=14, decimal_places=4)
    source = models.CharField(max_length=30)
    fetched_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-fetched_at"]
        indexes = [models.Index(fields=["metal", "-fetched_at"])]

    def __str__(self):
        return f"{self.metal} K{self.price_per_gram}/g @ {self.fetched_at:%Y-%m-%d %H:%M}"


class CustodianTransaction(models.Model):
    """One buy or sell executed by the (simulated) ZGCL custodian.

    This table is the metal ledger: a member's holding in a group is the sum of
    their BUY grams minus their SELL grams. Rows are never edited or deleted.
    """

    class Kind(models.TextChoices):
        BUY = "BUY", "Buy"
        SELL = "SELL", "Sell"

    kind = models.CharField(max_length=4, choices=Kind.choices)
    metal = models.CharField(max_length=3, choices=Metal.choices)
    grams = models.DecimalField(max_digits=14, decimal_places=4)
    price_per_gram = models.DecimalField(max_digits=14, decimal_places=4)
    gross_zmw = models.DecimalField(max_digits=14, decimal_places=2, help_text="ZMW before the custodian fee")
    fee_zmw = models.DecimalField(max_digits=14, decimal_places=2)
    group = models.ForeignKey("savings.SavingsGroup", on_delete=models.PROTECT, related_name="custodian_transactions")
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="custodian_transactions")
    reference = models.CharField(max_length=30, unique=True, help_text="ZGCL certificate / deal reference")
    batch = models.CharField(max_length=30, blank=True, db_index=True, help_text="Shared by every buy in one pooled purchase")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.reference} {self.kind} {self.grams}g {self.metal}"
