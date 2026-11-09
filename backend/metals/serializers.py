from rest_framework import serializers

from .models import CustodianTransaction, MetalPrice


class MetalPriceSerializer(serializers.ModelSerializer):
    metal_name = serializers.CharField(source="get_metal_display", read_only=True)

    class Meta:
        model = MetalPrice
        fields = ["metal", "metal_name", "price_per_gram", "source", "fetched_at"]


class CustodianTransactionSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source="group.name", read_only=True)

    class Meta:
        model = CustodianTransaction
        fields = ["id", "kind", "metal", "grams", "price_per_gram", "gross_zmw", "fee_zmw",
                  "group", "group_name", "reference", "created_at"]
