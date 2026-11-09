from django.contrib import admin

from .models import Payout


@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = ["member", "group", "kind", "cycle", "grams", "amount_zmw", "status", "payment_reference", "created_at"]
    list_filter = ["kind", "status", "group"]
    search_fields = ["member__phone", "payment_reference"]

    def has_change_permission(self, request, obj=None):
        return False
