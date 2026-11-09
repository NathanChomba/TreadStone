from decimal import Decimal

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from loans.services import available_grams, locked_grams
from metals import custodian
from metals.prices import latest_price
from payouts.models import Payout
from savings import dues
from savings import services as savings
from savings.models import Contribution, Membership, SavingsGroup

from . import wallets
from .models import Notification
from .serializers import (LoginSerializer, MemberSerializer, MobileWalletSerializer, NotificationSerializer,
                          RegisterSerializer)


def _auth_response(user, code=status.HTTP_200_OK):
    token, _ = Token.objects.get_or_create(user=user)
    return Response({"token": token.key, "member": MemberSerializer(user).data}, status=code)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        member = serializer.save()
        wallets.ensure_wallet(member)
        return _auth_response(member, status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return _auth_response(serializer.validated_data["user"])


class LogoutView(APIView):
    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/auth/me/ - profile, NRC, language and alert settings."""

    serializer_class = MemberSerializer

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    """POST /api/auth/password/ {current, new}"""

    def post(self, request):
        user = request.user
        if not user.check_password(request.data.get("current", "")):
            return Response({"detail": "Your current password is wrong."}, status=400)
        new = request.data.get("new", "")
        try:
            validate_password(new, user)
        except ValidationError as e:
            return Response({"detail": " ".join(e.messages)}, status=400)
        user.set_password(new)
        user.save(update_fields=["password"])
        return Response({"detail": "Password changed."})


# ---- mobile money numbers ----

class WalletListView(APIView):
    """GET /api/auth/wallets/ ; POST {number, provider?, make_default?}"""

    def get(self, request):
        wallets.ensure_wallet(request.user)
        return Response(MobileWalletSerializer(request.user.wallets.all(), many=True).data)

    def post(self, request):
        s = MobileWalletSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        w = wallets.add_wallet(request.user, number=s.validated_data["number"],
                               provider=s.validated_data.get("provider"),
                               make_default=bool(request.data.get("make_default")))
        return Response(MobileWalletSerializer(w).data, status=status.HTTP_201_CREATED)


class WalletDefaultView(APIView):
    def post(self, request, pk):
        return Response(MobileWalletSerializer(wallets.set_default(request.user, pk)).data)


class WalletDeleteView(APIView):
    def delete(self, request, pk):
        wallets.remove_wallet(request.user, pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---- notifications ----

class NotificationListView(APIView):
    """GET /api/auth/notifications/ - newest 50 and the unread count."""

    def get(self, request):
        qs = request.user.notifications.all()
        return Response({
            "unread": qs.filter(read_at__isnull=True).count(),
            "results": NotificationSerializer(qs[:50], many=True).data,
        })


class NotificationReadView(APIView):
    """POST /api/auth/notifications/read/ - mark everything read."""

    def post(self, request):
        request.user.notifications.filter(read_at__isnull=True).update(read_at=timezone.now())
        return Response({"unread": 0})


# ---- dashboard ----

class DashboardView(APIView):
    """GET /api/auth/dashboard/ - holdings across all the member's groups, valued at the latest price."""

    def get(self, request):
        member = request.user
        prices = {}
        holdings, up_next = [], []
        total = bought_total = received_total = paid_out_total = Decimal("0.00")
        grams_by_metal = {}
        for ms in Membership.objects.filter(member=member).select_related("group"):
            g = ms.group
            if g.metal not in prices:
                prices[g.metal] = latest_price(g.metal)
            price = prices[g.metal].price_per_gram
            # A rotating-group member who has already received the pot is "owed" by the group,
            # not holding negative gold; show zero rather than a negative holding.
            grams = max(custodian.member_grams(member, g), Decimal("0.0000"))
            value = (grams * price).quantize(Decimal("0.01"))
            mine = Contribution.objects.filter(member=member, group=g)
            bought = mine.filter(status=Contribution.Status.COMPLETED).aggregate(s=Sum("amount"))["s"] or Decimal("0.00")
            received = mine.filter(status=Contribution.Status.RECEIVED).aggregate(s=Sum("amount"))["s"] or Decimal("0.00")
            paid_out = Payout.objects.filter(member=member, group=g).aggregate(s=Sum("amount_zmw"))["s"] or Decimal("0.00")
            total += value
            bought_total += bought
            received_total += received
            paid_out_total += paid_out
            grams_by_metal[g.metal] = grams_by_metal.get(g.metal, Decimal("0")) + grams

            active = g.status == SavingsGroup.Status.ACTIVE
            next_due = dues.next_due(g) if active else None
            paid_now = savings.paid_this_period(g, member) if active else False
            holding = {
                "group": g.id,
                "group_name": g.name,
                "group_type": g.group_type,
                "group_status": g.status,
                "metal": g.metal,
                "contribution_amount": str(g.contribution_amount),
                "frequency": g.frequency,
                "current_cycle": g.current_cycle,
                "member_count": g.memberships.count(),
                "is_admin": ms.is_admin,
                "grams": str(grams),
                "locked_grams": str(locked_grams(member, g)),
                "available_grams": str(available_grams(member, g)),
                "value_zmw": str(value),
                "contributed_zmw": str(bought + received),
                "awaiting_gold_zmw": str(received),
                "paid_out_zmw": str(paid_out),
                "next_due_date": next_due,
                "paid_this_period": paid_now,
                "period_index": dues.periods_elapsed(g) + 1 if g.started_at else None,
                "term_cycles": g.term_cycles if not g.is_rotating else g.memberships.count(),
                "maturity_date": dues.maturity_date(g) if not g.is_rotating else None,
            }
            holdings.append(holding)
            if active and not paid_now:
                up_next.append({"kind": "due", "group": g.id, "group_name": g.name, "date": next_due,
                                "amount": str(g.contribution_amount), "days": (next_due - dues.today()).days})
            if received:
                up_next.append({"kind": "gold", "group": g.id, "group_name": g.name, "date": next_due or dues.today(),
                                "amount": str(received)})
            if holding["maturity_date"] and active:
                up_next.append({"kind": "matures", "group": g.id, "group_name": g.name, "date": holding["maturity_date"],
                                "period_index": holding["period_index"], "term_cycles": g.term_cycles})
        up_next.sort(key=lambda i: i["date"])
        return Response({
            "member": MemberSerializer(member).data,
            "holdings": holdings,
            "up_next": up_next[:4],
            "total_value_zmw": str(total),
            "grams_by_metal": {m: str(v) for m, v in grams_by_metal.items()},
            "contributed_zmw": str(bought_total + received_total),
            "awaiting_gold_zmw": str(received_total),
            "paid_out_zmw": str(paid_out_total),
            # Saving in metal versus holding the same kwacha as cash. Money still waiting for its
            # gold purchase counts at face value on both sides, so it is left out.
            "preserved_zmw": str(total + paid_out_total - bought_total),
            "unread_notifications": member.notifications.filter(read_at__isnull=True).count(),
            "prices": {m: {"price_per_gram": str(p.price_per_gram), "fetched_at": p.fetched_at} for m, p in prices.items()},
        })
