from django.contrib import admin

from .models import CustodianTransaction, MetalPrice


@admin.register(MetalPrice)
class MetalPriceAdmin(admin.ModelAdmin):
    list_display = ["metal", "price_per_gram", "source", "fetched_at"]
    list_filter = ["metal", "source"]


@admin.register(CustodianTransaction)
class CustodianTransactionAdmin(admin.ModelAdmin):
    list_display = ["reference", "kind", "metal", "grams", "price_per_gram", "gross_zmw", "fee_zmw", "group", "member", "created_at"]
    list_filter = ["kind", "metal", "group"]
    search_fields = ["reference", "member__phone"]

    # The ledger is append-only.
    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
