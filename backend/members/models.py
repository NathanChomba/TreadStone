from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import RegexValidator
from django.db import models

zambian_phone = RegexValidator(
    regex=r"^\+260(9[5-7]|7[5-7])\d{7}$",
    message="Use the international format, e.g. +260971234567.",
)

nrc_format = RegexValidator(
    regex=r"^\d{6}/\d{2}/\d$",
    message="NRC format is 123456/78/1.",
)


class MemberManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, phone, password, **extra):
        if not phone:
            raise ValueError("A phone number is required")
        user = self.model(phone=phone, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, phone, password=None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create_user(phone, password, **extra)

    def create_superuser(self, phone, password=None, **extra):
        extra["is_staff"] = True
        extra["is_superuser"] = True
        extra.setdefault("kyc_status", Member.KYC.VERIFIED)
        return self._create_user(phone, password, **extra)


class Member(AbstractUser):
    """A platform user. Logs in with their phone number, which is also their mobile money wallet."""

    class KYC(models.TextChoices):
        PENDING = "PENDING", "Pending"
        VERIFIED = "VERIFIED", "Verified"
        REJECTED = "REJECTED", "Rejected"

    username = None
    phone = models.CharField(max_length=13, unique=True, validators=[zambian_phone])
    nrc_number = models.CharField(
        "NRC number", max_length=11, unique=True, null=True, blank=True, validators=[nrc_format]
    )
    kyc_status = models.CharField(max_length=10, choices=KYC.choices, default=KYC.PENDING)

    class Language(models.TextChoices):
        ENGLISH = "en", "English"
        BEMBA = "bem", "Bemba"
        NYANJA = "nya", "Nyanja"

    language = models.CharField(max_length=3, choices=Language.choices, default=Language.ENGLISH)
    sms_reminders = models.BooleanField(default=True, help_text="SMS two days before each due date")
    price_alerts = models.BooleanField(default=False, help_text="Alert when gold moves 3% or more in a day")

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = MemberManager()

    class Meta:
        ordering = ["first_name", "last_name"]

    def __str__(self):
        name = self.get_full_name()
        return f"{name} ({self.phone})" if name else self.phone

    def default_wallet_number(self):
        """Where payouts and loans are sent: the default wallet, else the login phone."""
        wallet = self.wallets.filter(is_default=True).first()
        return wallet.number if wallet else self.phone


def provider_for(number):
    """Zambian mobile networks by prefix: 096/076 MTN, 097/077 Airtel, 095 Zamtel."""
    prefix = number[4:6] if number.startswith("+260") else ""
    return {"96": "MTN", "76": "MTN", "97": "AIRTEL", "77": "AIRTEL", "95": "ZAMTEL"}.get(prefix, "MTN")


class MobileWallet(models.Model):
    class Provider(models.TextChoices):
        MTN = "MTN", "MTN MoMo"
        AIRTEL = "AIRTEL", "Airtel Money"
        ZAMTEL = "ZAMTEL", "Zamtel Kwacha"

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="wallets")
    provider = models.CharField(max_length=6, choices=Provider.choices)
    number = models.CharField(max_length=13, validators=[zambian_phone])
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_default", "created_at"]
        constraints = [
            models.UniqueConstraint(fields=["member", "number"], name="unique_member_wallet"),
            models.UniqueConstraint(fields=["member"], condition=models.Q(is_default=True), name="one_default_wallet"),
        ]

    def __str__(self):
        return f"{self.get_provider_display()} {self.number}"


class Notification(models.Model):
    class Kind(models.TextChoices):
        PAYMENT = "PAYMENT", "Payment"
        GOLD = "GOLD", "Gold bought or sold"
        PAYOUT = "PAYOUT", "Payout"
        LOAN = "LOAN", "Loan"
        REMINDER = "REMINDER", "Reminder"
        PRICE = "PRICE", "Price alert"
        GROUP = "GROUP", "Group"

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="notifications")
    kind = models.CharField(max_length=8, choices=Kind.choices)
    title = models.CharField(max_length=120)
    body = models.CharField(max_length=300)
    link = models.CharField(max_length=100, blank=True, help_text="App route, e.g. /groups/3")
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.member}: {self.title}"
