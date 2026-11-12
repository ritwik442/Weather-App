from typing import Any

from fastapi import APIRouter, Query

from app.schemas import LocationCandidateOut, LocationResolveOut
from app.services import extras, geocoding

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("/resolve", response_model=LocationResolveOut)
async def resolve(
    q: str = Query(min_length=1, description="Free-text query"),
) -> LocationResolveOut:
    candidates = await geocoding.resolve_location(q)
    return LocationResolveOut(
        query=q,
        candidates=[LocationCandidateOut(**c.to_dict()) for c in candidates],
    )


@router.get("/extras")
async def get_extras(
    lat: float = Query(ge=-90.0, le=90.0),
    lon: float = Query(ge=-180.0, le=180.0),
    name: str = Query(min_length=1, description="Place name for text-based lookups"),
) -> dict[str, Any]:
    return await extras.fetch_extras(lat, lon, name)
