from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from loans.services import available_grams, locked_grams
from metals import custodian
from payouts.serializers import PayoutSerializer
from payouts.services import run_rotation_payout

from . import dues, services
from .models import Contribution, SavingsGroup
from .serializers import ContributionSerializer, MembershipSerializer, SavingsGroupSerializer


def schedule_info(group, member):
    """Due date, period and maturity facts the app shows for a group."""
    info = {
        "next_due_date": dues.next_due(group) if group.status == SavingsGroup.Status.ACTIVE else None,
        "period_index": dues.periods_elapsed(group) + 1 if group.started_at else None,
        "maturity_date": dues.maturity_date(group) if not group.is_rotating else None,
        "paid_this_period": services.paid_this_period(group, member) if group.status == SavingsGroup.Status.ACTIVE else False,
        "my_received_zmw": str(services.received_total(group, member)),
        "group_received_zmw": str(services.received_total(group)),
    }
    if info["paid_this_period"] is False and group.status == SavingsGroup.Status.ACTIVE:
        info["days_until_due"] = (info["next_due_date"] - dues.today()).days
    return info


class SavingsGroupViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin,
                          viewsets.GenericViewSet):
    """Groups the current member belongs to."""

    serializer_class = SavingsGroupSerializer

    def get_queryset(self):
        return SavingsGroup.objects.filter(memberships__member=self.request.user).distinct()

    def perform_create(self, serializer):
        serializer.instance = services.create_group(creator=self.request.user, **serializer.validated_data)

    def retrieve(self, request, *args, **kwargs):
        group = self.get_object()
        me = request.user
        data = SavingsGroupSerializer(group).data
        data["members"] = MembershipSerializer(group.memberships.select_related("member"), many=True).data
        data["is_admin"] = group.memberships.filter(member=me, is_admin=True).exists()
        data["group_grams"] = str(custodian.group_grams(group))
        data["my_grams"] = str(custodian.member_grams(me, group))
        data["my_locked_grams"] = str(locked_grams(me, group))
        data["my_available_grams"] = str(available_grams(me, group))
        data["my_value_zmw"] = str(custodian.value_zmw(custodian.member_grams(me, group), group.metal))
        data.update(schedule_info(group, me))
        if group.status == SavingsGroup.Status.ACTIVE:
            data["paid_member_ids"] = [
                ms.member_id for ms in group.memberships.all() if services.paid_this_period(group, ms.member)
            ]
        if group.is_rotating:
            cs = services.cycle_status(group)
            data["cycle_status"] = {
                "cycle": cs["cycle"],
                "paid_member_ids": [m.member_id for m in cs["paid"]],
                "i_have_paid": any(m.member_id == me.pk for m in cs["paid"]),
                "recipient": MembershipSerializer(cs["recipient"]).data if cs["recipient"] else None,
                "awaiting_gold": cs["awaiting_gold"],
            }
        return Response(data)

    @action(detail=False, methods=["post"])
    def join(self, request):
        membership = services.join_group(member=request.user, invite_code=request.data.get("invite_code", ""))
        return Response(SavingsGroupSerializer(membership.group).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        group = services.start_group(group=self.get_object(), by=request.user)
        return Response(SavingsGroupSerializer(group).data)

    @action(detail=True, methods=["post"])
    def payout(self, request, pk=None):
        payout = run_rotation_payout(group=self.get_object(), by=request.user)
        return Response(PayoutSerializer(payout).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def remind(self, request, pk=None):
        """Group admin: remind unpaid members (all, or `member_ids`) by SMS and in the app."""
        ids = request.data.get("member_ids") or None
        sent = services.remind(group=self.get_object(), by=request.user, member_ids=ids)
        return Response({"reminded": [m.get_full_name() or m.phone for m in sent]})


class ContributionViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = ContributionSerializer

    def get_queryset(self):
        qs = Contribution.objects.filter(member=self.request.user).select_related("group", "custodian_transaction")
        group = self.request.query_params.get("group")
        return qs.filter(group_id=group) if group else qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        group = serializer.validated_data["group"]
        if not group.memberships.filter(member=request.user).exists():
            return Response({"detail": "You are not a member of this group"}, status=403)
        contribution = services.contribute(
            member=request.user, group=group, amount=serializer.validated_data["amount"],
            wallet_id=request.data.get("wallet"),
        )
        return Response(self.get_serializer(contribution).data, status=status.HTTP_201_CREATED)
