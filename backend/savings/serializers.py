from rest_framework import serializers

from metals import custodian

from . import dues
from .models import Contribution, Membership, SavingsGroup


class MembershipSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="member.get_full_name", read_only=True)
    phone = serializers.CharField(source="member.phone", read_only=True)

    class Meta:
        model = Membership
        fields = ["id", "member", "name", "phone", "position", "is_admin", "joined_at"]


class SavingsGroupSerializer(serializers.ModelSerializer):
    member_count = serializers.IntegerField(source="memberships.count", read_only=True)

    class Meta:
        model = SavingsGroup
        fields = ["id", "name", "description", "group_type", "metal", "contribution_amount", "frequency",
                  "due_day", "term_cycles", "started_at", "max_members", "member_count", "invite_code", "status",
                  "current_cycle", "created_at"]
        read_only_fields = ["invite_code", "status", "current_cycle", "started_at", "created_at"]


class ContributionSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source="group.name", read_only=True)
    metal = serializers.CharField(source="group.metal", read_only=True)
    grams = serializers.DecimalField(source="custodian_transaction.grams", max_digits=14, decimal_places=4,
                                     read_only=True, allow_null=True)
    price_per_gram = serializers.DecimalField(source="custodian_transaction.price_per_gram", max_digits=14,
                                              decimal_places=4, read_only=True, allow_null=True)
    custodian_reference = serializers.CharField(source="custodian_transaction.reference", read_only=True,
                                                allow_null=True)
    estimated_grams = serializers.SerializerMethodField()
    gold_buy_date = serializers.SerializerMethodField()

    class Meta:
        model = Contribution
        fields = ["id", "group", "group_name", "metal", "cycle", "amount", "status", "reference", "provider",
                  "wallet_number", "payment_reference", "failure_reason", "grams", "price_per_gram",
                  "custodian_reference", "estimated_grams", "gold_buy_date", "created_at"]
        read_only_fields = ["cycle", "status", "reference", "provider", "wallet_number", "payment_reference",
                            "failure_reason"]

    def get_estimated_grams(self, obj):
        """Received but not yet bought: what it would buy at today's price."""
        if obj.status != Contribution.Status.RECEIVED:
            return None
        grams, _, _ = custodian.quote(obj.group.metal, obj.amount)
        return str(grams)

    def get_gold_buy_date(self, obj):
        if obj.status != Contribution.Status.RECEIVED:
            return None
        return dues.next_due(obj.group)
