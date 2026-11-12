"""Open-Meteo weather client.

The forecast endpoint covers current, hourly and daily data for near-future
and recent-past dates. The archive endpoint fills in historical dates; we
route per date and merge the daily series when a range straddles the boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

from app.errors import UpstreamFailure
from app.services import http
from app.services.cache import TTLCache

_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

# How far back the live forecast endpoint still covers reliably.
# Beyond this we route to the archive API.
FORECAST_PAST_DAYS = 7
# Open-Meteo's forecast horizon (current default is 16 days).
FORECAST_MAX_HORIZON_DAYS = 16
# Archive API typically lags real-time by about five days.
ARCHIVE_LAG_DAYS = 5

_WEATHER_TTL_SECONDS = 10 * 60

_current_cache: TTLCache[dict[str, Any]] = TTLCache(_WEATHER_TTL_SECONDS)
_forecast_cache: TTLCache[dict[str, Any]] = TTLCache(_WEATHER_TTL_SECONDS)
_daily_cache: TTLCache[list[dict[str, Any]]] = TTLCache(_WEATHER_TTL_SECONDS)


@dataclass
class DailyRow:
    date: date
    temp_min: float | None = None
    temp_max: float | None = None
    temp_mean: float | None = None
    precipitation_sum: float | None = None
    weather_code: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "date": self.date.isoformat(),
            "temp_min": self.temp_min,
            "temp_max": self.temp_max,
            "temp_mean": self.temp_mean,
            "precipitation_sum": self.precipitation_sum,
            "weather_code": self.weather_code,
        }


@dataclass
class CurrentWeather:
    temperature: float | None = None
    feels_like: float | None = None
    humidity: float | None = None
    wind_speed: float | None = None
    wind_direction: float | None = None
    precipitation: float | None = None
    precipitation_probability: float | None = None
    uv_index: float | None = None
    visibility: float | None = None
    pressure: float | None = None
    weather_code: int | None = None
    is_day: bool | None = None
    time: str | None = None
    timezone: str | None = None
    sunrise: str | None = None
    sunset: str | None = None
    temp_max_today: float | None = None
    temp_min_today: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass
class ForecastDay:
    date: date
    temp_min: float | None = None
    temp_max: float | None = None
    precipitation_sum: float | None = None
    precipitation_probability_max: float | None = None
    weather_code: int | None = None
    uv_index_max: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "date": self.date.isoformat(),
            "temp_min": self.temp_min,
            "temp_max": self.temp_max,
            "precipitation_sum": self.precipitation_sum,
            "precipitation_probability_max": self.precipitation_probability_max,
            "weather_code": self.weather_code,
            "uv_index_max": self.uv_index_max,
        }


@dataclass
class ForecastBundle:
    current: CurrentWeather
    daily: list[ForecastDay] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"current": self.current.to_dict(), "daily": [d.to_dict() for d in self.daily]}


_DAILY_FIELDS = (
    "weather_code",
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
    "precipitation_sum",
    "precipitation_probability_max",
    "uv_index_max",
    "sunrise",
    "sunset",
)

_CURRENT_FIELDS = (
    "temperature_2m",
    "apparent_temperature",
    "relative_humidity_2m",
    "precipitation",
    "weather_code",
    "wind_speed_10m",
    "wind_direction_10m",
    "pressure_msl",
    "surface_pressure",
    "is_day",
)

_HOURLY_FIELDS = ("uv_index", "visibility", "precipitation_probability")


def _get_at(series: list[Any] | None, index: int) -> Any:
    if not series or index < 0 or index >= len(series):
        return None
    return series[index]


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def split_date_range(
    start: date, end: date, today: date | None = None
) -> tuple[list[date], list[date]]:
    """Split a date range into (archive_dates, forecast_dates).

    Dates older than ARCHIVE_LAG_DAYS go to the archive endpoint; the rest go
    to the forecast endpoint which accepts recent past + future.
    """
    today = today or date.today()
    archive_cutoff = today - timedelta(days=ARCHIVE_LAG_DAYS)
    archive: list[date] = []
    forecast: list[date] = []
    cur = start
    while cur <= end:
        (archive if cur < archive_cutoff else forecast).append(cur)
        cur += timedelta(days=1)
    return archive, forecast


async def fetch_current_and_5day(lat: float, lon: float) -> ForecastBundle:
    key = f"{lat:.4f},{lon:.4f}"
    cached = _forecast_cache.get(key)
    if cached is not None:
        return _bundle_from_dict(cached)

    params = {
        "latitude": lat,
        "longitude": lon,
        "timezone": "auto",
        "current": ",".join(_CURRENT_FIELDS),
        "hourly": ",".join(_HOURLY_FIELDS),
        "daily": ",".join(_DAILY_FIELDS),
        "forecast_days": 5,
        "past_days": 0,
    }
    data = await http.get_json(_FORECAST_URL, params=params, upstream_name="open-meteo forecast")
    if not isinstance(data, dict):
        raise UpstreamFailure("Unexpected open-meteo forecast response.")

    bundle = _parse_forecast_bundle(data)
    _forecast_cache.set(key, bundle.to_dict())
    return bundle


def _parse_forecast_bundle(data: dict[str, Any]) -> ForecastBundle:
    current_data = data.get("current") or {}
    timezone = data.get("timezone")

    # Pull today's high/low + sunrise/sunset from the daily series.
    daily = data.get("daily") or {}
    daily_dates = daily.get("time") or []
    temp_max_today = _get_at(daily.get("temperature_2m_max"), 0)
    temp_min_today = _get_at(daily.get("temperature_2m_min"), 0)
    sunrise = _get_at(daily.get("sunrise"), 0)
    sunset = _get_at(daily.get("sunset"), 0)

    # Pull UV / visibility / precip-probability from the matching hour.
    hourly = data.get("hourly") or {}
    hourly_times: list[str] = hourly.get("time") or []
    current_time: str | None = current_data.get("time")
    hour_index = hourly_times.index(current_time) if current_time in hourly_times else -1
    uv = _get_at(hourly.get("uv_index"), hour_index) if hour_index >= 0 else None
    visibility = _get_at(hourly.get("visibility"), hour_index) if hour_index >= 0 else None
    precip_prob = (
        _get_at(hourly.get("precipitation_probability"), hour_index) if hour_index >= 0 else None
    )

    current = CurrentWeather(
        temperature=current_data.get("temperature_2m"),
        feels_like=current_data.get("apparent_temperature"),
        humidity=current_data.get("relative_humidity_2m"),
        wind_speed=current_data.get("wind_speed_10m"),
        wind_direction=current_data.get("wind_direction_10m"),
        precipitation=current_data.get("precipitation"),
        precipitation_probability=precip_prob,
        uv_index=uv,
        visibility=visibility,
        pressure=current_data.get("pressure_msl") or current_data.get("surface_pressure"),
        weather_code=current_data.get("weather_code"),
        is_day=bool(current_data.get("is_day")) if current_data.get("is_day") is not None else None,
        time=current_time,
        timezone=timezone,
        sunrise=sunrise,
        sunset=sunset,
        temp_max_today=temp_max_today,
        temp_min_today=temp_min_today,
    )

    days: list[ForecastDay] = []
    for i, iso in enumerate(daily_dates):
        try:
            d = _parse_date(iso)
        except ValueError:
            continue
        days.append(
            ForecastDay(
                date=d,
                temp_min=_get_at(daily.get("temperature_2m_min"), i),
                temp_max=_get_at(daily.get("temperature_2m_max"), i),
                precipitation_sum=_get_at(daily.get("precipitation_sum"), i),
                precipitation_probability_max=_get_at(
                    daily.get("precipitation_probability_max"), i
                ),
                weather_code=_get_at(daily.get("weather_code"), i),
                uv_index_max=_get_at(daily.get("uv_index_max"), i),
            )
        )

    return ForecastBundle(current=current, daily=days)


def _bundle_from_dict(data: dict[str, Any]) -> ForecastBundle:
    cur = data["current"]
    current = CurrentWeather(**cur)
    days = [
        ForecastDay(
            date=_parse_date(d["date"]),
            temp_min=d.get("temp_min"),
            temp_max=d.get("temp_max"),
            precipitation_sum=d.get("precipitation_sum"),
            precipitation_probability_max=d.get("precipitation_probability_max"),
            weather_code=d.get("weather_code"),
            uv_index_max=d.get("uv_index_max"),
        )
        for d in data["daily"]
    ]
    return ForecastBundle(current=current, daily=days)


async def fetch_daily_range(lat: float, lon: float, start: date, end: date) -> list[DailyRow]:
    """Fetch daily rows across [start, end], routing to archive + forecast."""
    if end < start:
        raise ValueError("end must be >= start")

    key = f"{lat:.4f},{lon:.4f}:{start.isoformat()}:{end.isoformat()}"
    cached = _daily_cache.get(key)
    if cached is not None:
        return [
            DailyRow(
                date=_parse_date(d["date"]),
                **{k: d[k] for k in d if k != "date"},
            )
            for d in cached
        ]

    archive_dates, forecast_dates = split_date_range(start, end)
    rows: dict[date, DailyRow] = {}

    daily_fields = ",".join(
        [
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "temperature_2m_mean",
            "precipitation_sum",
        ]
    )

    if archive_dates:
        data = await http.get_json(
            _ARCHIVE_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "start_date": archive_dates[0].isoformat(),
                "end_date": archive_dates[-1].isoformat(),
                "daily": daily_fields,
                "timezone": "auto",
            },
            upstream_name="open-meteo archive",
        )
        for row in _rows_from_daily(data):
            rows[row.date] = row

    if forecast_dates:
        data = await http.get_json(
            _FORECAST_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "start_date": forecast_dates[0].isoformat(),
                "end_date": forecast_dates[-1].isoformat(),
                "daily": daily_fields,
                "timezone": "auto",
            },
            upstream_name="open-meteo forecast",
        )
        for row in _rows_from_daily(data):
            rows[row.date] = row

    merged = [rows[d] for d in sorted(rows.keys()) if start <= d <= end]
    _daily_cache.set(key, [r.to_dict() for r in merged])
    return merged


def _rows_from_daily(data: Any) -> list[DailyRow]:
    if not isinstance(data, dict):
        return []
    daily = data.get("daily") or {}
    dates = daily.get("time") or []
    rows: list[DailyRow] = []
    for i, iso in enumerate(dates):
        try:
            d = _parse_date(iso)
        except ValueError:
            continue
        rows.append(
            DailyRow(
                date=d,
                temp_min=_get_at(daily.get("temperature_2m_min"), i),
                temp_max=_get_at(daily.get("temperature_2m_max"), i),
                temp_mean=_get_at(daily.get("temperature_2m_mean"), i),
                precipitation_sum=_get_at(daily.get("precipitation_sum"), i),
                weather_code=_get_at(daily.get("weather_code"), i),
            )
        )
    return rows


def clear_caches_for_tests() -> None:
    _current_cache.clear()
    _forecast_cache.clear()
    _daily_cache.clear()
