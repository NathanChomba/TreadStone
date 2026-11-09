from decimal import Decimal

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html, format_html_join

from metals import custodian

from .models import Member, MobileWallet, Notification

KYC_CHIP = {
    Member.KYC.VERIFIED: "positive",
    Member.KYC.PENDING: "gold",
    Member.KYC.REJECTED: "negative",
}


def local_phone(phone):
    """+260971234567 -> 097 123 4567, the way members write their number."""
    if phone and phone.startswith("+260") and len(phone) == 13:
        d = "0" + phone[4:]
        return f"{d[:3]} {d[3:6]} {d[6:]}"
    return phone


class GroupFilter(admin.SimpleListFilter):
    title = "group"
    parameter_name = "group"

    def lookups(self, request, model_admin):
        from savings.models import SavingsGroup

        return [(g.pk, g.name) for g in SavingsGroup.objects.order_by("name")]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(memberships__group_id=self.value()).distinct()
        return queryset


class WalletInline(admin.TabularInline):
    model = MobileWallet
    extra = 0
    fields = ["provider", "number", "is_default"]


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["member", "kind", "title", "read_at", "created_at"]
    list_filter = ["kind"]
    search_fields = ["member__phone", "title"]


@admin.register(Member)
class MemberAdmin(UserAdmin):
    inlines = [WalletInline]
    ordering = ["first_name", "last_name"]
    list_display = ["name", "phone_display", "groups_display", "kyc_chip", "joined", "gold_share"]
    list_display_links = ["name"]
    list_filter = ["kyc_status", GroupFilter, "date_joined", "is_staff"]
    search_fields = ["phone", "first_name", "last_name", "nrc_number"]
    search_help_text = "Name, phone or NRC number"
    list_per_page = 25
    fieldsets = (
        (None, {"fields": ("phone", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "email", "nrc_number", "kyc_status")}),
        ("Preferences", {"fields": ("language", "sms_reminders", "price_alerts")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("phone", "first_name", "last_name", "password1", "password2"),
        }),
    )
    actions = ["verify_kyc", "reject_kyc"]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("memberships__group")

    @admin.display(description="Name", ordering="first_name")
    def name(self, obj):
        return obj.get_full_name() or obj.phone

    @admin.display(description="Phone", ordering="phone")
    def phone_display(self, obj):
        return format_html('<span class="ts-mono">{}</span>', local_phone(obj.phone))

    @admin.display(description="Groups")
    def groups_display(self, obj):
        ms = list(obj.memberships.all())
        if not ms:
            return format_html('<span class="ts-muted">—</span>')
        return format_html_join(
            ", ", "{}{}", ((m.group.name, " (admin)" if m.is_admin else "") for m in ms)
        )

    @admin.display(description="KYC", ordering="kyc_status")
    def kyc_chip(self, obj):
        return format_html(
            '<span class="ts-chip ts-chip--{}">{}</span>', KYC_CHIP.get(obj.kyc_status, "neutral"),
            obj.get_kyc_status_display(),
        )

    @admin.display(description="Joined", ordering="date_joined")
    def joined(self, obj):
        return obj.date_joined.strftime("%d %b %Y").lstrip("0")  # e.g. 3 Nov 2026

    @admin.display(description="Gold share")
    def gold_share(self, obj):
        grams = sum((custodian.member_grams(obj, m.group) for m in obj.memberships.all()), Decimal("0"))
        return f"{max(grams, Decimal('0')):.4f} g"

    @admin.action(description="Mark KYC as verified")
    def verify_kyc(self, request, queryset):
        queryset.update(kyc_status=Member.KYC.VERIFIED)

    @admin.action(description="Mark KYC as rejected")
    def reject_kyc(self, request, queryset):
        queryset.update(kyc_status=Member.KYC.REJECTED)
