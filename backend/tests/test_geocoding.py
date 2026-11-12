from __future__ import annotations

import httpx
import pytest
import respx

from app.errors import LocationNotFound, UpstreamTimeout
from app.services import geocoding


@pytest.mark.asyncio
async def test_free_text_hits_nominatim() -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock.get("https://nominatim.openstreetmap.org/search").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {
                        "lat": "48.8566",
                        "lon": "2.3522",
                        "display_name": "Paris, France",
                        "address": {"country": "France", "state": "Île-de-France"},
                    }
                ],
            )
        )
        results = await geocoding.resolve_location("Paris")
        assert len(results) == 1
        assert results[0].display_name == "Paris, France"
        assert results[0].country == "France"


@pytest.mark.asyncio
async def test_empty_nominatim_falls_back_to_open_meteo() -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock.get("https://nominatim.openstreetmap.org/search").mock(
            return_value=httpx.Response(200, json=[])
        )
        mock.get("https://geocoding-api.open-meteo.com/v1/search").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "name": "Rivendell",
                            "latitude": 45.0,
                            "longitude": 9.0,
                            "country": "Middle-Earth",
                            "admin1": "Eriador",
                            "timezone": "Europe/Rome",
                        }
                    ]
                },
            )
        )
        results = await geocoding.resolve_location("Rivendell")
        assert len(results) == 1
        assert results[0].source == "open-meteo"
        assert results[0].timezone == "Europe/Rome"


@pytest.mark.asyncio
async def test_no_matches_raises_location_not_found() -> None:
    with respx.mock(assert_all_called=False) as mock:
        mock.get("https://nominatim.openstreetmap.org/search").mock(
            return_value=httpx.Response(200, json=[])
        )
        mock.get("https://geocoding-api.open-meteo.com/v1/search").mock(
            return_value=httpx.Response(200, json={"results": []})
        )
        with pytest.raises(LocationNotFound):
            await geocoding.resolve_location("asdfghjkl-nonexistent")


@pytest.mark.asyncio
async def test_coordinates_route_to_reverse() -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock.get("https://nominatim.openstreetmap.org/reverse").mock(
            return_value=httpx.Response(
                200,
                json={
                    "lat": "40.7",
                    "lon": "-74.0",
                    "display_name": "New York, USA",
                    "address": {"country": "USA", "state": "New York"},
                },
            )
        )
        results = await geocoding.resolve_location("40.7, -74.0")
        assert results[0].display_name == "New York, USA"


@pytest.mark.asyncio
async def test_postal_code_routes_with_country() -> None:
    captured: dict[str, str] = {}

    def _capture(request: httpx.Request) -> httpx.Response:
        captured.update(dict(request.url.params))
        return httpx.Response(
            200,
            json=[
                {
                    "lat": "40.7",
                    "lon": "-74.0",
                    "display_name": "NY 10001",
                    "address": {"country": "USA"},
                }
            ],
        )

    with respx.mock(assert_all_called=True) as mock:
        mock.get("https://nominatim.openstreetmap.org/search").mock(side_effect=_capture)
        await geocoding.resolve_location("10001")
    assert captured.get("postalcode") == "10001"
    assert captured.get("countrycodes") == "us"


@pytest.mark.asyncio
async def test_timeout_raises_upstream_timeout() -> None:
    with respx.mock(assert_all_called=False) as mock:
        mock.get("https://nominatim.openstreetmap.org/search").mock(
            side_effect=httpx.ConnectTimeout("timeout")
        )
        with pytest.raises(UpstreamTimeout):
            await geocoding.resolve_location("Paris")
