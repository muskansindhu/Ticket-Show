from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.encoders import jsonable_encoder
from typing import List
import httpx

from .config import settings
from .auth import get_current_user
from .proxy import proxy_request
from shared.schemas import (
    UserCreate,
    UserLogin,
    Token,
    UserResponse,
)
from shared.schemas.event_schemas import (
    ShowCreate, ShowResponse,
    VenueCreate, VenueResponse,
    ScreenCreate, ScreenResponse,
    ScheduleCreate, ScheduleResponse,
    ScheduleWithDetails
)
from shared.utils import setup_logger

logger = setup_logger(__name__)
security = HTTPBearer()


# ==================== ROUTERS ====================

auth_router = APIRouter(prefix="/auth", tags=["auth"])
shows_router = APIRouter(prefix="/shows", tags=["shows"])
venues_router = APIRouter(prefix="/venues", tags=["venues"])
screens_router = APIRouter(prefix="/screens", tags=["screens"])
schedules_router = APIRouter(prefix="/schedules", tags=["schedules"])


# ==================== AUTH ROUTES ====================

@auth_router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    return await proxy_request(
        "POST",
        f"{settings.AUTH_SERVICE_URL}/auth/register",
        json=user_data.model_dump(),
        timeout=10.0,
    )


@auth_router.post("/login", response_model=Token)
async def login(user_data: UserLogin):
    return await proxy_request(
        "POST",
        f"{settings.AUTH_SERVICE_URL}/auth/login",
        json=user_data.model_dump(),
        timeout=10.0,
    )


@auth_router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: dict = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    return await proxy_request(
        "GET",
        f"{settings.AUTH_SERVICE_URL}/auth/me",
        headers={"Authorization": f"Bearer {credentials.credentials}"},
        timeout=10.0,
    )


# ==================== SHOWS ROUTES ====================

@shows_router.post("/", response_model=ShowResponse, status_code=status.HTTP_201_CREATED)
async def create_show(
    show_data: ShowCreate,
    current_user: dict = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    return await proxy_request(
        "POST",
        f"{settings.EVENT_SERVICE_URL}/shows/",
        json=jsonable_encoder(show_data),
        headers={"Authorization": f"Bearer {credentials.credentials}"},
        timeout=10.0,
    )


@shows_router.get("/", response_model=List[ShowResponse])
async def get_shows(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    return await proxy_request(
        "GET",
        f"{settings.EVENT_SERVICE_URL}/shows/",
        params={"skip": skip, "limit": limit},
        headers={"Authorization": f"Bearer {credentials.credentials}"},
        timeout=10.0,
    )


# ==================== VENUES ROUTES ====================

@venues_router.post("/", response_model=VenueResponse, status_code=status.HTTP_201_CREATED)
async def create_venue(
    venue_data: VenueCreate,
    current_user: dict = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    return await proxy_request(
        "POST",
        f"{settings.EVENT_SERVICE_URL}/venues/",
        json=jsonable_encoder(venue_data),
        headers={"Authorization": f"Bearer {credentials.credentials}"},
        timeout=10.0,
    )


@venues_router.get("/", response_model=List[VenueResponse])
async def get_venues(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    return await proxy_request(
        "GET",
        f"{settings.EVENT_SERVICE_URL}/venues/",
        params={"skip": skip, "limit": limit},
        timeout=10.0,
    )


# ==================== SCREENS ROUTES ====================

@screens_router.post("/", response_model=ScreenResponse, status_code=status.HTTP_201_CREATED)
async def create_screen(
    screen_data: ScreenCreate,
    current_user: dict = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    return await proxy_request(
        "POST",
        f"{settings.EVENT_SERVICE_URL}/screens/",
        json=jsonable_encoder(screen_data),
        headers={"Authorization": f"Bearer {credentials.credentials}"},
        timeout=10.0,
    )


@screens_router.get("/", response_model=List[ScreenResponse])
async def get_screens(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    return await proxy_request(
        "GET",
        f"{settings.EVENT_SERVICE_URL}/screens/",
        params={"skip": skip, "limit": limit},
        timeout=10.0,
    )


# ==================== SCHEDULES ROUTES ====================

@schedules_router.post("/", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    schedule_data: ScheduleCreate,
    current_user: dict = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    return await proxy_request(
        "POST",
        f"{settings.EVENT_SERVICE_URL}/schedules/",
        json=jsonable_encoder(schedule_data),
        headers={"Authorization": f"Bearer {credentials.credentials}"},
        timeout=10.0,
    )


@schedules_router.get("/venue/{venue_id}", response_model=List[ScheduleWithDetails])
async def get_venue_schedules(
    venue_id: int,
    from_date: str = Query(None),
    to_date: str = Query(None),
):
    params = {}
    if from_date:
        params["from_date"] = from_date
    if to_date:
        params["to_date"] = to_date

    return await proxy_request(
        "GET",
        f"{settings.EVENT_SERVICE_URL}/schedules/venue/{venue_id}",
        params=params,
        timeout=10.0,
    )
