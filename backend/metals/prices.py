"""Metal price providers. Prices are stored in ZMW per gram."""

import json
import logging
import random
import urllib.error
import urllib.request
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings

from .fx import usd_zmw_rate
from .models import Metal, MetalPrice

logger = logging.getLogger("treadstone.prices")

FOUR_DP = Decimal("0.0001")
TROY_OUNCE_GRAMS = Decimal("31.1034768")
GOLDAPI_BASE = "https://www.goldapi.io/api"

# Starting points for the simulated feed, USD per gram.
SIMULATED_BASE_USD = {Metal.GOLD: Decimal("85.00"), Metal.SILVER: Decimal("1.00")}


class PriceError(Exception):
    pass


def simulated_price(metal):
    """Random walk of at most +/-0.5% from the last stored price."""
    last = MetalPrice.objects.filter(metal=metal).first()
    if last:
        base = last.price_per_gram
    else:
        base = SIMULATED_BASE_USD[metal] * usd_zmw_rate()[0]
    drift = Decimal(str(random.uniform(-0.005, 0.005)))
    return (base * (1 + drift)).quantize(FOUR_DP, ROUND_HALF_UP)


def goldapi_get(path):
    """GET a GoldAPI endpoint and return the parsed JSON."""
    if not settings.GOLDAPI_KEY:
        raise PriceError("GOLDAPI_KEY is not set")
    req = urllib.request.Request(
        f"{GOLDAPI_BASE}/{path}",
        headers={"x-access-token": settings.GOLDAPI_KEY, "Accept": "application/json", "User-Agent": "Treadstone/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        raise PriceError(f"GoldAPI {path} returned HTTP {e.code}: {e.read()[:200]!r}") from e
    if isinstance(data, dict) and data.get("error"):
        raise PriceError(f"GoldAPI {path}: {data['error']}")
    return data


def goldapi_price(metal):
    """Live spot price from GoldAPI (USD), converted to ZMW per gram at today's exchange rate."""
    data = goldapi_get(f"price/{metal}/USD")
    per_unit = data.get("price_per_unit") or {}
    if per_unit.get("gram"):
        usd_per_gram = Decimal(str(per_unit["gram"]))
    else:
        usd_per_gram = Decimal(str(data["price"])) / TROY_OUNCE_GRAMS
    rate, fx_source = usd_zmw_rate()
    logger.info("%s $%s/g x %s ZMW/USD (%s)", metal, usd_per_gram, rate, fx_source)
    return (usd_per_gram * rate).quantize(FOUR_DP, ROUND_HALF_UP)


PROVIDERS = {"simulated": simulated_price, "goldapi": goldapi_price}


def fetch_and_store(metal):
    """Fetch from the configured provider and store it. On failure nothing is stored,
    so the app keeps showing the last good price (with its timestamp)."""
    name = settings.METAL_PRICE_PROVIDER
    provider = PROVIDERS.get(name)
    if provider is None:
        raise PriceError(f"Unknown METAL_PRICE_PROVIDER '{name}'")
    price = provider(metal)
    return MetalPrice.objects.create(metal=metal, price_per_gram=price, source=name)


def latest_price(metal):
    """The most recent stored price. If there is none yet, fetch one; if the live
    provider is unreachable then, fall back to a simulated price labelled as such."""
    price = MetalPrice.objects.filter(metal=metal).first()
    if price:
        return price
    try:
        return fetch_and_store(metal)
    except Exception:
        logger.exception("No stored %s price and the live fetch failed; using a simulated fallback", metal)
        return MetalPrice.objects.create(metal=metal, price_per_gram=simulated_price(metal), source="simulated-fallback")
