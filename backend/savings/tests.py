"""End-to-end tests of the money flow through the service layer.

Run with: python manage.py test
"""

from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from config.errors import DomainError
from loans import services as loans
from members.models import Member
from metals import custodian
from metals.models import CustodianTransaction, Metal, MetalPrice
from payouts import services as payouts
from savings import services
from savings.models import Contribution, SavingsGroup

PRICE = Decimal("2000.0000")  # ZMW per gram, fixed for predictable maths


def make_member(phone, verified=True):
    return Member.objects.create_user(
        phone=phone, password="Str0ng-pass!", first_name="Test", last_name=phone[-4:],
        kyc_status=Member.KYC.VERIFIED if verified else Member.KYC.PENDING,
    )


@override_settings(CUSTODIAN_FEE_PERCENT=Decimal("1.0"))
@patch("members.notify.queue_sms", lambda *a, **k: None)
class MoneyFlowTests(TestCase):
    def setUp(self):
        MetalPrice.objects.create(metal=Metal.GOLD, price_per_gram=PRICE, source="test")
        self.alice = make_member("+260971000001")
        self.bob = make_member("+260971000002")
        self.cara = make_member("+260971000003")

    def rotating_group(self):
        g = services.create_group(
            creator=self.alice, name="Kalingalinga Circle", group_type=SavingsGroup.Type.ROTATING,
            metal=Metal.GOLD, contribution_amount=Decimal("500.00"),
        )
        services.join_group(member=self.bob, invite_code=g.invite_code)
        services.join_group(member=self.cara, invite_code=g.invite_code)
        return services.start_group(group=g, by=self.alice)

    def annuity_group(self):
        g = services.create_group(
            creator=self.alice, name="Retirement Gold", group_type=SavingsGroup.Type.ANNUITY,
            metal=Metal.GOLD, contribution_amount=Decimal("100.00"),
        )
        services.join_group(member=self.bob, invite_code=g.invite_code)
        return g

    def pay(self, group, *members, amount="500"):
        for m in members:
            services.contribute(member=m, group=group, amount=Decimal(amount))
        services.buy_gold_for_group(group)

    # --- custodian ---------------------------------------------------------

    def test_buy_converts_net_of_fee_and_rounds_grams_down(self):
        g = self.annuity_group()
        txn = custodian.buy(group=g, member=self.alice, amount_zmw=Decimal("1000.00"))
        # K1000 - 1% fee = K990, / K2000 per gram = 0.495 g
        self.assertEqual(txn.fee_zmw, Decimal("10.00"))
        self.assertEqual(txn.grams, Decimal("0.4950"))
        self.assertTrue(txn.reference.startswith("ZGCL-"))

    def test_cannot_sell_more_than_group_holds(self):
        g = self.annuity_group()
        with self.assertRaises(DomainError):
            custodian.sell(group=g, member=self.alice, grams=Decimal("1"))

    # --- rotating group ----------------------------------------------------

    def test_rotating_join_rules(self):
        g = self.rotating_group()
        dave = make_member("+260971000004")
        with self.assertRaisesMessage(DomainError, "already started"):
            services.join_group(member=dave, invite_code=g.invite_code)

    def test_rotating_contribution_must_be_exact_and_once_per_cycle(self):
        g = self.rotating_group()
        with self.assertRaises(DomainError):
            services.contribute(member=self.bob, group=g, amount=Decimal("400"))
        services.contribute(member=self.bob, group=g, amount=Decimal("500"))
        with self.assertRaisesMessage(DomainError, "already contributed"):
            services.contribute(member=self.bob, group=g, amount=Decimal("500"))

    def test_failed_payment_records_failed_contribution_and_buys_nothing(self):
        g = services.create_group(
            creator=self.alice, name="A", group_type=SavingsGroup.Type.ANNUITY,
            metal=Metal.GOLD, contribution_amount=Decimal("100"),
        )
        broke = make_member("+260970000000")  # simulated provider fails numbers ending 0000
        services.join_group(member=broke, invite_code=g.invite_code)
        with self.assertRaisesMessage(DomainError, "Payment failed"):
            services.contribute(member=broke, group=g, amount=Decimal("100"))
        self.assertEqual(Contribution.objects.get(member=broke).status, Contribution.Status.FAILED)
        self.assertEqual(services.buy_gold_for_group(g), 0)
        self.assertFalse(CustodianTransaction.objects.exists())

    def test_rotation_payout_needs_everyone_paid_then_pays_and_advances(self):
        g = self.rotating_group()
        services.contribute(member=self.alice, group=g, amount=Decimal("500"))
        services.contribute(member=self.bob, group=g, amount=Decimal("500"))
        with self.assertRaisesMessage(DomainError, "Still waiting"):
            payouts.run_rotation_payout(group=g, by=self.alice)

        services.contribute(member=self.cara, group=g, amount=Decimal("500"))
        # Everyone has paid, but the gold is only bought on the due date.
        with self.assertRaisesMessage(DomainError, "gold is bought on"):
            payouts.run_rotation_payout(group=g, by=self.alice)
        self.assertEqual(services.buy_gold_for_group(g), 3)
        self.assertEqual(CustodianTransaction.objects.values("batch").distinct().count(), 1)
        payout = payouts.run_rotation_payout(group=g, by=self.alice)

        # 3 x (K500 - K5 fee) / K2000 = 3 x 0.2475 g
        self.assertEqual(payout.grams, Decimal("0.7425"))
        self.assertEqual(payout.member, self.alice)  # position 1 goes first
        # Sold at K2000: K1485.00 gross, 1% fee K14.85, net K1470.15
        self.assertEqual(payout.amount_zmw, Decimal("1470.15"))
        g.refresh_from_db()
        self.assertEqual(g.current_cycle, 2)
        self.assertEqual(custodian.group_grams(g), Decimal("0"))

    def test_only_admin_runs_payout(self):
        g = self.rotating_group()
        with self.assertRaisesMessage(DomainError, "admin"):
            payouts.run_rotation_payout(group=g, by=self.bob)

    def test_group_closes_after_last_cycle(self):
        g = self.rotating_group()
        for _ in range(3):
            g.refresh_from_db()
            self.pay(g, self.alice, self.bob, self.cara)
            payouts.run_rotation_payout(group=g, by=self.alice)
        g.refresh_from_db()
        self.assertEqual(g.status, SavingsGroup.Status.CLOSED)

    # --- annuity, loans, withdrawals ---------------------------------------

    def test_annuity_withdrawal_respects_loan_collateral(self):
        g = self.annuity_group()
        self.pay(g, self.bob, amount="2020.20")  # ~1 g after fee
        bal = custodian.member_grams(self.bob, g)
        self.assertEqual(bal, Decimal("1.0000"))

        # 50% LTV at K2000/g -> max loan K1000 against 1 g
        self.assertEqual(loans.max_loan(self.bob, g), Decimal("1000.00"))
        loan = loans.request_loan(member=self.bob, group=g, amount=Decimal("500"))
        self.assertEqual(loan.collateral_grams, Decimal("0.5000"))
        self.assertEqual(loans.available_grams(self.bob, g), Decimal("0.5000"))

        with self.assertRaisesMessage(DomainError, "at most"):
            payouts.withdraw(member=self.bob, group=g, grams=Decimal("0.6"))
        p = payouts.withdraw(member=self.bob, group=g, grams=Decimal("0.5"))
        self.assertEqual(p.amount_zmw, Decimal("990.00"))

        # Repaying in full releases the collateral.
        loans.approve_loan(loan=loan, by=self.alice)
        loan = loans.repay_loan(loan=loan, member=self.bob, amount=Decimal("550.00"))
        self.assertEqual(loan.status, loan.Status.REPAID)
        self.assertEqual(loans.available_grams(self.bob, g), Decimal("0.5000"))

    def test_unverified_member_cannot_borrow(self):
        g = self.annuity_group()
        eve = make_member("+260971000005", verified=False)
        services.join_group(member=eve, invite_code=g.invite_code)
        self.pay(g, eve, amount="1000")
        with self.assertRaisesMessage(DomainError, "KYC"):
            loans.request_loan(member=eve, group=g, amount=Decimal("10"))

    def test_no_loans_against_rotating_groups(self):
        g = self.rotating_group()
        services.contribute(member=self.bob, group=g, amount=Decimal("500"))
        with self.assertRaisesMessage(DomainError, "annuity"):
            loans.request_loan(member=self.bob, group=g, amount=Decimal("10"))


