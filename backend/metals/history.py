"""Price history for charts, downsampled so a year of 15-minute prices stays small."""

from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.utils import timezone

from .models import MetalPrice

RANGES = {"1D": timedelta(days=1), "1W": timedelta(weeks=1), "1M": timedelta(days=30),
          "6M": timedelta(days=182), "1Y": timedelta(days=365)}
MAX_POINTS = 60


def history(metal, range_key="1M"):
    span = RANGES.get(range_key, RANGES["1M"])
    since = timezone.now() - span
    rows = list(
        MetalPrice.objects.filter(metal=metal, fetched_at__gte=since).order_by("fetched_at").values_list("fetched_at", "price_per_gram")
    )
    # Keep the last price in each of MAX_POINTS equal time buckets, and always the newest price.
    if len(rows) > MAX_POINTS:
        bucket = span / MAX_POINTS
        kept = {}
        for t, p in rows:
            kept[int((t - since) / bucket)] = (t, p)
        sampled = [kept[k] for k in sorted(kept)]
        if sampled[-1] != rows[-1]:
            sampled.append(rows[-1])
        rows = sampled
    change_pct = None
    if len(rows) >= 2 and rows[0][1]:
        change_pct = ((rows[-1][1] - rows[0][1]) / rows[0][1] * 100).quantize(Decimal("0.01"), ROUND_HALF_UP)
    return {
        "metal": metal,
        "range": range_key if range_key in RANGES else "1M",
        "points": [{"t": t, "price": str(p)} for t, p in rows],
        "change_pct": str(change_pct) if change_pct is not None else None,
    }


def change_since(metal, hours=24):
    """Percentage move between the newest price and the price `hours` ago, or None."""
    latest = MetalPrice.objects.filter(metal=metal).first()
    if latest is None:
        return None
    past = MetalPrice.objects.filter(metal=metal, fetched_at__lte=latest.fetched_at - timedelta(hours=hours)).first()
    if past is None or not past.price_per_gram:
        return None
    return (latest.price_per_gram - past.price_per_gram) / past.price_per_gram * 100
