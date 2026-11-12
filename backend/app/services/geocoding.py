"""Resolve a free-text location query into one or more concrete coordinates.

Routing:
- coordinates → Open-Meteo reverse geocoding
- postal code → Nominatim structured postalcode search
- free text  → Nominatim free-text search, falling back to Open-Meteo geocoding
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any

from app.config import settings
from app.errors import LocationNotFound, UpstreamFailure
from app.services import http
from app.services.cache import TTLCache
from app.utils.input_detect import DetectedInput, detect_input

_NOMINATIM_BASE = "https://nominatim.openstreetmap.org"
_OM_GEOCODE = "https://geocoding-api.open-meteo.com/v1/search"
_OM_REVERSE = "https://geocoding-api.open-meteo.com/v1/reverse"

_CACHE_TTL_SECONDS = 24 * 60 * 60
_NOMINATIM_MIN_INTERVAL = 1.0  # seconds; Nominatim policy is ≤ 1 req/s.


@dataclass(frozen=True)
class LocationCandidate:
    display_name: str
    lat: float
    lon: float
    country: str | None = None
    region: str | None = None
    timezone: str | None = None
    source: str = "nominatim"

    def to_dict(self) -> dict[str, Any]:
        return {
            "display_name": self.display_name,
            "lat": self.lat,
            "lon": self.lon,
            "country": self.country,
            "region": self.region,
            "timezone": self.timezone,
            "source": self.source,
        }


_cache: TTLCache[list[LocationCandidate]] = TTLCache(_CACHE_TTL_SECONDS)
_nominatim_lock = asyncio.Lock()
_last_nominatim_call: float = 0.0


async def _nominatim_rate_limit() -> None:
    """Ensure at most one Nominatim call per second (per process)."""
    global _last_nominatim_call
    async with _nominatim_lock:
        delta = time.monotonic() - _last_nominatim_call
        if delta < _NOMINATIM_MIN_INTERVAL:
            await asyncio.sleep(_NOMINATIM_MIN_INTERVAL - delta)
        _last_nominatim_call = time.monotonic()


def _ua_headers() -> dict[str, str]:
    return {"User-Agent": settings.nominatim_user_agent}


def _parse_nominatim(results: list[dict[str, Any]]) -> list[LocationCandidate]:
    out: list[LocationCandidate] = []
    for item in results:
        try:
            lat = float(item["lat"])
            lon = float(item["lon"])
        except (KeyError, TypeError, ValueError):
            continue
        address = item.get("address") or {}
        country = address.get("country")
        region = address.get("state") or address.get("region") or address.get("county")
        out.append(
            LocationCandidate(
                display_name=item.get("display_name", ""),
                lat=lat,
                lon=lon,
                country=country,
                region=region,
                source="nominatim",
            )
        )
    return out


def _parse_open_meteo(payload: dict[str, Any]) -> list[LocationCandidate]:
    results = payload.get("results") or []
    out: list[LocationCandidate] = []
    for item in results:
        try:
            lat = float(item["latitude"])
            lon = float(item["longitude"])
        except (KeyError, TypeError, ValueError):
            continue
        parts = [
            part
            for part in (item.get("name"), item.get("admin1"), item.get("country"))
            if part
        ]
        out.append(
            LocationCandidate(
                display_name=", ".join(parts) or item.get("name", ""),
                lat=lat,
                lon=lon,
                country=item.get("country"),
                region=item.get("admin1"),
                timezone=item.get("timezone"),
                source="open-meteo",
            )
        )
    return out


async def _nominatim_search(params: dict[str, Any]) -> list[LocationCandidate]:
    await _nominatim_rate_limit()
    data = await http.get_json(
        f"{_NOMINATIM_BASE}/search",
        params={**params, "format": "jsonv2", "addressdetails": 1, "limit": 5},
        headers=_ua_headers(),
        upstream_name="nominatim",
    )
    if not isinstance(data, list):
        raise UpstreamFailure("Unexpected nominatim response.")
    return _parse_nominatim(data)


async def _nominatim_reverse(lat: float, lon: float) -> list[LocationCandidate]:
    await _nominatim_rate_limit()
    data = await http.get_json(
        f"{_NOMINATIM_BASE}/reverse",
        params={"lat": lat, "lon": lon, "format": "jsonv2", "addressdetails": 1},
        headers=_ua_headers(),
        upstream_name="nominatim",
    )
    if not isinstance(data, dict):
        raise UpstreamFailure("Unexpected nominatim reverse response.")
    return _parse_nominatim([data])


async def _open_meteo_search(name: str, count: int = 5) -> list[LocationCandidate]:
    data = await http.get_json(
        _OM_GEOCODE,
        params={"name": name, "count": count, "language": "en", "format": "json"},
        upstream_name="open-meteo geocoding",
    )
    if not isinstance(data, dict):
        raise UpstreamFailure("Unexpected open-meteo geocoding response.")
    return _parse_open_meteo(data)


async def autocomplete(query: str, limit: int = 6) -> list[LocationCandidate]:
    """Lightweight suggestions as the user types, via Open-Meteo.

    Deliberately skips Nominatim (whose policy forbids autocomplete use).
    Returns an empty list for very short queries so clients don't hammer
    the API on every keystroke.
    """
    text = query.strip()
    if len(text) < 2:
        return []
    try:
        return await _open_meteo_search(text, count=limit)
    except UpstreamFailure:
        return []


async def _open_meteo_reverse(lat: float, lon: float) -> list[LocationCandidate]:
    data = await http.get_json(
        _OM_REVERSE,
        params={"latitude": lat, "longitude": lon, "language": "en", "format": "json"},
        upstream_name="open-meteo reverse",
    )
    if not isinstance(data, dict):
        return []
    return _parse_open_meteo(data)


def _cache_key(detected: DetectedInput) -> str:
    if detected.kind == "coordinates":
        return f"coord:{detected.lat:.4f},{detected.lon:.4f}"
    if detected.kind == "postal_code":
        return f"postal:{detected.country_hint or '*'}:{detected.postal_code}"
    return f"text:{detected.raw.lower()}"


async def resolve_location(query: str) -> list[LocationCandidate]:
    """Resolve the query into one or more candidate locations.

    Raises `LocationNotFound` if nothing matches. Ambiguity (>1 result) is
    returned to the caller to decide how to surface it.
    """
    detected = detect_input(query)
    if detected.kind == "free_text" and not detected.raw:
        raise LocationNotFound("Empty location query.")

    cache_key = _cache_key(detected)
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    candidates: list[LocationCandidate] = []
    if detected.kind == "coordinates":
        assert detected.lat is not None and detected.lon is not None
        candidates = await _nominatim_reverse(detected.lat, detected.lon)
        if not candidates:
            candidates = await _open_meteo_reverse(detected.lat, detected.lon)
        if not candidates:
            # Still surface the raw point so callers can proceed.
            candidates = [
                LocationCandidate(
                    display_name=f"{detected.lat:.4f}, {detected.lon:.4f}",
                    lat=detected.lat,
                    lon=detected.lon,
                    source="coordinates",
                )
            ]
    elif detected.kind == "postal_code":
        params: dict[str, Any] = {"postalcode": detected.postal_code}
        if detected.country_hint:
            params["countrycodes"] = detected.country_hint
        candidates = await _nominatim_search(params)
    else:
        candidates = await _nominatim_search({"q": detected.raw})
        if not candidates:
            candidates = await _open_meteo_search(detected.raw)

    if not candidates:
        raise LocationNotFound(
            "No location matches the query.",
            details={"query": detected.raw},
        )

    _cache.set(cache_key, candidates)
    return candidates


def clear_cache_for_tests() -> None:
    """Expose cache clearing to tests without touching the module global."""
    global _last_nominatim_call
    _cache.clear()
    _last_nominatim_call = 0.0
