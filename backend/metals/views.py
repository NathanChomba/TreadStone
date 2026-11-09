from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CustodianTransaction, Metal, MetalPrice
from . import custodian
from .history import history
from .prices import latest_price
from .serializers import CustodianTransactionSerializer, MetalPriceSerializer


class LatestPricesView(APIView):
    """GET /api/metals/prices/latest/ - public, cached offline by the PWA."""

    permission_classes = [AllowAny]

    def get(self, request):
        return Response([MetalPriceSerializer(latest_price(m)).data for m in Metal.values])


class PriceHistoryView(generics.ListAPIView):
    """GET /api/metals/prices/?metal=XAU"""

    permission_classes = [AllowAny]
    serializer_class = MetalPriceSerializer

    def get_queryset(self):
        qs = MetalPrice.objects.all()
        metal = self.request.query_params.get("metal")
        return qs.filter(metal=metal) if metal else qs


class MyLedgerView(generics.ListAPIView):
    """GET /api/metals/ledger/ - the current member's custodian deals."""

    serializer_class = CustodianTransactionSerializer

    def get_queryset(self):
        return CustodianTransaction.objects.filter(member=self.request.user).select_related("group")


class PriceHistoryRangeView(APIView):
    """GET /api/metals/history/?metal=XAU&range=1W|1M|6M|1Y"""

    permission_classes = [AllowAny]

    def get(self, request):
        metal = request.query_params.get("metal", Metal.GOLD)
        if metal not in Metal.values:
            return Response({"detail": "Unknown metal"}, status=400)
        return Response(history(metal, request.query_params.get("range", "1M")))


class QuoteView(APIView):
    """GET /api/metals/quote/?metal=XAU&amount=1000 - roughly what the money buys at today's price."""

    def get(self, request):
        from decimal import Decimal, InvalidOperation

        metal = request.query_params.get("metal", Metal.GOLD)
        try:
            amount = Decimal(request.query_params.get("amount", "0"))
        except InvalidOperation:
            return Response({"detail": "Amount must be a number"}, status=400)
        if metal not in Metal.values or amount <= 0:
            return Response({"detail": "Give a metal and a positive amount"}, status=400)
        grams, fee, price = custodian.quote(metal, amount)
        return Response({
            "metal": metal, "amount": str(amount.quantize(Decimal("0.01"))), "grams": str(grams),
            "fee_zmw": str(fee), "price_per_gram": str(price.price_per_gram), "fetched_at": price.fetched_at,
        })
