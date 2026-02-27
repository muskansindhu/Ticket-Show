from datetime import datetime, timedelta
from pathlib import Path
import uuid
from typing import List

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from shared.schemas.event_schemas import (
    ScheduleCreate,
    ScheduleResponse,
    ScheduleUpdate,
    ScheduleWithDetails,
    ScreenCreate,
    ScreenResponse,
    ScreenUpdate,
    ShowCreate,
    ShowResponse,
    ShowStatus,
    ShowUpdate,
    VenueCreate,
    VenueResponse,
    VenueStatus,
    VenueUpdate,
)
from shared.utils import setup_logger
from shared.utils.rbac import create_rbac
from .config import settings
from .database import get_db
from .kafka_handler import publish_show_changed, publish_venue_changed
from .models import Schedule, Screen, Seat, Show, Venue
from .s3_client import delete_poster, upload_poster

logger = setup_logger(__name__)

# Create RBAC instance
rbac = create_rbac(
    settings.JWT_SECRET if hasattr(settings, "JWT_SECRET") else "default-secret"
)

# Routers
shows_router = APIRouter(prefix="/shows", tags=["shows"])
venues_router = APIRouter(prefix="/venues", tags=["venues"])
screens_router = APIRouter(prefix="/screens", tags=["screens"])
schedules_router = APIRouter(prefix="/schedules", tags=["schedules"])

ALLOWED_POSTER_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


async def _get_show_or_404(show_id: int, db: AsyncSession):
    result = await db.execute(select(Show).where(Show.id == show_id))
    show = result.scalar_one_or_none()
    if not show:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Show not found",
        )
    return show


async def _get_screen_or_404(screen_id: int, db: AsyncSession):
    result = await db.execute(select(Screen).where(Screen.id == screen_id))
    screen = result.scalar_one_or_none()
    if not screen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Screen not found",
        )
    return screen


async def _get_venue_for_screen(screen: Screen, db: AsyncSession):
    result = await db.execute(select(Venue).where(Venue.id == screen.venue_id))
    venue = result.scalar_one_or_none()
    if not venue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venue not found",
        )
    return venue


def _validate_schedule_window(start_time: datetime, end_time: datetime, venue: Venue):
    start_time_of_day = start_time.time()
    end_time_of_day = end_time.time()

    if start_time_of_day < venue.opening_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Schedule start time "
                f"({start_time_of_day}) is before venue opening time "
                f"({venue.opening_time})"
            ),
        )

    if end_time_of_day > venue.closing_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Schedule end time "
                f"({end_time_of_day}) is after venue closing time "
                f"({venue.closing_time})"
            ),
        )


def _ensure_show_is_active(show: Show):
    if show.status != ShowStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot use a cancelled show for scheduling",
        )


def _ensure_venue_is_active(venue: Venue):
    if venue.status != VenueStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot use an inactive venue for scheduling",
        )


async def _cancel_related_bookings(path: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.BOOKING_SERVICE_URL}{path}",
                timeout=15.0,
            )
            if response.status_code >= 400:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Failed to cancel related bookings",
                )
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Booking service unavailable",
        )


# ==================== SHOWS (ADMIN ONLY) ======================================

