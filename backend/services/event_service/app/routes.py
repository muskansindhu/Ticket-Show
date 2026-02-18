from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from shared.schemas.event_schemas import (
    ScheduleCreate,
    ScheduleResponse,
    ScheduleWithDetails,
    ScreenCreate,
    ScreenResponse,
    ShowCreate,
    ShowResponse,
    VenueCreate,
    VenueResponse,
)
from shared.utils import setup_logger
from shared.utils.rbac import create_rbac
from .config import settings
from .database import get_db
from .models import Schedule, Screen, Seat, Show, Venue

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


# ==================== SHOWS (ADMIN ONLY) ====================

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
        return new_show
    except Exception as e:
        logger.error(f"Error creating show: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create show",
        )


@shows_router.get("/", response_model=List[ShowResponse])
async def get_shows(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get all shows (PUBLIC)"""
    try:
        result = await db.execute(
            select(Show).offset(skip).limit(limit).order_by(Show.created_at.desc())
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
    db: AsyncSession = Depends(get_db),
):
    """Get venues that are showing a given show (PUBLIC)"""
    try:
        result = await db.execute(
            select(Venue)
            .join(Screen, Screen.venue_id == Venue.id)
            .join(Schedule, Schedule.screen_id == Screen.id)
            .where(Schedule.show_id == show_id)
            .distinct(Venue.id)
        )
        venues = result.scalars().all()
        return venues

    except Exception as e:
        logger.error(f"Error fetching show venues: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch venues for show",
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
        new_venue = Venue(
            name=venue_data.name,
            location=venue_data.location,
            opening_time=venue_data.opening_time,
            closing_time=venue_data.closing_time,
        )

        db.add(new_venue)
        await db.commit()
        await db.refresh(new_venue)

        logger.info(f"Venue created: {new_venue.name} by admin {current_user['user_id']}")

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
    db: AsyncSession = Depends(get_db),
):
    """Get all venues (PUBLIC)"""
    try:
        result = await db.execute(select(Venue).offset(skip).limit(limit))
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
    db: AsyncSession = Depends(get_db),
):
    return await get_venues(skip=skip, limit=limit, db=db)


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

# ==================== SCHEDULES (ADMIN CREATE, USER VIEW) ====================

@schedules_router.post("/", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    schedule_data: ScheduleCreate,
    current_user: dict = Depends(rbac.require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new schedule (ADMIN only) with scheduling constraints enforcement"""
    try:
        # 1. Fetch show to get duration
        show_result = await db.execute(
            select(Show).where(Show.id == schedule_data.show_id)
        )
        show = show_result.scalar_one_or_none()

        if not show:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Show not found",
            )

        # 2. Fetch screen and venue
        screen_result = await db.execute(
            select(Screen).where(Screen.id == schedule_data.screen_id)
        )
        screen = screen_result.scalar_one_or_none()

        if not screen:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Screen not found",
            )

        venue_result = await db.execute(
            select(Venue).where(Venue.id == screen.venue_id)
        )
        venue = venue_result.scalar_one_or_none()

        # 3. Calculate end_time based on show duration
        end_time = schedule_data.start_time + timedelta(minutes=show.duration_minutes)

        # 4. CONSTRAINT: Validate venue operating hours
        start_time_of_day = schedule_data.start_time.time()
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

        # 5. Create schedule
        # PostgreSQL exclusion constraint will automatically prevent overlapping schedules
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


@schedules_router.get("/venue/{venue_id}", response_model=List[ScheduleWithDetails])
async def get_venue_schedules(
    venue_id: int,
    from_date: datetime = Query(None),
    to_date: datetime = Query(None),
    show_id: int = Query(None),
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
