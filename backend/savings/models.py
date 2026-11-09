import secrets

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from metals.models import Metal


def new_invite_code():
    return secrets.token_hex(4).upper()


class SavingsGroup(models.Model):
    """A community savings circle whose pooled money is held as metal.

    ROTATING (tontine / chilimba): each cycle every member pays the fixed
    amount and one member, in position order, receives that cycle's metal.
    ANNUITY: members build up their own metal balance and withdraw it later
    in instalments.
    """

    class Type(models.TextChoices):
        ROTATING = "ROTATING", "Rotating (tontine)"
        ANNUITY = "ANNUITY", "Annuity"

    class Frequency(models.TextChoices):
        WEEKLY = "WEEKLY", "Weekly"
        MONTHLY = "MONTHLY", "Monthly"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open for members"
        ACTIVE = "ACTIVE", "Active"
        CLOSED = "CLOSED", "Closed"

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    group_type = models.CharField(max_length=10, choices=Type.choices)
    metal = models.CharField(max_length=3, choices=Metal.choices, default=Metal.GOLD)
    contribution_amount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(10)],
        help_text="ZMW per member per cycle (rotating) or minimum deposit (annuity)",
    )
    frequency = models.CharField(max_length=10, choices=Frequency.choices, default=Frequency.MONTHLY)
    max_members = models.PositiveSmallIntegerField(default=12, validators=[MinValueValidator(2)])
    invite_code = models.CharField(max_length=8, unique=True, default=new_invite_code)
    status = models.CharField(max_length=6, choices=Status.choices, default=Status.OPEN)
    current_cycle = models.PositiveSmallIntegerField(default=1)
    due_day = models.PositiveSmallIntegerField(
        default=10, validators=[MinValueValidator(1), MaxValueValidator(28)],
        help_text="Day of the month contributions are due and gold is bought (monthly groups)",
    )
    term_cycles = models.PositiveSmallIntegerField(
        default=12, validators=[MinValueValidator(1)], help_text="Annuity: number of periods until it matures",
    )
    started_at = models.DateField(null=True, blank=True, help_text="When contributions opened")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_groups")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    @property
    def is_rotating(self):
        return self.group_type == self.Type.ROTATING


class Membership(models.Model):
    group = models.ForeignKey(SavingsGroup, on_delete=models.CASCADE, related_name="memberships")
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="memberships")
    position = models.PositiveSmallIntegerField(help_text="Payout order in a rotating group (1 = first)")
    is_admin = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(fields=["group", "member"], name="unique_group_member"),
            models.UniqueConstraint(fields=["group", "position"], name="unique_group_position"),
        ]

    def __str__(self):
        return f"{self.member} in {self.group} (#{self.position})"


class Contribution(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Collecting"
        RECEIVED = "RECEIVED", "Received, gold not bought yet"
        COMPLETED = "COMPLETED", "Gold bought"
        FAILED = "FAILED", "Failed"

    # Money is in the group's account (received) or already turned into metal (completed).
    PAID = (Status.RECEIVED, Status.COMPLETED)

    group = models.ForeignKey(SavingsGroup, on_delete=models.PROTECT, related_name="contributions")
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="contributions")
    cycle = models.PositiveSmallIntegerField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    reference = models.CharField(max_length=20, unique=True, null=True, blank=True, help_text="Treadstone receipt, TS-yymm-dd-nnnn")
    provider = models.CharField(max_length=6, blank=True)
    wallet_number = models.CharField(max_length=13, blank=True)
    payment_reference = models.CharField(max_length=40, blank=True)
    failure_reason = models.CharField(max_length=200, blank=True)
    custodian_transaction = models.OneToOneField(
        "metals.CustodianTransaction", on_delete=models.PROTECT, null=True, blank=True, related_name="contribution"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.member} K{self.amount} to {self.group} (cycle {self.cycle}, {self.status})"
