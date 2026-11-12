from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class LocationCandidateOut(BaseModel):
    display_name: str
    lat: float
    lon: float
    country: str | None = None
    region: str | None = None
    timezone: str | None = None
    source: str


class LocationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    query_text: str
    display_name: str
    lat: float
    lon: float
    country: str | None = None
    region: str | None = None
    timezone: str | None = None
    source: str
    created_at: datetime


class DailyTemperatureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: date
    temp_min: float | None = None
    temp_max: float | None = None
    temp_mean: float | None = None
    precipitation_sum: float | None = None
    weather_code: int | None = None


class WeatherRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    location: LocationOut
    start_date: date
    end_date: date
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
    daily: list[DailyTemperatureOut] = Field(default_factory=list)


class RequestListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    location: LocationOut
    start_date: date
    end_date: date
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class RequestListOut(BaseModel):
    total: int
    items: list[RequestListItem]


class WeatherRequestCreate(BaseModel):
    location: str = Field(min_length=1)
    start_date: date
    end_date: date
    notes: str | None = None
    location_index: int | None = Field(
        default=None,
        description=(
            "When location resolution returns multiple candidates, pick the "
            "nth one (0-based) instead of returning an ambiguity error."
        ),
    )


class WeatherRequestUpdate(BaseModel):
    location: str | None = Field(default=None, min_length=1)
    start_date: date | None = None
    end_date: date | None = None
    notes: str | None = None
    location_index: int | None = None


class CurrentWeatherOut(BaseModel):
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


class ForecastDayOut(BaseModel):
    date: date
    temp_min: float | None = None
    temp_max: float | None = None
    precipitation_sum: float | None = None
    precipitation_probability_max: float | None = None
    weather_code: int | None = None
    uv_index_max: float | None = None


class WeatherBundleOut(BaseModel):
    location: LocationCandidateOut
    current: CurrentWeatherOut
    daily: list[ForecastDayOut]
    tips: list[dict[str, Any]]


class LocationResolveOut(BaseModel):
    query: str
    candidates: list[LocationCandidateOut]
