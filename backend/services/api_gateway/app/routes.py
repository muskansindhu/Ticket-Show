from typing import List

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, Response, UploadFile, status
from fastapi.encoders import jsonable_encoder
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from shared.schemas import (
    BookingCreate,
    BookingResponse,
    PaymentCreate,
    PaymentResponse,
    Token,
    UserCreate,
    UserLogin,
    UserResponse,
    WalletResponse,
)
from shared.schemas.event_schemas import (
    SearchResponse,
    ScheduleCreate,
    ScheduleResponse,
    ScheduleWithDetails,
    ScreenCreate,
    ScreenResponse,
    ShowCreate,
    ShowUpdate,
    ShowResponse,
    VenueCreate,
    VenueUpdate,
    VenueResponse,
)
from .auth import get_current_user
from .config import settings
from .proxy import proxy_request

security = HTTPBearer()


# ==================== ROUTERS ====================

auth_router = APIRouter(prefix="/auth", tags=["auth"])
shows_router = APIRouter(prefix="/shows", tags=["shows"])
venues_router = APIRouter(prefix="/venues", tags=["venues"])
screens_router = APIRouter(prefix="/screens", tags=["screens"])
schedules_router = APIRouter(prefix="/schedules", tags=["schedules"])
bookings_router = APIRouter(prefix="/bookings", tags=["bookings"])
payments_router = APIRouter(prefix="/payments", tags=["payments"])
search_router = APIRouter(prefix="/search", tags=["search"])


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


@auth_router.get("/wallet", response_model=WalletResponse)
async def get_wallet(
    current_user: dict = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    return await proxy_request(
        "GET",
        f"{settings.AUTH_SERVICE_URL}/auth/wallet",
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


@shows_router.post("/{show_id}/poster", response_model=ShowResponse)
async def upload_show_poster(
    show_id: int,
    poster: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    payload = await poster.read()
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Poster file is empty",
        )
    return await proxy_request(
        "POST",
        f"{settings.EVENT_SERVICE_URL}/shows/{show_id}/poster",
        files={
            "poster": (
                poster.filename or "poster.jpg",
                payload,
                poster.content_type or "application/octet-stream",
            )
        },
        headers={"Authorization": f"Bearer {credentials.credentials}"},
        timeout=30.0,
    )


@shows_router.get("/posters/{filename}")
async def get_show_poster(filename: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.EVENT_SERVICE_URL}/shows/posters/{filename}",
                timeout=20.0,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = "Failed to fetch poster"
            try:
                payload = exc.response.json()
                if isinstance(payload, dict) and payload.get("detail"):
                    detail = payload["detail"]
            except Exception:
                if exc.response.text:
                    detail = exc.response.text
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=detail,
            )
        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service unavailable",
            )

    return Response(
        content=response.content,
        media_type=response.headers.get("content-type", "application/octet-stream"),
    )


@shows_router.get("/", response_model=List[ShowResponse])
async def get_shows(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    include_cancelled: bool = Query(False),
):
    return await proxy_request(
        "GET",
        f"{settings.EVENT_SERVICE_URL}/shows/",
        params={
            "skip": skip,
            "limit": limit,
            "include_cancelled": include_cancelled,
        },
        timeout=10.0,
    )


@shows_router.get("", response_model=List[ShowResponse], include_in_schema=False)
async def get_shows_no_slash(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    include_cancelled: bool = Query(False),
):
    return await get_shows(
        skip=skip,
        limit=limit,
        include_cancelled=include_cancelled,
    )


@shows_router.get("/{show_id}/venues", response_model=List[VenueResponse])
async def get_show_venues(
    show_id: int,
    city: str | None = Query(None, min_length=1, max_length=100),
):
    params = {}
    normalized_city = city.strip() if city else ""
    if normalized_city:
        params["city"] = normalized_city
    return await proxy_request(
        "GET",
        f"{settings.EVENT_SERVICE_URL}/shows/{show_id}/venues",
        params=params,
        timeout=10.0,
    )


