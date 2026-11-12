from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.config import settings
from app.db import get_session
from app.errors import LocationAmbiguous, RequestNotFound, ValidationFailed
from app.models import DailyTemperature, Location, WeatherRequest
from app.schemas import (
    RequestListItem,
    RequestListOut,
    WeatherRequestCreate,
    WeatherRequestOut,
    WeatherRequestUpdate,
)
from app.services import geocoding, weather

router = APIRouter(prefix="/requests", tags=["requests"])


def _archive_first_date() -> date:
    return date.fromisoformat(settings.archive_first_date)


def _forecast_last_date() -> date:
    return date.today() + timedelta(days=weather.FORECAST_MAX_HORIZON_DAYS)


def _validate_range(start: date, end: date) -> None:
    if start > end:
        raise ValidationFailed(
            "start_date must be on or before end_date.",
            details={"start_date": start.isoformat(), "end_date": end.isoformat()},
        )
    if start < _archive_first_date():
        raise ValidationFailed(
            "start_date is earlier than the archive's first available date.",
            details={"archive_first_date": settings.archive_first_date},
        )
    if end > _forecast_last_date():
        raise ValidationFailed(
            "end_date is beyond the forecast horizon.",
            details={"forecast_last_date": _forecast_last_date().isoformat()},
        )
    span = (end - start).days + 1
    if span > settings.max_request_span_days:
        raise ValidationFailed(
            "Date range exceeds the maximum allowed span.",
            details={"span_days": span, "max_days": settings.max_request_span_days},
        )


async def _resolve_one(query: str, location_index: int | None) -> geocoding.LocationCandidate:
    candidates = await geocoding.resolve_location(query)
    if location_index is None:
        if len(candidates) > 1:
            raise LocationAmbiguous(
                "Multiple locations match the query.",
                details={"candidates": [c.to_dict() for c in candidates]},
            )
        return candidates[0]
    if location_index < 0 or location_index >= len(candidates):
        raise LocationAmbiguous(
            "location_index out of range.",
            details={"candidates": [c.to_dict() for c in candidates]},
        )
    return candidates[location_index]


def _upsert_location(
    session: Session, query: str, chosen: geocoding.LocationCandidate
) -> Location:
    existing = session.scalar(
        select(Location).where(
            Location.lat == chosen.lat,
            Location.lon == chosen.lon,
            Location.display_name == chosen.display_name,
        )
    )
    if existing is not None:
        return existing
    loc = Location(
        query_text=query,
        display_name=chosen.display_name,
        lat=chosen.lat,
        lon=chosen.lon,
        country=chosen.country,
        region=chosen.region,
        timezone=chosen.timezone,
        source=chosen.source,
    )
    session.add(loc)
    session.flush()
    return loc


@router.post("", response_model=WeatherRequestOut, status_code=status.HTTP_201_CREATED)
async def create_request(
    payload: WeatherRequestCreate,
    session: Session = Depends(get_session),
) -> WeatherRequestOut:
    _validate_range(payload.start_date, payload.end_date)
    chosen = await _resolve_one(payload.location, payload.location_index)
    daily_rows = await weather.fetch_daily_range(
        chosen.lat, chosen.lon, payload.start_date, payload.end_date
    )

    location = _upsert_location(session, payload.location, chosen)
    req = WeatherRequest(
        location_id=location.id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        notes=payload.notes,
    )
    session.add(req)
    session.flush()
    for row in daily_rows:
        session.add(
            DailyTemperature(
                request_id=req.id,
                date=row.date,
                temp_min=row.temp_min,
                temp_max=row.temp_max,
                temp_mean=row.temp_mean,
                precipitation_sum=row.precipitation_sum,
                weather_code=row.weather_code,
            )
        )
    session.commit()
    session.refresh(req)
    return WeatherRequestOut.model_validate(req)


@router.get("", response_model=RequestListOut)
def list_requests(
    session: Session = Depends(get_session),
    q: str | None = Query(default=None, description="Search by location text"),
    sort: str = Query(default="-created_at", description="Sort field, prefix '-' for desc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> RequestListOut:
    sortable = {
        "created_at": WeatherRequest.created_at,
        "updated_at": WeatherRequest.updated_at,
        "start_date": WeatherRequest.start_date,
        "end_date": WeatherRequest.end_date,
    }
    descending = sort.startswith("-")
    key = sort.lstrip("-")
    if key not in sortable:
        raise ValidationFailed("Unknown sort field.", details={"allowed": list(sortable)})
    order_col = sortable[key]

    stmt = select(WeatherRequest).join(WeatherRequest.location)
    count_stmt = select(func.count(WeatherRequest.id)).join(WeatherRequest.location)
    if q:
        needle = f"%{q.lower()}%"
        where = or_(
            func.lower(Location.display_name).like(needle),
            func.lower(Location.query_text).like(needle),
        )
        stmt = stmt.where(where)
        count_stmt = count_stmt.where(where)

    stmt = stmt.order_by(order_col.desc() if descending else order_col.asc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    stmt = stmt.options(selectinload(WeatherRequest.location))

    total = session.scalar(count_stmt) or 0
    items = session.scalars(stmt).all()
    return RequestListOut(
        total=total,
        items=[RequestListItem.model_validate(r) for r in items],
    )


@router.get("/{request_id}", response_model=WeatherRequestOut)
def get_request(request_id: int, session: Session = Depends(get_session)) -> WeatherRequestOut:
    req = session.get(WeatherRequest, request_id)
    if req is None:
        raise RequestNotFound("Request not found.", details={"id": request_id})
    return WeatherRequestOut.model_validate(req)


@router.patch("/{request_id}", response_model=WeatherRequestOut)
async def update_request(
    request_id: int,
    payload: WeatherRequestUpdate,
    session: Session = Depends(get_session),
) -> WeatherRequestOut:
    req = session.get(WeatherRequest, request_id)
    if req is None:
        raise RequestNotFound("Request not found.", details={"id": request_id})

    new_start = payload.start_date or req.start_date
    new_end = payload.end_date or req.end_date
    _validate_range(new_start, new_end)

    location_changed = payload.location is not None
    dates_changed = (new_start != req.start_date) or (new_end != req.end_date)

    if location_changed:
        chosen = await _resolve_one(payload.location or "", payload.location_index)
        req.location = _upsert_location(session, payload.location or "", chosen)

    if payload.notes is not None:
        req.notes = payload.notes

    req.start_date = new_start
    req.end_date = new_end

    if location_changed or dates_changed:
        # Re-fetch and replace daily rows.
        for row in list(req.daily):
            session.delete(row)
        session.flush()
        daily_rows = await weather.fetch_daily_range(
            req.location.lat, req.location.lon, new_start, new_end
        )
        for row in daily_rows:
            session.add(
                DailyTemperature(
                    request_id=req.id,
                    date=row.date,
                    temp_min=row.temp_min,
                    temp_max=row.temp_max,
                    temp_mean=row.temp_mean,
                    precipitation_sum=row.precipitation_sum,
                    weather_code=row.weather_code,
                )
            )

    session.commit()
    session.refresh(req)
    return WeatherRequestOut.model_validate(req)


@router.delete(
    "/{request_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_request(
    request_id: int, session: Session = Depends(get_session)
) -> Response:
    req = session.get(WeatherRequest, request_id)
    if req is None:
        raise RequestNotFound("Request not found.", details={"id": request_id})
    session.delete(req)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
