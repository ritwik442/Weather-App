from fastapi import APIRouter, Query

from app.errors import LocationAmbiguous
from app.schemas import (
    CurrentWeatherOut,
    ForecastDayOut,
    LocationCandidateOut,
    WeatherBundleOut,
)
from app.services import geocoding, weather
from app.services.tips import WeatherSnapshot, generate_tips

router = APIRouter(prefix="/weather", tags=["weather"])


def _pick_candidate(
    candidates: list[geocoding.LocationCandidate], index: int | None
) -> geocoding.LocationCandidate:
    if index is None:
        if len(candidates) > 1:
            raise LocationAmbiguous(
                "Multiple locations match the query.",
                details={"candidates": [c.to_dict() for c in candidates]},
            )
        return candidates[0]
    if index < 0 or index >= len(candidates):
        raise LocationAmbiguous(
            "location_index out of range.",
            details={"candidates": [c.to_dict() for c in candidates]},
        )
    return candidates[index]


@router.get("/current", response_model=WeatherBundleOut)
async def current(
    q: str = Query(min_length=1, description="Location query"),
    location_index: int | None = Query(default=None, ge=0),
) -> WeatherBundleOut:
    candidates = await geocoding.resolve_location(q)
    chosen = _pick_candidate(candidates, location_index)
    bundle = await weather.fetch_current_and_5day(chosen.lat, chosen.lon)

    snapshot = WeatherSnapshot(
        temp_c=bundle.current.temperature,
        temp_max_c=bundle.current.temp_max_today,
        temp_min_c=bundle.current.temp_min_today,
        precipitation_mm=bundle.current.precipitation,
        precipitation_probability=bundle.current.precipitation_probability,
        uv_index=bundle.current.uv_index,
        wind_speed_ms=bundle.current.wind_speed,
        humidity=bundle.current.humidity,
    )
    tips = generate_tips(snapshot)

    return WeatherBundleOut(
        location=LocationCandidateOut(**chosen.to_dict()),
        current=CurrentWeatherOut(**bundle.current.to_dict()),
        daily=[ForecastDayOut(**d.to_dict()) for d in bundle.daily],
        tips=tips,
    )
