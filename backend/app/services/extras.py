"""Location extras: videos, map, air quality, Wikipedia.

Each piece is fetched independently. A failure in one does not affect the
others — the endpoint returns `{value: null, error: "..."}` for the pieces
that could not be fetched.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote_plus

from app.config import settings
from app.services import http
from app.services.cache import TTLCache

_AQI_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
_YOUTUBE_URL = "https://www.googleapis.com/youtube/v3/search"
_WIKIPEDIA_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/"

_CACHE_TTL = 15 * 60
_extras_cache: TTLCache[dict[str, Any]] = TTLCache(_CACHE_TTL)


@dataclass
class ExtraPiece:
    value: Any = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"value": self.value, "error": self.error}


def google_maps_link(lat: float, lon: float) -> str:
    return f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"


def youtube_search_url(name: str) -> str:
    return f"https://www.youtube.com/results?search_query={quote_plus(f'weather in {name}')}"


async def fetch_youtube(name: str) -> ExtraPiece:
    key = settings.youtube_api_key
    fallback = youtube_search_url(name)
    if not key:
        return ExtraPiece(value={"videos": [], "search_url": fallback, "has_key": False})
    try:
        data = await http.get_json(
            _YOUTUBE_URL,
            params={
                "part": "snippet",
                "q": f"weather in {name}",
                "type": "video",
                "maxResults": 5,
                "key": key,
            },
            upstream_name="youtube",
        )
    except Exception as exc:  # noqa: BLE001 - intentional isolation
        return ExtraPiece(
            value={"videos": [], "search_url": fallback, "has_key": True},
            error=f"youtube: {type(exc).__name__}",
        )
    videos: list[dict[str, Any]] = []
    if isinstance(data, dict):
        for item in data.get("items", []) or []:
            vid_id = (item.get("id") or {}).get("videoId")
            snippet = item.get("snippet") or {}
            if not vid_id:
                continue
            videos.append(
                {
                    "id": vid_id,
                    "title": snippet.get("title"),
                    "channel": snippet.get("channelTitle"),
                    "published_at": snippet.get("publishedAt"),
                    "thumbnail": (snippet.get("thumbnails") or {})
                    .get("medium", {})
                    .get("url"),
                    "url": f"https://www.youtube.com/watch?v={vid_id}",
                }
            )
    return ExtraPiece(value={"videos": videos, "search_url": fallback, "has_key": True})


async def fetch_wikipedia(name: str) -> ExtraPiece:
    title = name.split(",")[0].strip().replace(" ", "_")
    if not title:
        return ExtraPiece(error="wikipedia: empty title")
    try:
        data = await http.get_json(
            f"{_WIKIPEDIA_URL}{quote_plus(title)}",
            headers={"accept": "application/json"},
            upstream_name="wikipedia",
            retries=0,
        )
    except Exception as exc:  # noqa: BLE001
        return ExtraPiece(error=f"wikipedia: {type(exc).__name__}")
    if not isinstance(data, dict):
        return ExtraPiece(error="wikipedia: unexpected response")
    if data.get("type") == "disambiguation":
        return ExtraPiece(error="wikipedia: disambiguation page")
    return ExtraPiece(
        value={
            "title": data.get("title"),
            "extract": data.get("extract"),
            "url": (data.get("content_urls") or {}).get("desktop", {}).get("page"),
            "thumbnail": (data.get("thumbnail") or {}).get("source"),
        }
    )


async def fetch_air_quality(lat: float, lon: float) -> ExtraPiece:
    try:
        data = await http.get_json(
            _AQI_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "european_aqi,us_aqi,pm10,pm2_5,ozone",
            },
            upstream_name="open-meteo air-quality",
        )
    except Exception as exc:  # noqa: BLE001
        return ExtraPiece(error=f"air_quality: {type(exc).__name__}")
    if not isinstance(data, dict):
        return ExtraPiece(error="air_quality: unexpected response")
    current = data.get("current") or {}
    return ExtraPiece(
        value={
            "time": current.get("time"),
            "european_aqi": current.get("european_aqi"),
            "us_aqi": current.get("us_aqi"),
            "pm10": current.get("pm10"),
            "pm2_5": current.get("pm2_5"),
            "ozone": current.get("ozone"),
        }
    )


def map_piece(lat: float, lon: float) -> ExtraPiece:
    """Pure (no network) — can never fail, so always wrapped as value-only."""
    return ExtraPiece(
        value={
            "lat": lat,
            "lon": lon,
            "google_maps_url": google_maps_link(lat, lon),
            "osm_tile_url_template": (
                "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            ),
        }
    )


async def fetch_extras(lat: float, lon: float, name: str) -> dict[str, Any]:
    cache_key = f"{lat:.4f},{lon:.4f}:{name.lower()}"
    cached = _extras_cache.get(cache_key)
    if cached is not None:
        return cached

    youtube_task = asyncio.create_task(fetch_youtube(name))
    wiki_task = asyncio.create_task(fetch_wikipedia(name))
    aqi_task = asyncio.create_task(fetch_air_quality(lat, lon))
    await asyncio.gather(youtube_task, wiki_task, aqi_task, return_exceptions=True)

    def _safe(task: asyncio.Task[ExtraPiece], label: str) -> ExtraPiece:
        if task.cancelled() or task.exception() is not None:
            exc = task.exception() if not task.cancelled() else None
            return ExtraPiece(error=f"{label}: {type(exc).__name__ if exc else 'cancelled'}")
        return task.result()

    payload = {
        "videos": _safe(youtube_task, "youtube").to_dict(),
        "wikipedia": _safe(wiki_task, "wikipedia").to_dict(),
        "air_quality": _safe(aqi_task, "air_quality").to_dict(),
        "map": map_piece(lat, lon).to_dict(),
    }
    _extras_cache.set(cache_key, payload)
    return payload


def clear_cache_for_tests() -> None:
    _extras_cache.clear()
