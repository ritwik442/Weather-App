from __future__ import annotations

import httpx
import pytest
import respx

from app.services import extras


def _wiki_payload(title: str = "Paris", extract: str = "Capital of France.") -> dict:
    return {
        "title": title,
        "extract": extract,
        "type": "standard",
        "content_urls": {"desktop": {"page": f"https://en.wikipedia.org/wiki/{title}"}},
        "thumbnail": {"source": "https://example.com/thumb.jpg"},
    }


def _aqi_payload() -> dict:
    return {
        "current": {
            "time": "2026-01-01T12:00",
            "european_aqi": 42,
            "us_aqi": 55,
            "pm10": 21.5,
            "pm2_5": 10.1,
            "ozone": 60.0,
        }
    }


@pytest.mark.asyncio
async def test_fetch_extras_all_pieces_succeed(monkeypatch) -> None:
    monkeypatch.setattr("app.config.settings.youtube_api_key", "", raising=False)
    with respx.mock(assert_all_called=False) as mock:
        mock.get("https://en.wikipedia.org/api/rest_v1/page/summary/Paris").mock(
            return_value=httpx.Response(200, json=_wiki_payload())
        )
        mock.get("https://air-quality-api.open-meteo.com/v1/air-quality").mock(
            return_value=httpx.Response(200, json=_aqi_payload())
        )
        payload = await extras.fetch_extras(48.85, 2.35, "Paris")

    # YouTube: no API key → fallback URL, empty videos, no error
    assert payload["videos"]["error"] is None
    assert payload["videos"]["value"]["videos"] == []
    assert "search_query=weather" in payload["videos"]["value"]["search_url"]
    assert payload["videos"]["value"]["has_key"] is False

    # Wikipedia + AQI succeed
    assert payload["wikipedia"]["error"] is None
    assert payload["wikipedia"]["value"]["title"] == "Paris"
    assert payload["air_quality"]["error"] is None
    assert payload["air_quality"]["value"]["pm2_5"] == 10.1

    # Map piece is always present
    assert payload["map"]["error"] is None
    assert payload["map"]["value"]["google_maps_url"].endswith("48.85,2.35")


@pytest.mark.asyncio
async def test_wikipedia_failure_does_not_poison_other_pieces() -> None:
    with respx.mock(assert_all_called=False) as mock:
        mock.get("https://en.wikipedia.org/api/rest_v1/page/summary/Paris").mock(
            return_value=httpx.Response(500, json={"error": "boom"})
        )
        mock.get("https://air-quality-api.open-meteo.com/v1/air-quality").mock(
            return_value=httpx.Response(200, json=_aqi_payload())
        )
        payload = await extras.fetch_extras(48.85, 2.35, "Paris")

    assert payload["wikipedia"]["value"] is None
    assert payload["wikipedia"]["error"] and payload["wikipedia"]["error"].startswith("wikipedia:")
    assert payload["air_quality"]["value"]["pm2_5"] == 10.1
    assert payload["map"]["value"] is not None


@pytest.mark.asyncio
async def test_all_remote_pieces_fail_map_still_present() -> None:
    with respx.mock(assert_all_called=False) as mock:
        mock.get("https://en.wikipedia.org/api/rest_v1/page/summary/Paris").mock(
            side_effect=httpx.ConnectTimeout("nope")
        )
        mock.get("https://air-quality-api.open-meteo.com/v1/air-quality").mock(
            side_effect=httpx.ConnectTimeout("nope")
        )
        payload = await extras.fetch_extras(48.85, 2.35, "Paris")

    assert payload["wikipedia"]["error"] is not None
    assert payload["air_quality"]["error"] is not None
    assert payload["map"]["value"] is not None
    assert payload["videos"]["value"]["search_url"]  # fallback link is always available


@pytest.mark.asyncio
async def test_youtube_with_key_parses_items(monkeypatch) -> None:
    monkeypatch.setattr("app.config.settings.youtube_api_key", "fake-key", raising=False)
    sample = {
        "items": [
            {
                "id": {"videoId": "abc123"},
                "snippet": {
                    "title": "Weather in Paris",
                    "channelTitle": "SomeChannel",
                    "publishedAt": "2026-01-01T00:00:00Z",
                    "thumbnails": {"medium": {"url": "https://img.example/t.jpg"}},
                },
            }
        ]
    }
    with respx.mock(assert_all_called=False) as mock:
        mock.get("https://www.googleapis.com/youtube/v3/search").mock(
            return_value=httpx.Response(200, json=sample)
        )
        mock.get("https://en.wikipedia.org/api/rest_v1/page/summary/Paris").mock(
            return_value=httpx.Response(200, json=_wiki_payload())
        )
        mock.get("https://air-quality-api.open-meteo.com/v1/air-quality").mock(
            return_value=httpx.Response(200, json=_aqi_payload())
        )
        payload = await extras.fetch_extras(48.85, 2.35, "Paris")

    videos = payload["videos"]["value"]["videos"]
    assert len(videos) == 1
    assert videos[0]["id"] == "abc123"
    assert videos[0]["url"].endswith("abc123")
    assert payload["videos"]["value"]["has_key"] is True


def test_extras_endpoint_wiring(client, monkeypatch) -> None:
    monkeypatch.setattr("app.config.settings.youtube_api_key", "", raising=False)
    with respx.mock(assert_all_called=False) as mock:
        mock.get("https://en.wikipedia.org/api/rest_v1/page/summary/Paris").mock(
            return_value=httpx.Response(200, json=_wiki_payload())
        )
        mock.get("https://air-quality-api.open-meteo.com/v1/air-quality").mock(
            return_value=httpx.Response(200, json=_aqi_payload())
        )
        r = client.get("/api/v1/locations/extras?lat=48.85&lon=2.35&name=Paris")
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"videos", "wikipedia", "air_quality", "map"}


def test_extras_endpoint_validates_coords(client) -> None:
    r = client.get("/api/v1/locations/extras?lat=100&lon=2.35&name=Paris")
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_FAILED"
