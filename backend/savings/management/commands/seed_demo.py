"""Defense demo: five members of one annuity gold group, with backdated monthly
contributions bought at the REAL historical gold price of each date.

    python manage.py seed_demo           # create (refuses if the demo already exists)
    python manage.py seed_demo --reset   # remove the demo and create it again

Needs real price history back to March 2024: run import-real-prices.bat first.
Every number the app shows comes from the stored real prices and the normal
custodian/ledger code; nothing here sets a balance or a profit directly.
"""

import uuid
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from loans.models import Loan, LoanRepayment
from members.models import Member
from members.wallets import ensure_wallet
from metals import custodian
from metals.models import CustodianTransaction, Metal, MetalPrice
from metals.prices import latest_price
from payouts.models import Payout
from savings.models import Contribution, Membership, SavingsGroup

PASSWORD = "Demo@2026"
GROUP_CODE = "DEMOGOLD"
GROUP_START = date(2024, 3, 1)
DUE_DAY = 10
LAST_MONTH = None  # set in handle(): the most recent past due date


def months(start, stop):
    """The 10th of each month from `start` to `stop` inclusive."""
    d = date(start.year, start.month, DUE_DAY)
    while d <= stop:
        yield d
        d = date(d.year + d.month // 12, d.month % 12 + 1, DUE_DAY)


def plans(last):
    """Contribution plans: list of (date, amount). `last` is the latest due date to include."""
    return {
        "trader": [(d, Decimal("500")) for d in months(date(2024, 3, 1), last)],
        "teacher": [(date(2024, 6, 10), Decimal("3000"))]
                   + [(d, Decimal("300")) for d in months(date(2024, 7, 1), last)],
        "business": [(date(2024, 4, 10), Decimal("10000"))]
                    + [(d, Decimal("1000")) for d in months(date(2024, 5, 1), last) if d.month % 3 == 1],
        "farmer": [(d, Decimal("4000")) for d in months(date(2024, 6, 1), last) if d.month in (6, 7)],
        "late": [(d, Decimal("1000")) for d in months(date(2025, 6, 1), last)],
    }


USERS = [
    # key, phone, first, last, role
    ("trader", "+260971000001", "Mwila", "Banda", "Market trader, Chisokone - K500 every month since March 2024"),
    ("teacher", "+260971000002", "Grace", "Phiri", "Teacher - K3,000 to start (June 2024), then K300 a month"),
    ("business", "+260971000003", "Joseph", "Chanda", "Hardware shop owner - K10,000 to start (April 2024), K1,000 a quarter"),
    ("farmer", "+260971000004", "Mutale", "Zulu", "Maize farmer - K4,000 after each June and July harvest"),
    ("late", "+260971000005", "Natasha", "Mumba", "Joined late (June 2025, near the peak) - K1,000 a month"),
]
PHONES = [u[1] for u in USERS]


def price_on(day):
    """The stored real price at or just before noon on `day` (within 5 days)."""
    tz = timezone.get_current_timezone()
    at = timezone.make_aware(datetime.combine(day, time(23, 59)), tz)
    p = (MetalPrice.objects.filter(metal=Metal.GOLD, fetched_at__lte=at)
         .exclude(source__startswith="simulated").order_by("-fetched_at").first())
    if p is None or (at - p.fetched_at) > timedelta(days=5):
        raise CommandError(
            f"No real gold price stored for {day:%d %b %Y}. Run import-real-prices.bat first "
            "(it imports history back to March 2024)."
        )
    return p


def remove_demo(out):
    members = Member.objects.filter(phone__in=PHONES)
    groups = SavingsGroup.objects.filter(invite_code=GROUP_CODE)
    LoanRepayment.objects.filter(loan__member__in=members).delete()
    LoanRepayment.objects.filter(loan__group__in=groups).delete()
    Loan.objects.filter(member__in=members).delete()
    Loan.objects.filter(group__in=groups).delete()
    Payout.objects.filter(member__in=members).delete()
    Payout.objects.filter(group__in=groups).delete()
    Contribution.objects.filter(member__in=members).delete()
    Contribution.objects.filter(group__in=groups).delete()
    CustodianTransaction.objects.filter(member__in=members).delete()
    CustodianTransaction.objects.filter(group__in=groups).delete()
    Membership.objects.filter(member__in=members).delete()
    Membership.objects.filter(group__in=groups).delete()
    n_groups = groups.count()
    groups.delete()
    n_members = members.count()
    members.delete()
    out(f"Removed demo: {n_members} members, {n_groups} group(s).")


class Command(BaseCommand):
    help = "Create the five-member defense demo, priced from real historical gold prices."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Remove the existing demo first")

    @transaction.atomic
    def handle(self, *args, reset, **options):
        exists = SavingsGroup.objects.filter(invite_code=GROUP_CODE).exists() or \
            Member.objects.filter(phone__in=PHONES).exists()
        if exists and not reset:
            raise CommandError("The demo already exists. Use --reset to recreate it.")
        if exists:
            remove_demo(self.stdout.write)

        today = timezone.localdate()
        # Contributions up to the most recent due date that has already passed (gold is bought on the due date).
        last = date(today.year, today.month, DUE_DAY)
        if last >= today:
            last = date(last.year - (last.month == 1), (last.month - 2) % 12 + 1, DUE_DAY)
        schedule = plans(last)
        all_days = sorted({d for p in schedule.values() for d, _ in p})
        prices = {d: price_on(d) for d in all_days}  # fails early if history is missing

        members = {}
        for key, phone, first, last_name, role in USERS:
            m = Member.objects.create_user(phone, PASSWORD, first_name=first, last_name=last_name,
                                           kyc_status=Member.KYC.VERIFIED, price_alerts=True)
            ensure_wallet(m)
            members[key] = m

        group = SavingsGroup.objects.create(
            name="Copperbelt Gold Savers",
            description="Demo annuity group: each member builds their own gold balance at ZGCL.",
            group_type=SavingsGroup.Type.ANNUITY, metal=Metal.GOLD, contribution_amount=Decimal("300"),
            frequency=SavingsGroup.Frequency.MONTHLY, due_day=DUE_DAY, term_cycles=36, max_members=12,
            invite_code=GROUP_CODE, status=SavingsGroup.Status.ACTIVE, started_at=GROUP_START,
            created_by=members["trader"],
        )
        tz = timezone.get_current_timezone()
        for pos, (key, *_rest) in enumerate(USERS, 1):
            first_day = schedule[key][0][0]
            ms = Membership.objects.create(group=group, member=members[key], position=pos, is_admin=(key == "trader"))
            Membership.objects.filter(pk=ms.pk).update(
                joined_at=timezone.make_aware(datetime.combine(first_day - timedelta(days=3), time(9, 0)), tz))

        count = 0
        for key, plan in schedule.items():
            m = members[key]
            for d, amount in plan:
                cycle = (d.year - GROUP_START.year) * 12 + d.month - GROUP_START.month + 1
                paid_at = timezone.make_aware(datetime.combine(d - timedelta(days=2), time(10, 0)), tz)
                bought_at = timezone.make_aware(datetime.combine(d, time(11, 0)), tz)
                c = Contribution.objects.create(
                    group=group, member=m, cycle=cycle, amount=amount, status=Contribution.Status.RECEIVED,
                    reference=f"TS-{d:%y%m}-{d - timedelta(days=2):%d}-{count:04d}",
                    provider="AIRTEL", wallet_number=m.phone, payment_reference=f"SIM-{uuid.uuid4().hex[:12].upper()}",
                )
                txn = custodian.buy(group=group, member=m, amount_zmw=amount, price=prices[d],
                                    batch=f"ZGCL-B-DEMO{d:%y%m}")
                c.status = Contribution.Status.COMPLETED
                c.custodian_transaction = txn
                c.save(update_fields=["status", "custodian_transaction"])
                Contribution.objects.filter(pk=c.pk).update(created_at=paid_at)
                CustodianTransaction.objects.filter(pk=txn.pk).update(created_at=bought_at)
                count += 1

        # Results, valued exactly the way the dashboard values them.
        now = latest_price(Metal.GOLD)
        self.stdout.write(f"\n{count} backdated contributions, each bought at that date's real gold price.")
        self.stdout.write(f"Valued at the latest stored price: K{now.price_per_gram}/g ({now.source}, "
                          f"{timezone.localtime(now.fetched_at):%d %b %Y %H:%M})\n")
        self.stdout.write(f"{'Member':18}{'Phone':16}{'Paid':>11}{'Grams':>10}{'Worth now':>12}{'vs cash':>10}")
        for key, phone, first, last_name, role in USERS:
            m = members[key]
            paid = sum(a for _, a in schedule[key])
            grams = custodian.member_grams(m, group)
            worth = custodian.value_zmw(grams, Metal.GOLD)
            pct = (worth / paid - 1) * 100
            line = f"{first + ' ' + last_name:18}{phone:16}{'K' + format(paid, ',.0f'):>11}{grams:>10}" \
                   f"{'K' + format(worth, ',.0f'):>12}{pct:>+9.1f}%"
            self.stdout.write(self.style.SUCCESS(line) if pct >= 0 else self.style.WARNING(line))
        self.stdout.write(f"\nLog in with any phone above, password {PASSWORD}. Group invite code: {GROUP_CODE}.")