@shows_router.post("/", response_model=ShowResponse, status_code=status.HTTP_201_CREATED)
async def create_show(
    show_data: ShowCreate,
    current_user: dict = Depends(rbac.require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new show (ADMIN only)"""
    try:
        new_show = Show(
            title=show_data.title,
            status=ShowStatus.ACTIVE.value,
            duration_minutes=show_data.duration_minutes,
            price=show_data.price,
            description=show_data.description,
            language=show_data.language,
            rating=show_data.rating,
        )
        db.add(new_show)
        await db.commit()
        await db.refresh(new_show)
        logger.info(f"Show created: {new_show.title} by admin {current_user['user_id']}")
        await publish_show_changed({
            "id": new_show.id,
            "title": new_show.title,
            "description": new_show.description,
            "duration_minutes": new_show.duration_minutes,
            "price": new_show.price,
            "language": new_show.language,
            "rating": new_show.rating,
            "status": new_show.status,
            "action": "created",
        })
        return new_show
    except Exception as e:
        logger.error(f"Error creating show: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create show",
        )


@shows_router.post("/{show_id}/poster", response_model=ShowResponse)
async def upload_show_poster(
    show_id: int,
    poster: UploadFile = File(...),
    current_user: dict = Depends(rbac.require_admin),
    db: AsyncSession = Depends(get_db),
):
    show = await _get_show_or_404(show_id, db)
    content_type = (poster.content_type or "").lower()
    if not content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Poster must be an image file",
        )

    extension = Path(poster.filename or "").suffix.lower()
    if extension not in ALLOWED_POSTER_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Allowed poster formats: .jpg, .jpeg, .png, .webp",
        )

    payload = await poster.read()
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Poster file is empty",
        )
    if len(payload) > settings.MAX_POSTER_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Poster file size exceeds 5 MB limit",
        )

    filename = f"show-{show.id}-{uuid.uuid4().hex[:12]}{extension}"
    poster_url = upload_poster(payload, filename, content_type)

    old_poster_url = show.poster_url
    show.poster_url = poster_url
    await db.commit()
    await db.refresh(show)

    if old_poster_url:
        delete_poster(old_poster_url)

    logger.info("Poster uploaded for show %s by admin %s", show.id, current_user["user_id"])
    return show


@shows_router.get("/", response_model=List[ShowResponse])
async def get_shows(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    include_cancelled: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    """Get all shows (PUBLIC)"""
    try:
        query = select(Show)
        if not include_cancelled:
            query = query.where(Show.status == ShowStatus.ACTIVE.value)
        result = await db.execute(
            query.offset(skip).limit(limit).order_by(Show.created_at.desc())
        )
        shows = result.scalars().all()
        return shows

    except Exception as e:
        logger.error(f"Error fetching shows: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch shows",
        )


@shows_router.get("/{show_id}/venues", response_model=List[VenueResponse])
async def get_show_venues(
    show_id: int,
    city: str | None = Query(None, min_length=1, max_length=100),
    db: AsyncSession = Depends(get_db),
):
    """Get venues that are showing a given show (PUBLIC)"""
    try:
        query = (
            select(Venue)
            .join(Screen, Screen.venue_id == Venue.id)
            .join(Schedule, Schedule.screen_id == Screen.id)
            .join(Show, Show.id == Schedule.show_id)
            .where(Schedule.show_id == show_id)
            .where(Show.status == ShowStatus.ACTIVE.value)
            .where(Venue.status == VenueStatus.ACTIVE.value)
            .distinct(Venue.id)
        )
        normalized_city = city.strip() if city else ""
        if normalized_city:
            query = query.where(Venue.city.ilike(normalized_city))
        result = await db.execute(query)
        venues = result.scalars().all()
        return venues

    except Exception as e:
        logger.error(f"Error fetching show venues: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch venues for show",
        )


@shows_router.patch("/{show_id}", response_model=ShowResponse)
async def update_show(
    show_id: int,
    show_data: ShowUpdate,
    current_user: dict = Depends(rbac.require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing show (ADMIN only)"""
    try:
        show = await _get_show_or_404(show_id, db)
        payload = show_data.model_dump(exclude_unset=True)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields provided for update",
            )

        for field, value in payload.items():
            setattr(show, field, value)

        next_show_status = payload.get("status")
        if isinstance(next_show_status, ShowStatus):
            next_show_status = next_show_status.value
        if next_show_status == ShowStatus.CANCELLED.value:
            await _cancel_related_bookings(
                f"/bookings/internal/cancel-by-show/{show.id}"
            )

        await db.commit()
        await db.refresh(show)
        logger.info("Show updated: %s by admin %s", show.title, current_user["user_id"])
        await publish_show_changed({
            "id": show.id,
            "title": show.title,
            "description": show.description,
            "duration_minutes": show.duration_minutes,
            "price": show.price,
            "language": show.language,
            "rating": show.rating,
            "status": show.status,
            "action": "updated",
        })
        return show
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating show: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update show",
        )


