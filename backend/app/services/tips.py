"""Rule-based 'things you might not think about' tips.

Pure function: easy to unit-test, easy to tune without touching the routers.
All thresholds use SI units (°C, mm, m/s, hPa, µg/m³).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class WeatherSnapshot:
    """Minimal input shape; every field is optional so tips degrade gracefully."""

    temp_c: float | None = None
    temp_max_c: float | None = None
    temp_min_c: float | None = None
    precipitation_mm: float | None = None
    precipitation_probability: float | None = None
    uv_index: float | None = None
    wind_speed_ms: float | None = None
    humidity: float | None = None
    is_travel: bool = False
    air_quality_pm25: float | None = None


def _mk(code: str, message: str, severity: str = "info") -> dict[str, Any]:
    return {"code": code, "message": message, "severity": severity}


def generate_tips(snapshot: WeatherSnapshot) -> list[dict[str, Any]]:
    """Return an ordered list of tips (most severe first)."""
    tips: list[dict[str, Any]] = []

    pp = snapshot.precipitation_probability
    pm = snapshot.precipitation_mm
    if (pp is not None and pp > 50) or (pm is not None and pm >= 2):
        tips.append(_mk("umbrella", "Take an umbrella — rain is likely today.", "warning"))

    if snapshot.uv_index is not None and snapshot.uv_index >= 6:
        tips.append(_mk("sunscreen", "UV is high — wear sunscreen and sunglasses.", "warning"))

    if (
        snapshot.temp_max_c is not None
        and snapshot.temp_min_c is not None
        and (snapshot.temp_max_c - snapshot.temp_min_c) > 10
    ):
        tips.append(
            _mk(
                "layers",
                "Big day/night temperature swing — dress in layers.",
                "info",
            )
        )

    if snapshot.temp_min_c is not None and snapshot.temp_min_c <= 0:
        tips.append(_mk("ice", "Watch for ice or frost — temperatures reach freezing.", "warning"))

    if snapshot.temp_max_c is not None and snapshot.temp_max_c >= 32:
        tips.append(
            _mk(
                "heat",
                "Heat stress likely — hydrate and limit outdoor exposure.",
                "warning",
            )
        )

    if snapshot.wind_speed_ms is not None and snapshot.wind_speed_ms >= 10:
        tips.append(_mk("wind", "Strong winds — secure loose objects outdoors.", "warning"))

    if snapshot.air_quality_pm25 is not None and snapshot.air_quality_pm25 >= 35:
        tips.append(
            _mk(
                "air_quality",
                "Poor air quality — sensitive groups should limit outdoor activity.",
                "warning",
            )
        )

    if snapshot.is_travel:
        pieces: list[str] = []
        if snapshot.temp_max_c is not None and snapshot.temp_max_c >= 25:
            pieces.append("light clothing")
        if snapshot.temp_min_c is not None and snapshot.temp_min_c <= 10:
            pieces.append("a warm layer")
        if (pp is not None and pp > 30) or (pm is not None and pm >= 1):
            pieces.append("a rain jacket")
        if snapshot.uv_index is not None and snapshot.uv_index >= 6:
            pieces.append("sunscreen")
        if pieces:
            tips.append(
                _mk(
                    "travel_pack",
                    "Packing suggestion: " + ", ".join(pieces) + ".",
                    "info",
                )
            )

    severity_order = {"warning": 0, "info": 1}
    tips.sort(key=lambda t: severity_order.get(t["severity"], 2))
    return tips
