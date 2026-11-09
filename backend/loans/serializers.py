from rest_framework import serializers

from .models import Loan, LoanRepayment


class LoanRepaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanRepayment
        fields = ["id", "amount", "payment_reference", "created_at"]


class LoanSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source="group.name", read_only=True)
    member_name = serializers.CharField(source="member.get_full_name", read_only=True)
    outstanding = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    repayments = LoanRepaymentSerializer(many=True, read_only=True)

    class Meta:
        model = Loan
        fields = ["id", "group", "group_name", "member_name", "principal", "interest_percent", "total_due",
                  "amount_repaid", "outstanding", "collateral_grams", "status", "disbursement_reference",
                  "created_at", "reviewed_at", "repayments"]
        read_only_fields = ["interest_percent", "total_due", "amount_repaid", "collateral_grams", "status",
                            "disbursement_reference", "reviewed_at"]


class AmountSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
