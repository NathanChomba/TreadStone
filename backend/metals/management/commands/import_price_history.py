from datetime import date, datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from metals.fx import historical_usd_zmw, usd_zmw_rate
from metals.models import Metal, MetalPrice
from metals.prices import TROY_OUNCE_GRAMS, PriceError, goldapi_get

SOURCE = "goldapi-history"
SIMULATED_SOURCES = ["simulated", "simulated-history", "simulated-fallback"]
MAX_SPAN_DAYS = 90  # GoldAPI refuses history ranges longer than this


class Command(BaseCommand):
    help = (
        "Import REAL daily gold and silver prices from GoldAPI (USD, LBMA) and convert each day "
        "to ZMW per gram using that day's real USD->ZMW rate. Safe to re-run. Rows: source='goldapi-history'."
    )

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=365, help="How far back to import (default 365)")
        parser.add_argument("--replace", action="store_true",
                            help="Delete all simulated prices first so charts show real data only")

    def handle(self, *args, days, replace, **options):
        today = timezone.localdate()
        start = today - timedelta(days=days)
        end = today - timedelta(days=1)  # today comes from the live feed

        if replace:
            n, _ = MetalPrice.objects.filter(source__in=SIMULATED_SOURCES).delete()
            self.stdout.write(f"Removed {n} simulated price rows.")

        # 1. Daily USD prices per metal, fetched in <=90-day windows.
        usd = {m: {} for m in Metal.values}
        for metal in Metal.values:
            win_start = start
            while win_start <= end:
                win_end = min(win_start + timedelta(days=MAX_SPAN_DAYS - 1), end)
                try:
                    data = goldapi_get(f"history/{metal}/USD?from={win_start:%Y-%m-%d}&to={win_end:%Y-%m-%d}")
                except PriceError as e:
                    raise CommandError(str(e))
                for row in data.get("prices", []):
                    usd[metal][date.fromisoformat(row["date"])] = Decimal(str(row["price"]))
                win_start = win_end + timedelta(days=1)
            self.stdout.write(f"{metal}: {len(usd[metal])} daily USD prices")

        # 2. Real USD->ZMW for each of those days (one small request per day; gaps reuse the previous day).
        days_needed = sorted(set().union(*[set(d) for d in usd.values()]))
        self.stdout.write(f"Fetching USD->ZMW for {len(days_needed)} days...")
        rates, last_rate, missing = {}, None, 0
        for i, d in enumerate(days_needed, 1):
            r = historical_usd_zmw(d)
            if r is None:
                missing += 1
                r = last_rate
            rates[d] = last_rate = r
            if i % 60 == 0:
                self.stdout.write(f"  {i}/{len(days_needed)}")
        # Days before the first available FX file take the first known rate, not today's.
        first_known = next((r for r in rates.values() if r), None) or usd_zmw_rate()[0]
        rates = {d: (r or first_known) for d, r in rates.items()}
        if missing:
            self.stdout.write(f"  {missing} days had no FX file; used the previous day's rate.")

        # 3. Store, replacing any earlier import for the same window.
        tz = timezone.get_current_timezone()
        for metal in Metal.values:
            MetalPrice.objects.filter(metal=metal, source=SOURCE,
                                      fetched_at__date__gte=start, fetched_at__date__lte=end).delete()
            rows = [
                MetalPrice(
                    metal=metal, source=SOURCE,
                    price_per_gram=(p / TROY_OUNCE_GRAMS * rates[d]).quantize(Decimal("0.0001"), ROUND_HALF_UP),
                    fetched_at=timezone.make_aware(datetime.combine(d, time(12, 0)), tz),
                )
                for d, p in sorted(usd[metal].items())
            ]
            MetalPrice.objects.bulk_create(rows)
            if rows:
                self.stdout.write(f"{metal}: stored {len(rows)} days, "
                                  f"K{rows[0].price_per_gram}/g on {d_first(rows)} -> K{rows[-1].price_per_gram}/g on {d_last(rows)}")
        self.stdout.write(self.style.SUCCESS("Real price history imported."))


def d_first(rows):
    return f"{timezone.localtime(rows[0].fetched_at):%d %b %Y}"


def d_last(rows):
    return f"{timezone.localtime(rows[-1].fetched_at):%d %b %Y}"
