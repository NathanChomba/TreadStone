from django.conf import settings
from django.db import models


class Payout(models.Model):
    """Metal sold by the custodian and paid out to a member in ZMW."""

    class Kind(models.TextChoices):
        ROTATION = "ROTATION", "Rotation pot"
        WITHDRAWAL = "WITHDRAWAL", "Annuity withdrawal"

    class Status(models.TextChoices):
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    group = models.ForeignKey("savings.SavingsGroup", on_delete=models.PROTECT, related_name="payouts")
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="payouts")
    kind = models.CharField(max_length=10, choices=Kind.choices)
    cycle = models.PositiveSmallIntegerField(null=True, blank=True)
    grams = models.DecimalField(max_digits=14, decimal_places=4)
    amount_zmw = models.DecimalField(max_digits=12, decimal_places=2, help_text="Net ZMW sent to the member")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.COMPLETED)
    payment_reference = models.CharField(max_length=40, blank=True)
    custodian_transaction = models.OneToOneField(
        "metals.CustodianTransaction", on_delete=models.PROTECT, related_name="payout"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.kind} {self.grams}g -> {self.member} K{self.amount_zmw}"
