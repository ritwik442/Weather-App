from __future__ import annotations

from datetime import date, timedelta

import httpx
import respx

from app.services import weather


def _forecast_payload(dates: list[date]) -> dict:
    return {
        "timezone": "UTC",
        "current": {
            "temperature_2m": 18.2,
            "apparent_temperature": 17.5,
            "relative_humidity_2m": 55,
            "wind_speed_10m": 3.5,
            "wind_direction_10m": 180,
            "precipitation": 0.0,
            "weather_code": 2,
            "pressure_msl": 1013.2,
            "is_day": 1,
            "time": dates[0].isoformat() + "T12:00",
        },
        "hourly": {
            "time": [dates[0].isoformat() + "T12:00"],
            "uv_index": [5.0],
            "visibility": [10000],
            "precipitation_probability": [20],
        },
        "daily": {
            "time": [d.isoformat() for d in dates],
            "weather_code": [2] * len(dates),
            "temperature_2m_max": [22.0 + i for i in range(len(dates))],
            "temperature_2m_min": [12.0 + i for i in range(len(dates))],
            "temperature_2m_mean": [17.0 + i for i in range(len(dates))],
            "precipitation_sum": [0.0] * len(dates),
            "precipitation_probability_max": [10] * len(dates),
            "uv_index_max": [5.0] * len(dates),
            "sunrise": [d.isoformat() + "T06:00" for d in dates],
            "sunset": [d.isoformat() + "T20:00" for d in dates],
        },
    }


def _archive_payload(dates: list[date]) -> dict:
    return {
        "daily": {
            "time": [d.isoformat() for d in dates],
            "weather_code": [61] * len(dates),
            "temperature_2m_max": [15.0] * len(dates),
            "temperature_2m_min": [5.0] * len(dates),
            "temperature_2m_mean": [10.0] * len(dates),
            "precipitation_sum": [1.0] * len(dates),
        }
    }


def test_split_date_range_routes_old_and_new() -> None:
    today = date(2026, 6, 15)
    archive, forecast = weather.split_date_range(
        date(2026, 6, 1), date(2026, 6, 20), today=today
    )
    # Archive lag is 5 days: dates < today-5 → archive
    cutoff = today - timedelta(days=weather.ARCHIVE_LAG_DAYS)
    assert all(d < cutoff for d in archive)
    assert all(d >= cutoff for d in forecast)
    assert archive[0] == date(2026, 6, 1)
    assert archive[-1] == cutoff - timedelta(days=1)
    assert forecast[0] == cutoff


async def test_current_and_5day_parses_forecast() -> None:
    dates = [date.today() + timedelta(days=i) for i in range(5)]
    with respx.mock(assert_all_called=True) as mock:
        mock.get("https://api.open-meteo.com/v1/forecast").mock(
            return_value=httpx.Response(200, json=_forecast_payload(dates))
        )
        bundle = await weather.fetch_current_and_5day(40.0, -74.0)
    assert bundle.current.temperature == 18.2
    assert bundle.current.uv_index == 5.0
    assert bundle.current.precipitation_probability == 20
    assert len(bundle.daily) == 5
    assert bundle.daily[0].temp_max == 22.0


async def test_fetch_daily_range_merges_archive_and_forecast() -> None:
    today = date.today()
    start = today - timedelta(days=10)
    end = today + timedelta(days=2)

    archive_dates, forecast_dates = weather.split_date_range(start, end)

    with respx.mock(assert_all_called=True) as mock:
        mock.get("https://archive-api.open-meteo.com/v1/archive").mock(
            return_value=httpx.Response(200, json=_archive_payload(archive_dates))
        )
        mock.get("https://api.open-meteo.com/v1/forecast").mock(
            return_value=httpx.Response(200, json=_forecast_payload(forecast_dates))
        )
        rows = await weather.fetch_daily_range(40.0, -74.0, start, end)

    returned_dates = [r.date for r in rows]
    assert returned_dates == sorted(returned_dates)
    assert returned_dates[0] == start
    assert returned_dates[-1] == end
    archive_rows = [r for r in rows if r.date in archive_dates]
    forecast_rows = [r for r in rows if r.date in forecast_dates]
    assert all(r.temp_max == 15.0 for r in archive_rows)
    assert all(r.temp_max is not None and r.temp_max >= 22.0 for r in forecast_rows)