@shows_router.patch("/{show_id}", response_model=ShowResponse)
async def update_show(
    show_id: int,
    show_data: ShowUpdate,
    current_user: dict = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    return await proxy_request(
        "PATCH",
        f"{settings.EVENT_SERVICE_URL}/shows/{show_id}",
        json=jsonable_encoder(show_data.model_dump(exclude_unset=True)),
        headers={"Authorization": f"Bearer {credentials.credentials}"},
        timeout=10.0,
    )


@shows_router.delete("/{show_id}")
async def delete_show(
    show_id: int,
    current_user: dict = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    return await proxy_request(
        "DELETE",
        f"{settings.EVENT_SERVICE_URL}/shows/{show_id}",
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
    include_inactive: bool = Query(False),
    city: str | None = Query(None, min_length=1, max_length=100),
):
    params = {
        "skip": skip,
        "limit": limit,
        "include_inactive": include_inactive,
    }
    normalized_city = city.strip() if city else ""
    if normalized_city:
        params["city"] = normalized_city
    return await proxy_request(
        "GET",
        f"{settings.EVENT_SERVICE_URL}/venues/",
        params=params,
        timeout=10.0,
    )


@venues_router.get("", response_model=List[VenueResponse], include_in_schema=False)
async def get_venues_no_slash(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    include_inactive: bool = Query(False),
    city: str | None = Query(None, min_length=1, max_length=100),
):
    return await get_venues(
        skip=skip,
        limit=limit,
        include_inactive=include_inactive,
        city=city,
    )


@venues_router.patch("/{venue_id}", response_model=VenueResponse)
async def update_venue(
    venue_id: int,
    venue_data: VenueUpdate,
    current_user: dict = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    return await proxy_request(
        "PATCH",
        f"{settings.EVENT_SERVICE_URL}/venues/{venue_id}",
        json=jsonable_encoder(venue_data.model_dump(exclude_unset=True)),
        headers={"Authorization": f"Bearer {credentials.credentials}"},
        timeout=10.0,
    )


@venues_router.delete("/{venue_id}")
async def delete_venue(
    venue_id: int,
    current_user: dict = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    return await proxy_request(
        "DELETE",
        f"{settings.EVENT_SERVICE_URL}/venues/{venue_id}",
        headers={"Authorization": f"Bearer {credentials.credentials}"},
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


@screens_router.get("", response_model=List[ScreenResponse], include_in_schema=False)
async def get_screens_no_slash(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    return await get_screens(skip=skip, limit=limit)


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
    show_id: int = Query(None),
    include_cancelled: bool = Query(False),
):
    params = {}
    if from_date:
        params["from_date"] = from_date
    if to_date:
        params["to_date"] = to_date
    if show_id:
        params["show_id"] = show_id
    if include_cancelled:
        params["include_cancelled"] = include_cancelled

    return await proxy_request(
        "GET",
        f"{settings.EVENT_SERVICE_URL}/schedules/venue/{venue_id}",
        params=params,
        timeout=10.0,
    )



# ==================== BOOKING ROUTES ====================

@bookings_router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking_data: BookingCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new booking"""

    return await proxy_request(
        "POST",
        f"{settings.BOOKING_SERVICE_URL}/bookings",
        json=jsonable_encoder(booking_data),
        params={"user_id": current_user["user_id"]},
        timeout=10.0,
    )


@bookings_router.get("", response_model=List[BookingResponse])
async def get_user_bookings(current_user: dict = Depends(get_current_user)):
    """Get all bookings for current user"""

    return await proxy_request(
        "GET",
        f"{settings.BOOKING_SERVICE_URL}/bookings/",
        params={"user_id": current_user["user_id"]},
        timeout=10.0,
    )


@bookings_router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get booking by ID"""

    return await proxy_request(
        "GET",
        f"{settings.BOOKING_SERVICE_URL}/bookings/{booking_id}",
        params={"user_id": current_user["user_id"]},
        timeout=10.0,
    )


@bookings_router.get("/schedule/{schedule_id}/seats")
async def get_schedule_seats(
    schedule_id: int,
    current_user: dict = Depends(get_current_user),
):
    return await proxy_request(
        "GET",
        f"{settings.BOOKING_SERVICE_URL}/bookings/schedule/{schedule_id}/seats",
        params={"user_id": current_user["user_id"]},
        timeout=10.0,
    )


@bookings_router.delete("/{booking_id}")
async def cancel_booking(
    booking_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Cancel a booking"""
    
    return await proxy_request(
        "DELETE",
        f"{settings.BOOKING_SERVICE_URL}/bookings/{booking_id}",
        params={"user_id": current_user["user_id"]},
        timeout=10.0,
    )


# ==================== PAYMENT ROUTES ====================

@payments_router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def make_payment(
    payment_data: PaymentCreate,
    current_user: dict = Depends(get_current_user)
):
    """Make a payment for a booking"""
    payload = payment_data
    if payment_data.user_email is None:
        payload = payment_data.model_copy(
            update={"user_email": current_user.get("email")}
        )
    return await proxy_request(
        "POST",
        f"{settings.PAYMENT_SERVICE_URL}/payments",
        json=jsonable_encoder(payload),
        timeout=10.0,
    )


@payments_router.post("/webhook")
async def dodo_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("webhook-signature") or request.headers.get("x-webhook-signature")
    webhook_id = request.headers.get("webhook-id")
    webhook_timestamp = request.headers.get("webhook-timestamp")
    headers = {"content-type": "application/json"}
    if signature:
        headers["webhook-signature"] = signature
    if webhook_id:
        headers["webhook-id"] = webhook_id
    if webhook_timestamp:
        headers["webhook-timestamp"] = webhook_timestamp
    return await proxy_request(
        "POST",
        f"{settings.PAYMENT_SERVICE_URL}/payments/webhook",
        content=body,
        headers=headers,
        timeout=10.0,
    )

@payments_router.get("/booking/{booking_id}", response_model=PaymentResponse)
async def get_payment_by_booking(
    booking_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get payment by booking ID"""
    return await proxy_request(
        "GET",
        f"{settings.PAYMENT_SERVICE_URL}/payments/booking/{booking_id}",
        params={"user_id": current_user["user_id"]},
        timeout=10.0,
    )

@payments_router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get payment by payment ID"""
    return await proxy_request(
        "GET",
        f"{settings.PAYMENT_SERVICE_URL}/payments/{payment_id}",
        params={"user_id": current_user["user_id"]},
        timeout=10.0,
    )


# ==================== SEARCH ROUTES ====================

@search_router.get("", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1, max_length=120),
    city: str | None = Query(None, min_length=1, max_length=100),
    limit: int = Query(8, ge=1, le=50),
):
    params = {"q": q, "limit": limit}
    normalized_city = city.strip() if city else ""
    if normalized_city:
        params["city"] = normalized_city
    return await proxy_request(
        "GET",
        f"{settings.SEARCH_SERVICE_URL}/search",
        params=params,
        timeout=10.0,
    )


@search_router.get("/cities", response_model=List[str])
async def search_cities(limit: int = Query(100, ge=1, le=500)):
    return await proxy_request(
        "GET",
        f"{settings.SEARCH_SERVICE_URL}/search/cities",
        params={"limit": limit},
        timeout=10.0,
    )
