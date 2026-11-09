from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from savings.models import SavingsGroup

from . import services
from .models import Loan
from .serializers import AmountSerializer, LoanSerializer


class LoanViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin,
                  viewsets.GenericViewSet):
    """Members see their own loans. Staff (is_staff) also see and review everyone's."""

    serializer_class = LoanSerializer

    def get_queryset(self):
        qs = Loan.objects.select_related("group", "member").prefetch_related("repayments")
        if self.request.user.is_staff and self.request.query_params.get("all"):
            return qs
        return qs.filter(member=self.request.user)

    def create(self, request, *args, **kwargs):
        s = self.get_serializer(data=request.data)
        s.is_valid(raise_exception=True)
        loan = services.request_loan(
            member=request.user, group=s.validated_data["group"], amount=s.validated_data["principal"]
        )
        return Response(self.get_serializer(loan).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def repay(self, request, pk=None):
        s = AmountSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        loan = services.repay_loan(loan=self.get_object(), member=request.user, amount=s.validated_data["amount"])
        return Response(self.get_serializer(loan).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminUser])
    def approve(self, request, pk=None):
        loan = services.approve_loan(loan=get_object_or_404(Loan, pk=pk), by=request.user)
        return Response(self.get_serializer(loan).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminUser])
    def reject(self, request, pk=None):
        loan = services.reject_loan(loan=get_object_or_404(Loan, pk=pk), by=request.user)
        return Response(self.get_serializer(loan).data)


class LoanLimitView(APIView):
    """GET /api/loans/limit/?group=<id> - how much the member could borrow right now."""

    def get(self, request):
        group = get_object_or_404(SavingsGroup, pk=request.query_params.get("group"), memberships__member=request.user)
        if group.is_rotating:
            return Response({"max_loan": "0.00", "reason": "Loans are only available against annuity balances"})
        return Response({
            "max_loan": str(services.max_loan(request.user, group)),
            "available_grams": str(services.available_grams(request.user, group)),
        })
