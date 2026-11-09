from decimal import ROUND_DOWN, Decimal

from django.conf import settings
from django.contrib import admin, messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import path, reverse
from django.utils.html import format_html

from config.errors import DomainError
from members.admin import local_phone
from metals.prices import latest_price

from . import services
from .models import Loan, LoanRepayment

STATUS_CHIP = {
    Loan.Status.PENDING: "gold",
    Loan.Status.ACTIVE: "positive",
    Loan.Status.REPAID: "neutral",
    Loan.Status.REJECTED: "negative",
}


class LoanRepaymentInline(admin.TabularInline):
    model = LoanRepayment
    extra = 0
    can_delete = False
    readonly_fields = ["amount", "payment_reference", "created_at"]
    verbose_name_plural = "Loan repayments"

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ["id", "member", "group", "principal", "total_due", "amount_repaid", "collateral_grams", "status_chip", "created_at"]
    list_display_links = ["id", "member"]
    list_filter = ["status", "group"]
    search_fields = ["member__phone", "member__first_name", "member__last_name"]
    search_help_text = "Member name or phone"
    inlines = [LoanRepaymentInline]
    actions = ["approve", "reject"]
    change_form_template = "admin/loans/loan/change_form.html"
    fieldsets = (
        ("Borrower", {"fields": ("member", "group", "disburse_to")}),
        ("Terms", {"fields": ("principal", "interest_percent", "limit_now", "summary_tiles")}),
        ("Decision", {"fields": ("status", "reviewed_by", "reviewed_at", "disbursement_reference")}),
    )

    # Loans only change through the service layer (approve / reject / repay), never by hand.
    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in Loan._meta.fields] + ["disburse_to", "limit_now", "summary_tiles"]

    def has_add_permission(self, request):
        return False

    @admin.display(description="Status", ordering="status")
    def status_chip(self, obj):
        return format_html('<span class="ts-chip ts-chip--{}">{}</span>', STATUS_CHIP[obj.status], obj.get_status_display())

    @admin.display(description="Disburse to")
    def disburse_to(self, obj):
        return format_html('<span class="ts-mono">Mobile money · {}</span>', local_phone(obj.member.phone))

    @admin.display(description="Limit right now")
    def limit_now(self, obj):
        if obj.status != Loan.Status.PENDING:
            return "—"
        # This loan's own collateral is already locked, so add it back to see the limit it was judged against.
        available = services.available_grams(obj.member, obj.group) + obj.collateral_grams
        price = latest_price(obj.group.metal).price_per_gram
        limit = (available * price * settings.LOAN_TO_VALUE).quantize(Decimal("0.01"), ROUND_DOWN)
        return format_html(
            '<span class="ts-mono">K{}</span> <span class="ts-muted">(50% of {} g available, at K{} / g)</span>',
            f"{limit:,.2f}", f"{available:.4f}", f"{price:,.2f}",
        )

    @admin.display(description="")
    def summary_tiles(self, obj):
        return format_html(
            '<div class="ts-tiles" style="padding:0">'
            '<div class="ts-tile"><span class="ts-tile__label">Total repayable</span><span class="ts-tile__value">K{}</span></div>'
            '<div class="ts-tile"><span class="ts-tile__label">Still owed</span><span class="ts-tile__value">K{}</span></div>'
            '<div class="ts-tile ts-tile--gold"><span class="ts-tile__label">Gold held as collateral</span><span class="ts-tile__value">{} g</span></div>'
            "</div>",
            f"{obj.total_due:,.2f}", f"{obj.outstanding:,.2f}", f"{obj.collateral_grams:.4f}",
        )

    # --- approve / reject: list actions and buttons on the loan page ---------

    def get_urls(self):
        own = [
            path("<int:pk>/approve/", self.admin_site.admin_view(self.approve_view), name="loans_loan_approve"),
            path("<int:pk>/reject/", self.admin_site.admin_view(self.reject_view), name="loans_loan_reject"),
        ]
        return own + super().get_urls()

    def _decide(self, request, pk, fn, verb):
        loan = get_object_or_404(Loan, pk=pk)
        if request.method != "POST" or not self.has_change_permission(request, loan):
            messages.error(request, "Not allowed.")
        else:
            try:
                fn(loan=loan, by=request.user)
                messages.success(request, f"Loan #{loan.pk} {verb}.")
            except DomainError as e:
                messages.error(request, f"Loan #{loan.pk}: {e}")
        return redirect(reverse("admin:loans_loan_change", args=[pk]))

    def approve_view(self, request, pk):
        return self._decide(request, pk, services.approve_loan, "approved and disbursed")

    def reject_view(self, request, pk):
        return self._decide(request, pk, services.reject_loan, "rejected")

    def _run(self, request, queryset, fn, verb):
        for loan in queryset:
            try:
                fn(loan=loan, by=request.user)
                self.message_user(request, f"Loan #{loan.pk} {verb}.")
            except DomainError as e:
                self.message_user(request, f"Loan #{loan.pk}: {e}", messages.ERROR)

    @admin.action(description="Approve and disburse selected loans")
    def approve(self, request, queryset):
        self._run(request, queryset, services.approve_loan, "approved")

    @admin.action(description="Reject selected loans")
    def reject(self, request, queryset):
        self._run(request, queryset, services.reject_loan, "rejected")
