from __future__ import annotations

import httpx
import respx
from fastapi.testclient import TestClient


def test_autocomplete_returns_candidates(client: TestClient) -> None:
    with respx.mock(assert_all_called=False) as mock:
        mock.get("https://geocoding-api.open-meteo.com/v1/search").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "name": "Paris",
                            "latitude": 48.85,
                            "longitude": 2.35,
                            "country": "France",
                            "admin1": "Île-de-France",
                            "timezone": "Europe/Paris",
                        },
                        {
                            "name": "Paris",
                            "latitude": 33.66,
                            "longitude": -95.55,
                            "country": "USA",
                            "admin1": "Texas",
                            "timezone": "America/Chicago",
                        },
                    ]
                },
            )
        )
        r = client.get("/api/v1/locations/autocomplete?q=Par")
    assert r.status_code == 200
    body = r.json()
    assert body["query"] == "Par"
    assert len(body["candidates"]) == 2


def test_autocomplete_single_char_returns_empty(client: TestClient) -> None:
    r = client.get("/api/v1/locations/autocomplete?q=P")
    assert r.status_code == 200
    assert r.json()["candidates"] == []


def test_autocomplete_swallows_upstream_failure(client: TestClient) -> None:
    with respx.mock(assert_all_called=False) as mock:
        mock.get("https://geocoding-api.open-meteo.com/v1/search").mock(
            return_value=httpx.Response(500, text="boom")
        )
        r = client.get("/api/v1/locations/autocomplete?q=Par")
    assert r.status_code == 200
    assert r.json()["candidates"] == []
