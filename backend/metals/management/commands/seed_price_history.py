import random
from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from metals.models import Metal, MetalPrice
from metals.prices import latest_price


class Command(BaseCommand):
    help = (
        "Backfill SIMULATED daily metal prices so the 1W/1M/6M/1Y charts have something to show. "
        "Only runs while METAL_PRICE_PROVIDER=simulated. Rows are marked source='simulated-history'."
    )

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=365)
        parser.add_argument("--replace", action="store_true", help="Delete earlier simulated history first")

    def handle(self, *args, days, replace, **options):
        if settings.METAL_PRICE_PROVIDER != "simulated":
            raise CommandError("Refusing to invent history while a real price provider is configured.")
        if replace:
            MetalPrice.objects.filter(source="simulated-history").delete()
        now = timezone.now()
        for metal in Metal.values:
            oldest_real = MetalPrice.objects.filter(metal=metal).exclude(source="simulated-history").order_by("fetched_at").first()
            anchor = oldest_real or latest_price(metal)
            price = anchor.price_per_gram
            start = anchor.fetched_at
            rows = []
            # Walk backwards from the oldest real price, one point a day, drifting a little upward over time.
            for d in range(1, days + 1):
                price = (price / Decimal(str(1 + random.uniform(-0.012, 0.0145)))).quantize(Decimal("0.0001"), ROUND_HALF_UP)
                rows.append(MetalPrice(metal=metal, price_per_gram=price, source="simulated-history",
                                       fetched_at=start - timedelta(days=d)))
            MetalPrice.objects.bulk_create(rows)
            self.stdout.write(f"{metal}: {len(rows)} simulated daily prices back to {(start - timedelta(days=days)):%d %b %Y}")
        self.stdout.write(self.style.SUCCESS(f"Done ({now:%H:%M})."))
