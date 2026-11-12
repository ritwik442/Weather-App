from fastapi import APIRouter, Query

from app.schemas import LocationCandidateOut, LocationResolveOut
from app.services import geocoding

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