@patch("members.notify.queue_sms", lambda *a, **k: None)
class ApiTests(TestCase):
    def setUp(self):
        MetalPrice.objects.create(metal=Metal.GOLD, price_per_gram=PRICE, source="test")
        MetalPrice.objects.create(metal=Metal.SILVER, price_per_gram=Decimal("25"), source="test")
        self.client = APIClient()

    def test_register_login_create_group_contribute_dashboard(self):
        r = self.client.post("/api/auth/register/", {
            "phone": "+260977123456", "first_name": "Mwila", "last_name": "Banda", "password": "Tontine-2026!",
        }, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        r = self.client.post("/api/auth/login/", {"phone": "+260977123456", "password": "Tontine-2026!"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {r.data['token']}")

        r = self.client.post("/api/groups/", {
            "name": "My pension", "group_type": "ANNUITY", "metal": "XAU", "contribution_amount": "100.00",
        }, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        gid = r.data["id"]

        r = self.client.post("/api/contributions/", {"group": gid, "amount": "50.00"}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("minimum", r.data["detail"])

        r = self.client.post("/api/contributions/", {"group": gid, "amount": "202.02"}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.data["status"], "RECEIVED")
        self.assertEqual(r.data["estimated_grams"], "0.1000")
        self.assertRegex(r.data["reference"], r"^TS-\d{4}-\d{2}-\d{4}$")
        services.buy_gold_for_group(SavingsGroup.objects.get(pk=gid))

        r = self.client.get("/api/auth/dashboard/")
        self.assertEqual(r.data["holdings"][0]["grams"], "0.1000")
        self.assertEqual(r.data["total_value_zmw"], "200.00")

    def test_prices_are_public_and_everything_else_needs_auth(self):
        self.assertEqual(self.client.get("/api/metals/prices/latest/").status_code, 200)
        self.assertEqual(self.client.get("/api/groups/").status_code, 401)


@patch("members.notify.queue_sms", lambda *a, **k: None)
class DueDatesWalletsNotificationsTests(TestCase):
    def setUp(self):
        MetalPrice.objects.create(metal=Metal.GOLD, price_per_gram=PRICE, source="test")
        self.a = make_member("+260971000011")
        self.b = make_member("+260771000012")

    def group(self, **kw):
        g = services.create_group(creator=self.a, name="G", group_type=SavingsGroup.Type.ANNUITY,
                                  metal=Metal.GOLD, contribution_amount=Decimal("100"), **kw)
        services.join_group(member=self.b, invite_code=g.invite_code)
        return g

    def test_monthly_due_dates(self):
        from datetime import date
        from savings import dues
        g = self.group()
        self.assertEqual(dues.next_due(g, date(2026, 11, 4)), date(2026, 11, 10))
        self.assertEqual(dues.next_due(g, date(2026, 11, 10)), date(2026, 11, 10))
        self.assertEqual(dues.next_due(g, date(2026, 11, 11)), date(2026, 12, 10))
        self.assertEqual(dues.next_due(g, date(2026, 12, 20)), date(2027, 1, 10))
        self.assertEqual(dues.last_due(g, date(2026, 11, 4)), date(2026, 10, 10))
        self.assertEqual(dues.period_start(g, date(2026, 11, 4)), date(2026, 10, 11))
        g.started_at = date(2026, 9, 1)
        self.assertEqual(dues.periods_elapsed(g, date(2026, 11, 4)), 2)  # 10 Sep and 10 Oct have passed
        self.assertEqual(dues.maturity_date(g), date(2027, 8, 10))  # 12 periods from 10 Sep

    def test_daily_job_buys_only_when_due(self):
        from datetime import timedelta
        from savings import dues
        g = self.group()
        services.contribute(member=self.b, group=g, amount=Decimal("100"))
        due = dues.next_due(g)
        if due != dues.today():
            self.assertEqual(services.buy_due_gold(on=due - timedelta(days=1)), 0)
        self.assertEqual(services.buy_due_gold(on=due), 1)
        self.assertEqual(Contribution.objects.get(member=self.b).status, Contribution.Status.COMPLETED)

    def test_wallets_and_paying_from_a_second_number(self):
        from members import wallets
        wallets.ensure_wallet(self.b)
        self.assertEqual(self.b.wallets.get().provider, "AIRTEL")  # 077
        second = wallets.add_wallet(self.b, number="+260961234567")
        self.assertEqual(second.provider, "MTN")
        self.assertFalse(second.is_default)
        g = self.group()
        c = services.contribute(member=self.b, group=g, amount=Decimal("100"), wallet_id=second.pk)
        self.assertEqual((c.provider, c.wallet_number), ("MTN", "+260961234567"))
        with self.assertRaises(DomainError):
            wallets.remove_wallet(self.b, self.b.wallets.get(is_default=True).pk)
        wallets.set_default(self.b, second.pk)
        self.assertEqual(self.b.default_wallet_number(), "+260961234567")

    def test_reminders_skip_paid_members_and_opt_outs(self):
        g = self.group()
        services.contribute(member=self.a, group=g, amount=Decimal("100"))
        sent = services.remind(group=g, by=self.a)
        self.assertEqual([m.pk for m in sent], [self.b.pk])
        self.assertTrue(self.b.notifications.filter(kind="REMINDER").exists())
        self.b.sms_reminders = False
        self.b.save()
        self.assertEqual(services.remind(group=g, automatic=True), [])
        with self.assertRaisesMessage(DomainError, "admin"):
            services.remind(group=g, by=self.b)

    def test_notification_api_and_quote_and_history(self):
        g = self.group()
        services.contribute(member=self.b, group=g, amount=Decimal("100"))
        c = APIClient()
        c.force_authenticate(self.b)
        r = c.get("/api/auth/notifications/")
        self.assertEqual(r.data["unread"], 1)
        c.post("/api/auth/notifications/read/")
        self.assertEqual(c.get("/api/auth/notifications/").data["unread"], 0)
        q = c.get("/api/metals/quote/?metal=XAU&amount=1000").data
        self.assertEqual((q["grams"], q["fee_zmw"]), ("0.4950", "10.00"))
        h = c.get("/api/metals/history/?metal=XAU&range=1W").data
        self.assertEqual(h["range"], "1W")
        self.assertEqual(h["points"][-1]["price"], "2000.0000")
