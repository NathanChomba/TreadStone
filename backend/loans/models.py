from django.conf import settings
from django.db import models


class Loan(models.Model):
    """A ZMW loan secured against the member's metal in one group.

    While PENDING or ACTIVE, `collateral_grams` are locked: the member cannot
    withdraw them.
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "Awaiting approval"
        ACTIVE = "ACTIVE", "Active"
        REPAID = "REPAID", "Repaid"
        REJECTED = "REJECTED", "Rejected"

    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="loans")
    group = models.ForeignKey("savings.SavingsGroup", on_delete=models.PROTECT, related_name="loans")
    principal = models.DecimalField(max_digits=12, decimal_places=2)
    interest_percent = models.DecimalField(max_digits=5, decimal_places=2)
    total_due = models.DecimalField(max_digits=12, decimal_places=2)
    amount_repaid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    collateral_grams = models.DecimalField(max_digits=14, decimal_places=4)
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.PENDING)
    disbursement_reference = models.CharField(max_length=40, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="reviewed_loans"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Loan #{self.pk} {self.member} K{self.principal} ({self.status})"

    @property
    def outstanding(self):
        return self.total_due - self.amount_repaid


class LoanRepayment(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.PROTECT, related_name="repayments")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_reference = models.CharField(max_length=40)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
