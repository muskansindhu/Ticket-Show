from datetime import time as dt_time

from fastapi import APIRouter, Query

from shared.schemas.event_schemas import (
    SearchResponse,
    SearchShowResult,
    SearchVenueResult,
)
from shared.utils import setup_logger
from .elastic import get_cities as es_get_cities
from .elastic import search_shows as es_search_shows
from .elastic import search_venues as es_search_venues

router = APIRouter(prefix="/search", tags=["search"])
logger = setup_logger(__name__)


@router.get("", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1, max_length=120),
    city: str | None = Query(None, min_length=1, max_length=100),
    limit: int = Query(8, ge=1, le=50),
):
    term = q.strip()
    normalized_city = city.strip() if city else None

    show_docs = await es_search_shows(term, city=normalized_city, limit=limit)
    venue_docs = await es_search_venues(term, city=normalized_city, limit=limit)

    shows = [
        SearchShowResult(
            id=doc["id"],
            title=doc.get("title", ""),
            duration_minutes=doc.get("duration_minutes", 0),
            price=doc.get("price", 0),
            language=doc.get("language"),
            rating=doc.get("rating"),
        )
        for doc in show_docs
    ]

    venues = []
    for doc in venue_docs:
        opening = doc.get("opening_time")
        closing = doc.get("closing_time")
        if isinstance(opening, str):
            opening = dt_time.fromisoformat(opening)
        if isinstance(closing, str):
            closing = dt_time.fromisoformat(closing)
        venues.append(
            SearchVenueResult(
                id=doc["id"],
                name=doc.get("name", ""),
                location=doc.get("location", ""),
                city=doc.get("city", ""),
                opening_time=opening,
                closing_time=closing,
            )
        )

    return SearchResponse(query=term, city=normalized_city, shows=shows, venues=venues)


@router.get("/cities", response_model=list[str])
async def get_cities(
    limit: int = Query(100, ge=1, le=500),
):
    return await es_get_cities(limit=limit)
