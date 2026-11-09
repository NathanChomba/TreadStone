from django.contrib import admin, messages

from . import services

from .models import Contribution, Membership, SavingsGroup


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 0


@admin.register(SavingsGroup)
class SavingsGroupAdmin(admin.ModelAdmin):
    list_display = ["name", "group_type", "metal", "contribution_amount", "frequency", "status", "current_cycle", "invite_code"]
    list_filter = ["group_type", "metal", "status"]
    search_fields = ["name", "invite_code"]
    inlines = [MembershipInline]
    actions = ["buy_gold_now"]

    @admin.action(description="Buy gold now for received contributions (normally done on the due date)")
    def buy_gold_now(self, request, queryset):
        for group in queryset:
            n = services.buy_gold_for_group(group)
            self.message_user(request, f"{group.name}: gold bought for {n} contribution(s).",
                              messages.SUCCESS if n else messages.INFO)


@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = ["reference", "member", "group", "cycle", "amount", "status", "provider", "created_at"]
    list_filter = ["status", "group"]
    search_fields = ["member__phone", "payment_reference"]
    readonly_fields = ["custodian_transaction"]
