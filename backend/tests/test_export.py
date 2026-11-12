from __future__ import annotations

import csv
import io
import json
from datetime import date, timedelta
from xml.etree import ElementTree as ET

import httpx
import respx
from fastapi.testclient import TestClient


def _nominatim(display: str, lat: float, lon: float) -> dict:
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


def _seed_one(client: TestClient) -> int:
    today = date.today()
    dates = [today, today + timedelta(days=1)]
    with respx.mock(assert_all_called=False) as mock:
        mock.get("https://nominatim.openstreetmap.org/search").mock(
            return_value=httpx.Response(200, json=[_nominatim("Paris, France", 48.85, 2.35)])
        )
        mock.get("https://api.open-meteo.com/v1/forecast").mock(
            return_value=httpx.Response(200, json=_forecast_daily(dates))
        )
        r = client.post(
            "/api/v1/requests",
            json={
                "location": "Paris",
                "start_date": today.isoformat(),
                "end_date": (today + timedelta(days=1)).isoformat(),
                "notes": "demo",
            },
        )
    assert r.status_code == 201
    return int(r.json()["id"])


def test_export_rejects_unsupported_format(client: TestClient) -> None:
    r = client.get("/api/v1/requests/export?format=yaml")
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_FAILED"


def test_export_json(client: TestClient) -> None:
    _seed_one(client)
    r = client.get("/api/v1/requests/export?format=json")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/json")
    assert "attachment" in r.headers["content-disposition"]
    body = json.loads(r.content)
    assert body["app"] == "Weather App"
    assert len(body["records"]) == 1
    assert len(body["records"][0]["daily"]) == 2


def test_export_csv(client: TestClient) -> None:
    _seed_one(client)
    r = client.get("/api/v1/requests/export?format=csv")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    rows = list(csv.reader(io.StringIO(r.content.decode("utf-8"))))
    assert rows[0][0] == "request_id"
    assert rows[1][1] == "Paris, France"
    assert len(rows) == 3  # header + 2 daily rows


def test_export_xml(client: TestClient) -> None:
    _seed_one(client)
    r = client.get("/api/v1/requests/export?format=xml")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/xml")
    root = ET.fromstring(r.content)
    assert root.tag == "weather_requests"
    requests_els = root.findall("request")
    assert len(requests_els) == 1
    assert len(requests_els[0].find("daily").findall("day")) == 2


def test_export_markdown(client: TestClient) -> None:
    _seed_one(client)
    r = client.get("/api/v1/requests/export?format=md")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/markdown")
    text = r.content.decode("utf-8")
    assert "# Weather App" in text
    assert "## Paris, France" in text
    assert "| Date |" in text


def test_export_pdf(client: TestClient) -> None:
    _seed_one(client)
    r = client.get("/api/v1/requests/export?format=pdf")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/pdf")
    # PDF files start with "%PDF-"
    assert r.content[:5] == b"%PDF-"


def test_export_filter_by_ids(client: TestClient) -> None:
    id1 = _seed_one(client)
    id2 = _seed_one(client)
    assert id1 != id2
    r = client.get(f"/api/v1/requests/export?format=json&ids={id1}")
    body = json.loads(r.content)
    returned_ids = [rec["id"] for rec in body["records"]]
    assert returned_ids == [id1]


def test_export_bad_ids(client: TestClient) -> None:
    r = client.get("/api/v1/requests/export?format=json&ids=abc")
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_FAILED"


def test_export_empty(client: TestClient) -> None:
    r = client.get("/api/v1/requests/export?format=json")
    assert r.status_code == 200
    body = json.loads(r.content)
    assert body["records"] == []
