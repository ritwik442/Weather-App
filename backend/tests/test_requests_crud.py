from __future__ import annotations

from datetime import date, timedelta

import httpx
import respx
from fastapi.testclient import TestClient

from app.models import DailyTemperature, WeatherRequest


def _nominatim_result(display: str, lat: float, lon: float) -> dict:
    return {
        "lat": str(lat),
        "lon": str(lon),
        "display_name": display,
        "address": {"country": "France", "state": "Île-de-France"},
    }


def _forecast_daily(dates: list[date]) -> dict:
    return {
        "daily": {
            "time": [d.isoformat() for d in dates],
            "weather_code": [2] * len(dates),
            "temperature_2m_max": [20.0] * len(dates),
            "temperature_2m_min": [10.0] * len(dates),
            "temperature_2m_mean": [15.0] * len(dates),
            "precipitation_sum": [0.0] * len(dates),
        }
    }


def _mock_paris_and_forecast(mock: respx.MockRouter, dates: list[date]) -> None:
    mock.get("https://nominatim.openstreetmap.org/search").mock(
        return_value=httpx.Response(200, json=[_nominatim_result("Paris, France", 48.85, 2.35)])
    )
    mock.get("https://api.open-meteo.com/v1/forecast").mock(
        return_value=httpx.Response(200, json=_forecast_daily(dates))
    )


def test_create_request_persists_full_record(client: TestClient, db_session) -> None:
    today = date.today()
    start = today
    end = today + timedelta(days=2)
    dates = [start + timedelta(days=i) for i in range(3)]

    with respx.mock(assert_all_called=False) as mock:
        _mock_paris_and_forecast(mock, dates)
        r = client.post(
            "/api/v1/requests",
            json={
                "location": "Paris",
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "notes": "trip prep",
            },
        )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["location"]["display_name"] == "Paris, France"
    assert body["notes"] == "trip prep"
    assert len(body["daily"]) == 3

    # Persistence sanity check
    stored = db_session.query(WeatherRequest).one()
    assert stored.start_date == start
    assert len(stored.daily) == 3


def test_create_rejects_reversed_dates(client: TestClient) -> None:
    today = date.today()
    r = client.post(
        "/api/v1/requests",
        json={
            "location": "Paris",
            "start_date": (today + timedelta(days=5)).isoformat(),
            "end_date": today.isoformat(),
        },
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_FAILED"


def test_create_rejects_pre_archive_date(client: TestClient) -> None:
    r = client.post(
        "/api/v1/requests",
        json={
            "location": "Paris",
            "start_date": "1900-01-01",
            "end_date": "1900-01-02",
        },
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_FAILED"


def test_create_rejects_beyond_forecast_horizon(client: TestClient) -> None:
    today = date.today()
    r = client.post(
        "/api/v1/requests",
        json={
            "location": "Paris",
            "start_date": today.isoformat(),
            "end_date": (today + timedelta(days=365)).isoformat(),
        },
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_FAILED"


def test_ambiguous_location_returns_candidates(client: TestClient) -> None:
    today = date.today()
    with respx.mock(assert_all_called=False) as mock:
        mock.get("https://nominatim.openstreetmap.org/search").mock(
            return_value=httpx.Response(
                200,
                json=[
                    _nominatim_result("Springfield, IL, USA", 39.78, -89.65),
                    _nominatim_result("Springfield, MA, USA", 42.10, -72.59),
                ],
            )
        )
        r = client.post(
            "/api/v1/requests",
            json={
                "location": "Springfield",
                "start_date": today.isoformat(),
                "end_date": today.isoformat(),
            },
        )
    assert r.status_code == 409
    body = r.json()
    assert body["error"]["code"] == "LOCATION_AMBIGUOUS"
    assert len(body["error"]["details"]["candidates"]) == 2


def test_disambiguation_via_location_index(client: TestClient) -> None:
    today = date.today()
    with respx.mock(assert_all_called=False) as mock:
        mock.get("https://nominatim.openstreetmap.org/search").mock(
            return_value=httpx.Response(
                200,
                json=[
                    _nominatim_result("Springfield, IL, USA", 39.78, -89.65),
                    _nominatim_result("Springfield, MA, USA", 42.10, -72.59),
                ],
            )
        )
        mock.get("https://api.open-meteo.com/v1/forecast").mock(
            return_value=httpx.Response(200, json=_forecast_daily([today]))
        )
        r = client.post(
            "/api/v1/requests",
            json={
                "location": "Springfield",
                "start_date": today.isoformat(),
                "end_date": today.isoformat(),
                "location_index": 1,
            },
        )
    assert r.status_code == 201, r.text
    assert "Springfield, MA" in r.json()["location"]["display_name"]


def test_patch_refetches_on_date_change(client: TestClient, db_session) -> None:
    today = date.today()
    with respx.mock(assert_all_called=False) as mock:
        _mock_paris_and_forecast(mock, [today])
        r = client.post(
            "/api/v1/requests",
            json={
                "location": "Paris",
                "start_date": today.isoformat(),
                "end_date": today.isoformat(),
            },
        )
    assert r.status_code == 201
    rid = r.json()["id"]
    assert db_session.query(DailyTemperature).filter_by(request_id=rid).count() == 1

    with respx.mock(assert_all_called=False) as mock:
        new_dates = [today + timedelta(days=i) for i in range(3)]
        mock.get("https://api.open-meteo.com/v1/forecast").mock(
            return_value=httpx.Response(200, json=_forecast_daily(new_dates))
        )
        patch = client.patch(
            f"/api/v1/requests/{rid}",
            json={"end_date": (today + timedelta(days=2)).isoformat()},
        )
    assert patch.status_code == 200, patch.text
    daily_payload = patch.json()["daily"]
    assert len(daily_payload) == 3
    returned_dates = sorted(d["date"] for d in daily_payload)
    assert returned_dates == [d.isoformat() for d in new_dates]
    stored_dates = sorted(
        row.date
        for row in db_session.query(DailyTemperature).filter_by(request_id=rid).all()
    )
    assert stored_dates == new_dates, "Daily rows should be replaced to match the new range"


def test_list_search_and_pagination(client: TestClient) -> None:
    today = date.today()
    with respx.mock(assert_all_called=False) as mock:
        _mock_paris_and_forecast(mock, [today])
        client.post(
            "/api/v1/requests",
            json={
                "location": "Paris",
                "start_date": today.isoformat(),
                "end_date": today.isoformat(),
            },
        )

    r = client.get("/api/v1/requests?q=paris&page=1&page_size=10")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1

    r_none = client.get("/api/v1/requests?q=nowhere")
    assert r_none.json()["total"] == 0


def test_delete_cascades_daily_rows(client: TestClient, db_session) -> None:
    today = date.today()
    with respx.mock(assert_all_called=False) as mock:
        _mock_paris_and_forecast(mock, [today])
        r = client.post(
            "/api/v1/requests",
            json={
                "location": "Paris",
                "start_date": today.isoformat(),
                "end_date": today.isoformat(),
            },
        )
    rid = r.json()["id"]
    assert db_session.query(DailyTemperature).filter_by(request_id=rid).count() == 1

    d = client.delete(f"/api/v1/requests/{rid}")
    assert d.status_code == 204
    assert db_session.query(WeatherRequest).filter_by(id=rid).one_or_none() is None
    assert db_session.query(DailyTemperature).filter_by(request_id=rid).count() == 0


def test_delete_missing_returns_404(client: TestClient) -> None:
    r = client.delete("/api/v1/requests/99999")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NOT_FOUND"
