from fastapi import APIRouter, Depends, Query
from sqlalchemy import distinct, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.schemas.event_schemas import (
    SearchResponse,
    SearchShowResult,
    SearchVenueResult,
    ShowStatus,
    VenueStatus,
)
from shared.utils import setup_logger
from .database import get_db
from .models import Schedule, Screen, Show, Venue

router = APIRouter(prefix="/search", tags=["search"])
logger = setup_logger(__name__)


def _city_filter(city: str | None):
    if not city:
        return None
    return Venue.city.ilike(city.strip())


@router.get("", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1, max_length=120),
    city: str | None = Query(None, min_length=1, max_length=100),
    limit: int = Query(8, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    term = q.strip()
    normalized_city = city.strip() if city else None
    city_where = _city_filter(normalized_city)
    like_term = f"%{term}%"

    show_query = (
        select(
            Show.id,
            Show.title,
            Show.duration_minutes,
            Show.price,
            Show.language,
            Show.rating,
        )
        .where(Show.status == ShowStatus.ACTIVE.value)
        .where(
            or_(
                Show.title.ilike(like_term),
                Show.description.ilike(like_term),
                Show.language.ilike(like_term),
            )
        )
    )
    if city_where is not None:
        show_query = (
            show_query.join(Schedule, Schedule.show_id == Show.id)
            .join(Screen, Screen.id == Schedule.screen_id)
            .join(Venue, Venue.id == Screen.venue_id)
            .where(Venue.status == VenueStatus.ACTIVE.value)
            .where(city_where)
            .distinct()
        )
    show_query = show_query.order_by(Show.title.asc()).limit(limit)

    venue_query = (
        select(
            Venue.id,
            Venue.name,
            Venue.location,
            Venue.city,
            Venue.opening_time,
            Venue.closing_time,
        )
        .where(Venue.status == VenueStatus.ACTIVE.value)
        .where(
            or_(
                Venue.name.ilike(like_term),
                Venue.location.ilike(like_term),
                Venue.city.ilike(like_term),
            )
        )
        .order_by(Venue.name.asc())
        .limit(limit)
    )
    if city_where is not None:
        venue_query = venue_query.where(city_where)

    show_rows = (await db.execute(show_query)).all()
    venue_rows = (await db.execute(venue_query)).all()

    return SearchResponse(
        query=term,
        city=normalized_city,
        shows=[
            SearchShowResult(
                id=row.id,
                title=row.title,
                duration_minutes=row.duration_minutes,
                price=row.price,
                language=row.language,
                rating=row.rating,
            )
            for row in show_rows
        ],
        venues=[
            SearchVenueResult(
                id=row.id,
                name=row.name,
                location=row.location,
                city=row.city,
                opening_time=row.opening_time,
                closing_time=row.closing_time,
            )
            for row in venue_rows
        ],
    )


@router.get("/cities", response_model=list[str])
async def get_cities(
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    city_expr = func.trim(Venue.city).label("city")
    result = await db.execute(
        select(city_expr)
        .distinct()
        .where(Venue.status == VenueStatus.ACTIVE.value)
        .where(Venue.city.is_not(None))
        .order_by(city_expr.asc())
        .limit(limit)
    )
    return [value for value in result.scalars().all() if value]
