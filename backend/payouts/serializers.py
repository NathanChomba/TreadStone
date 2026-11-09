from rest_framework import serializers

from .models import Payout


class PayoutSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source="group.name", read_only=True)
    price_per_gram = serializers.DecimalField(source="custodian_transaction.price_per_gram", max_digits=14,
                                              decimal_places=4, read_only=True)
    custodian_reference = serializers.CharField(source="custodian_transaction.reference", read_only=True)

    class Meta:
        model = Payout
        fields = ["id", "group", "group_name", "kind", "cycle", "grams", "amount_zmw", "price_per_gram",
                  "status", "payment_reference", "custodian_reference", "created_at"]


class WithdrawSerializer(serializers.Serializer):
    group = serializers.IntegerField()
    grams = serializers.DecimalField(max_digits=14, decimal_places=4, min_value=0)