@shows_router.delete("/{show_id}")
async def delete_show(
    show_id: int,
    current_user: dict = Depends(rbac.require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Mark a show as cancelled and trigger related booking cancellations."""
    try:
        show = await _get_show_or_404(show_id, db)
        if show.status == ShowStatus.CANCELLED.value:
            return {"detail": "Show already cancelled"}

        show.status = ShowStatus.CANCELLED.value
        await _cancel_related_bookings(
            f"/bookings/internal/cancel-by-show/{show.id}"
        )
        await db.commit()
        logger.info("Show cancelled: %s by admin %s", show.title, current_user["user_id"])
        await publish_show_changed({
            "id": show.id,
            "title": show.title,
            "status": ShowStatus.CANCELLED.value,
            "action": "deleted",
        })
        return {"detail": "Show cancelled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting show: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete show",
        )


# ==================== VENUES (ADMIN ONLY) ====================

@venues_router.post("/", response_model=VenueResponse, status_code=status.HTTP_201_CREATED)
async def create_venue(
    venue_data: VenueCreate,
    current_user: dict = Depends(rbac.require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new venue (ADMIN only)"""
    try:
        city = venue_data.city.strip()
        if not city:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="city cannot be empty",
            )
        new_venue = Venue(
            name=venue_data.name,
            status=VenueStatus.ACTIVE.value,
            location=venue_data.location,
            city=city,
            opening_time=venue_data.opening_time,
            closing_time=venue_data.closing_time,
        )

        db.add(new_venue)
        await db.commit()
        await db.refresh(new_venue)

        logger.info(f"Venue created: {new_venue.name} by admin {current_user['user_id']}")
        await publish_venue_changed({
            "id": new_venue.id,
            "name": new_venue.name,
            "location": new_venue.location,
            "city": new_venue.city,
            "opening_time": str(new_venue.opening_time),
            "closing_time": str(new_venue.closing_time),
            "status": new_venue.status,
            "action": "created",
        })
        return new_venue

    except Exception as e:
        logger.error(f"Error creating venue: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create venue",
        )


@venues_router.get("/", response_model=List[VenueResponse])
async def get_venues(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    include_inactive: bool = Query(False),
    city: str | None = Query(None, min_length=1, max_length=100),
    db: AsyncSession = Depends(get_db),
):
    """Get all venues (PUBLIC)"""
    try:
        query = select(Venue)
        if not include_inactive:
            query = query.where(Venue.status == VenueStatus.ACTIVE.value)
        normalized_city = city.strip() if city else ""
        if normalized_city:
            query = query.where(Venue.city.ilike(normalized_city))
        result = await db.execute(query.offset(skip).limit(limit))
        venues = result.scalars().all()
        return venues

    except Exception as e:
        logger.error(f"Error fetching venues: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch venues",
        )


@venues_router.get("", response_model=List[VenueResponse], include_in_schema=False)
async def get_venues_no_slash(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    include_inactive: bool = Query(False),
    city: str | None = Query(None, min_length=1, max_length=100),
    db: AsyncSession = Depends(get_db),
):
    return await get_venues(
        skip=skip,
        limit=limit,
        include_inactive=include_inactive,
        city=city,
        db=db,
    )


@venues_router.patch("/{venue_id}", response_model=VenueResponse)
async def update_venue(
    venue_id: int,
    venue_data: VenueUpdate,
    current_user: dict = Depends(rbac.require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing venue (ADMIN only)"""
    try:
        result = await db.execute(select(Venue).where(Venue.id == venue_id))
        venue = result.scalar_one_or_none()
        if not venue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Venue not found",
            )
        _ensure_venue_is_active(venue)

        payload = venue_data.model_dump(exclude_unset=True)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields provided for update",
            )

        if "opening_time" in payload and payload["opening_time"] is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="opening_time cannot be null",
            )

        if "closing_time" in payload and payload["closing_time"] is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="closing_time cannot be null",
            )
        if "city" in payload:
            next_city = str(payload["city"] or "").strip()
            if not next_city:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="city cannot be empty",
                )
            payload["city"] = next_city

        opening_time = (
            payload["opening_time"]
            if "opening_time" in payload
            else venue.opening_time
        )
        closing_time = (
            payload["closing_time"]
            if "closing_time" in payload
            else venue.closing_time
        )
        if closing_time <= opening_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="closing_time must be after opening_time",
            )

        for field, value in payload.items():
            setattr(venue, field, value)

        next_venue_status = payload.get("status")
        if isinstance(next_venue_status, VenueStatus):
            next_venue_status = next_venue_status.value
        if next_venue_status == VenueStatus.INACTIVE.value:
            await _cancel_related_bookings(
                f"/bookings/internal/cancel-by-venue/{venue.id}"
            )

        await db.commit()
        await db.refresh(venue)
        logger.info("Venue updated: %s by admin %s", venue.name, current_user["user_id"])
        await publish_venue_changed({
            "id": venue.id,
            "name": venue.name,
            "location": venue.location,
            "city": venue.city,
            "opening_time": str(venue.opening_time),
            "closing_time": str(venue.closing_time),
            "status": venue.status,
            "action": "updated",
        })
        return venue
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating venue: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update venue",
        )


@venues_router.delete("/{venue_id}")
async def delete_venue(
    venue_id: int,
    current_user: dict = Depends(rbac.require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Mark a venue inactive and trigger related booking cancellations."""
    try:
        result = await db.execute(select(Venue).where(Venue.id == venue_id))
        venue = result.scalar_one_or_none()
        if not venue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Venue not found",
            )
        if venue.status == VenueStatus.INACTIVE.value:
            return {"detail": "Venue already inactive"}

        venue.status = VenueStatus.INACTIVE.value
        await _cancel_related_bookings(
            f"/bookings/internal/cancel-by-venue/{venue.id}"
        )
        await db.commit()
        logger.info("Venue inactivated: %s by admin %s", venue.name, current_user["user_id"])
        await publish_venue_changed({
            "id": venue.id,
            "name": venue.name,
            "status": VenueStatus.INACTIVE.value,
            "action": "deleted",
        })
        return {"detail": "Venue marked inactive successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting venue: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete venue",
        )


# ==================== SCREENS (ADMIN ONLY) ====================

@screens_router.post("/", response_model=ScreenResponse, status_code=status.HTTP_201_CREATED)
async def create_screen(
    screen_data: ScreenCreate,
    current_user: dict = Depends(rbac.require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new screen (ADMIN only)"""
    try:
        # Verify venue exists
        venue_result = await db.execute(
            select(Venue).where(Venue.id == screen_data.venue_id)
        )
        venue = venue_result.scalar_one_or_none()

        if not venue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Venue not found",
            )

        new_screen = Screen(
            venue_id=screen_data.venue_id,
            name=screen_data.name,
            capacity=screen_data.capacity,
        )

        db.add(new_screen)
        await db.commit()
        await db.refresh(new_screen)

        # Create seats for the screen
        seats = []
        for i in range(1, screen_data.capacity + 1):
            seat = Seat(
                screen_id=new_screen.id,
                seat_number=f"S{str(i).zfill(3)}",
                row_number=f"R{str((i - 1) // 10 + 1).zfill(2)}",
            )
            seats.append(seat)

        db.add_all(seats)
        await db.commit()

        logger.info(
            "Screen created: %s with %s seats by admin %s",
            new_screen.name,
            screen_data.capacity,
            current_user["user_id"],
        )

        return new_screen

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating screen: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create screen",
        )


@screens_router.get("/", response_model=List[ScreenResponse])
async def get_screens(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get all screens (PUBLIC)"""
    try:
        result = await db.execute(select(Screen).offset(skip).limit(limit))
        screens = result.scalars().all()
        return screens

    except Exception as e:
        logger.error(f"Error fetching screens: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch screens",
        )


@screens_router.patch("/{screen_id}", response_model=ScreenResponse)
async def update_screen(
    screen_id: int,
    screen_data: ScreenUpdate,
    current_user: dict = Depends(rbac.require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing screen (ADMIN only)"""
    try:
        screen = await _get_screen_or_404(screen_id, db)
        payload = screen_data.model_dump(exclude_unset=True)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields provided for update",
            )

        if "name" in payload:
            screen.name = payload["name"]

        if "capacity" in payload:
            new_capacity = payload["capacity"]
            if new_capacity < screen.capacity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Reducing screen capacity is not supported",
                )
            if new_capacity > screen.capacity:
                seats = []
                for i in range(screen.capacity + 1, new_capacity + 1):
                    seat = Seat(
                        screen_id=screen.id,
                        seat_number=f"S{str(i).zfill(3)}",
                        row_number=f"R{str((i - 1) // 10 + 1).zfill(2)}",
                    )
                    seats.append(seat)
                if seats:
                    db.add_all(seats)
                screen.capacity = new_capacity

        await db.commit()
        await db.refresh(screen)
        logger.info("Screen updated: %s by admin %s", screen.name, current_user["user_id"])
        return screen
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating screen: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update screen",
        )


# ==================== SCHEDULES (ADMIN CREATE, USER VIEW) ====================

@schedules_router.post("/", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    schedule_data: ScheduleCreate,
    current_user: dict = Depends(rbac.require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new schedule (ADMIN only) with scheduling constraints enforcement"""
    try:
        show = await _get_show_or_404(schedule_data.show_id, db)
        screen = await _get_screen_or_404(schedule_data.screen_id, db)
        venue = await _get_venue_for_screen(screen, db)
        _ensure_show_is_active(show)
        _ensure_venue_is_active(venue)

        end_time = schedule_data.start_time + timedelta(minutes=show.duration_minutes)
        _validate_schedule_window(schedule_data.start_time, end_time, venue)

        new_schedule = Schedule(
            show_id=schedule_data.show_id,
            screen_id=schedule_data.screen_id,
            start_time=schedule_data.start_time,
            end_time=end_time,
            created_by_admin_id=int(current_user["user_id"]),
        )

        db.add(new_schedule)
        await db.commit()
        await db.refresh(new_schedule)

        logger.info(
            "Schedule created: Show %s on Screen %s at %s by admin %s",
            show.title,
            screen.name,
            schedule_data.start_time,
            current_user["user_id"],
        )

        return new_schedule

    except HTTPException:
        raise
    except IntegrityError as e:
        await db.rollback()
        # This catches the exclusion constraint violation
        if "no_overlapping_schedules" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Schedule conflicts with existing schedule on this screen",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database integrity error",
        )
    except Exception as e:
        logger.error(f"Error creating schedule: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create schedule",
        )


@schedules_router.patch("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: int,
    schedule_data: ScheduleUpdate,
    current_user: dict = Depends(rbac.require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing schedule (ADMIN only)"""
    try:
        result = await db.execute(select(Schedule).where(Schedule.id == schedule_id))
        schedule = result.scalar_one_or_none()
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule not found",
            )

        payload = schedule_data.model_dump(exclude_unset=True)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields provided for update",
            )

        show_id = payload.get("show_id", schedule.show_id)
        screen_id = payload.get("screen_id", schedule.screen_id)
        start_time = payload.get("start_time", schedule.start_time)

        show = await _get_show_or_404(show_id, db)
        screen = await _get_screen_or_404(screen_id, db)
        venue = await _get_venue_for_screen(screen, db)
        _ensure_show_is_active(show)
        _ensure_venue_is_active(venue)

        end_time = start_time + timedelta(minutes=show.duration_minutes)
        _validate_schedule_window(start_time, end_time, venue)

        schedule.show_id = show_id
        schedule.screen_id = screen_id
        schedule.start_time = start_time
        schedule.end_time = end_time

        await db.commit()
        await db.refresh(schedule)
        logger.info("Schedule updated: %s by admin %s", schedule.id, current_user["user_id"])
        return schedule

    except HTTPException:
        raise
    except IntegrityError as e:
        await db.rollback()
        if "no_overlapping_schedules" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Schedule conflicts with existing schedule on this screen",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database integrity error",
        )
    except Exception as e:
        logger.error(f"Error updating schedule: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update schedule",
        )


@schedules_router.get("/venue/{venue_id}", response_model=List[ScheduleWithDetails])
async def get_venue_schedules(
    venue_id: int,
    from_date: datetime = Query(None),
    to_date: datetime = Query(None),
    show_id: int = Query(None),
    include_cancelled: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    """Get all schedules for a venue (PUBLIC)"""
    try:
        # Build query with joins
        query = (
            select(
                Schedule.id,
                Show.title.label("show_title"),
                Show.duration_minutes.label("show_duration"),
                Screen.name.label("screen_name"),
                Venue.name.label("venue_name"),
                Schedule.start_time,
                Schedule.end_time,
                Schedule.created_at,
            )
            .join(Screen, Schedule.screen_id == Screen.id)
            .join(Venue, Screen.venue_id == Venue.id)
            .join(Show, Schedule.show_id == Show.id)
            .where(Venue.id == venue_id)
        )

        if not include_cancelled:
            query = query.where(Venue.status == VenueStatus.ACTIVE.value)
            query = query.where(Show.status == ShowStatus.ACTIVE.value)

        # Add date filters if provided
        if from_date:
            query = query.where(Schedule.start_time >= from_date)
        if to_date:
            query = query.where(Schedule.start_time <= to_date)
        if show_id:
            query = query.where(Schedule.show_id == show_id)

        query = query.order_by(Schedule.start_time)

        result = await db.execute(query)
        schedules = [
            ScheduleWithDetails(
                id=row.id,
                show_title=row.show_title,
                show_duration=row.show_duration,
                screen_name=row.screen_name,
                venue_name=row.venue_name,
                start_time=row.start_time,
                end_time=row.end_time,
                created_at=row.created_at,
            )
            for row in result.fetchall()
        ]

        return schedules

    except Exception as e:
        logger.error(f"Error fetching schedules: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch schedules",
        )
