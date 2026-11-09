"""USD -> ZMW exchange rates. GoldAPI quotes metals in USD only (it has no ZMW),
so every Kwacha price is the USD price times one of these rates."""

import json
import logging
import urllib.request
from decimal import Decimal

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger("treadstone.prices")

HEADERS = {"User-Agent": "Treadstone/1.0", "Accept": "application/json"}

# Live sources, tried in order. Both are free and need no key.
LIVE_SOURCES = [
    ("open.er-api.com", "https://open.er-api.com/v6/latest/USD", lambda j: j["rates"]["ZMW"]),
    ("currency-api", "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.json",
     lambda j: j["usd"]["zmw"]),
]
# Daily history: one file per date.
HISTORY_URL = "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@{date}/v1/currencies/usd.json"

CACHE_KEY = "fx:usd_zmw"
CACHE_SECONDS = 60 * 60  # the rate moves slowly; one lookup an hour is plenty


def _get_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def usd_zmw_rate():
    """Today's USD->ZMW rate as (rate, source). Falls back to USD_ZMW_RATE in .env."""
    cached = cache.get(CACHE_KEY)
    if cached:
        return cached
    for name, url, pick in LIVE_SOURCES:
        try:
            rate = Decimal(str(pick(_get_json(url))))
            if rate > 0:
                cache.set(CACHE_KEY, (rate, name), CACHE_SECONDS)
                return rate, name
        except Exception:
            logger.warning("FX source %s failed", name, exc_info=True)
    logger.warning("All FX sources failed; using USD_ZMW_RATE=%s from .env", settings.USD_ZMW_RATE)
    return settings.USD_ZMW_RATE, "env-fallback"


def historical_usd_zmw(day):
    """USD->ZMW on a past date (datetime.date), or None if that day isn't available."""
    try:
        return Decimal(str(_get_json(HISTORY_URL.format(date=day.isoformat()))["usd"]["zmw"]))
    except Exception:
        return None
