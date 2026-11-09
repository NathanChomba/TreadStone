from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from savings.models import SavingsGroup

from .models import Payout
from .serializers import PayoutSerializer, WithdrawSerializer
from .services import withdraw


class MyPayoutsView(generics.ListAPIView):
    """GET /api/payouts/"""

    serializer_class = PayoutSerializer

    def get_queryset(self):
        return Payout.objects.filter(member=self.request.user).select_related("group", "custodian_transaction")


class WithdrawView(APIView):
    """POST /api/payouts/withdraw/ {group, grams} - annuity withdrawal."""

    def post(self, request):
        s = WithdrawSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        group = get_object_or_404(SavingsGroup, pk=s.validated_data["group"], memberships__member=request.user)
        payout = withdraw(member=request.user, group=group, grams=s.validated_data["grams"])
        return Response(PayoutSerializer(payout).data, status=status.HTTP_201_CREATED)
