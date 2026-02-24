from datetime import datetime, timedelta, timezone
import uuid
from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy import and_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from shared.schemas import BookingCreate, BookingResponse, BookingStatus
from shared.schemas import ShowStatus, VenueStatus
from shared.utils import setup_logger
from .database import get_db
from .kafka_handler import publish_refund_initiated, publish_refund_notification
from .models import Booking

logger = setup_logger(__name__)
router = APIRouter(prefix="/bookings", tags=["bookings"])


async def lock_seats(
    db: AsyncSession,
    screen_id: int,
    seat_ids: List[int],
    lock_duration_minutes: int = 10,
):
    """Lock seats for a screen using row-level lock checks."""
    try:
        lock_until = datetime.now(timezone.utc) + timedelta(minutes=lock_duration_minutes)
        query = text(
            """
            UPDATE events.seats
            SET locked_until = :lock_until,
                updated_at = NOW()
            WHERE id = ANY(:seat_ids)
              AND screen_id = :screen_id
              AND (locked_until IS NULL OR locked_until < NOW())
            RETURNING id
            """
        )
        result = await db.execute(
            query,
            {
                "seat_ids": seat_ids,
                "screen_id": screen_id,
                "lock_until": lock_until,
            },
        )
        locked_seat_ids = [row[0] for row in result.fetchall()]
        if len(locked_seat_ids) != len(seat_ids):
            await db.rollback()
            return False, []
        return True, locked_seat_ids
    except Exception as e:
        logger.error(f"Error locking seats: {str(e)}", exc_info=True)
        await db.rollback()
        return False, []


async def release_seats(
    db: AsyncSession,
    screen_id: int,
    seat_ids: List[int],
    commit: bool = True,
):
    """Release locked seats for a screen."""
    try:
        query = text(
            """
            UPDATE events.seats
            SET locked_until = NULL,
                updated_at = NOW()
            WHERE id = ANY(:seat_ids)
              AND screen_id = :screen_id
            """
        )
        await db.execute(
            query,
            {
                "seat_ids": seat_ids,
                "screen_id": screen_id,
            },
        )
        if commit:
            await db.commit()
    except Exception as e:
        logger.error(f"Error releasing seats: {str(e)}", exc_info=True)
        await db.rollback()


async def _get_screen_id_for_schedule(db: AsyncSession, schedule_id: int) -> int | None:
    schedule_query = text("SELECT screen_id FROM events.schedules WHERE id = :schedule_id")
    schedule_result = await db.execute(schedule_query, {"schedule_id": schedule_id})
    schedule_row = schedule_result.fetchone()
    if not schedule_row:
        return None
    return schedule_row[0]


async def _publish_refund_events(event: dict):
    try:
        await publish_refund_initiated(event)
        await publish_refund_notification(event)
    except RuntimeError:
        # Tests can invoke routes without service startup hooks.
        logger.warning("Kafka producer not initialized; skipping refund events")


async def _cancel_bookings(
    bookings: List[Booking],
    db: AsyncSession,
    reason: str,
    initiated_by: str,
) -> int:
    cancelled_count = 0

    for booking in bookings:
        if booking.status not in {
            BookingStatus.PENDING.value,
            BookingStatus.CONFIRMED.value,
        }:
            continue

        screen_id = await _get_screen_id_for_schedule(db, booking.schedule_id)
        if screen_id:
            await release_seats(db, screen_id, booking.seat_ids, commit=False)

        booking.status = BookingStatus.CANCELLED.value
        correlation_id = str(uuid.uuid4())
        refund_event = {
            "booking_id": booking.id,
            "user_id": booking.user_id,
            "amount": float(booking.total_amount),
            "correlation_id": correlation_id,
            "reason": reason,
            "initiated_by": initiated_by,
            "initiated_at": datetime.utcnow().isoformat(),
        }
        await _publish_refund_events(refund_event)
        cancelled_count += 1

    if cancelled_count > 0:
        await db.commit()

    return cancelled_count


@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking_data: BookingCreate,
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Create a new booking with seat locking (using schedule_id)."""
    correlation_id = str(uuid.uuid4())
    try:
        result = await db.execute(
            select(Booking).where(Booking.idempotency_key == booking_data.idempotency_key)
        )
        existing_booking = result.scalar_one_or_none()
        if existing_booking:
            logger.info(f"Idempotent request detected: {booking_data.idempotency_key}")
            return existing_booking

        schedule_query = text(
            """
            SELECT s.id, s.screen_id, sh.price, sh.status, v.status
            FROM events.schedules s
            JOIN events.shows sh ON s.show_id = sh.id
            JOIN events.screens sc ON s.screen_id = sc.id
            JOIN events.venues v ON sc.venue_id = v.id
            WHERE s.id = :schedule_id
            """
        )
        schedule_result = await db.execute(schedule_query, {"schedule_id": booking_data.schedule_id})
        schedule_row = schedule_result.fetchone()
        if not schedule_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule not found",
            )

        schedule_id, screen_id, show_price, show_status, venue_status = schedule_row
        if show_status != ShowStatus.ACTIVE.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot book a cancelled show",
            )
        if venue_status != VenueStatus.ACTIVE.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot book in an inactive venue",
            )

        total_amount = float(show_price) * len(booking_data.seat_ids)
        success, _ = await lock_seats(
            db,
            screen_id,
            booking_data.seat_ids,
            lock_duration_minutes=10,
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="One or more seats are not available",
            )

        expires_at = datetime.utcnow() + timedelta(minutes=10)
        new_booking = Booking(
            idempotency_key=booking_data.idempotency_key,
            user_id=user_id,
            schedule_id=schedule_id,
            seat_ids=booking_data.seat_ids,
            total_amount=total_amount,
            status=BookingStatus.PENDING.value,
            correlation_id=correlation_id,
            expires_at=expires_at,
        )
        db.add(new_booking)
        await db.commit()
        await db.refresh(new_booking)
        logger.info(
            f"Booking created: {new_booking.id}",
            extra={"correlation_id": correlation_id, "booking_id": new_booking.id},
        )
        return new_booking
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error creating booking: {str(e)}",
            extra={"correlation_id": correlation_id},
            exc_info=True,
        )
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create booking",
        )


@router.get("/", response_model=List[BookingResponse])
async def get_user_bookings(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get all bookings for a user."""
    try:
        result = await db.execute(
            select(Booking)
            .where(Booking.user_id == user_id)
            .order_by(Booking.created_at.desc())
        )
        bookings = result.scalars().all()
        return bookings
    except Exception as e:
        logger.error(f"Error fetching bookings: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch bookings",
        )


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get booking by ID."""
    try:
        result = await db.execute(
            select(Booking).where(
                and_(
                    Booking.id == booking_id,
                    Booking.user_id == user_id,
                )
            )
        )
        booking = result.scalar_one_or_none()
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found",
            )
        return booking
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching booking: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch booking",
        )


@router.get("/schedule/{schedule_id}/seats")
async def get_schedule_seats(
    schedule_id: int,
    user_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Get seat availability for a schedule."""
    try:
        schedule_query = text(
            "SELECT screen_id FROM events.schedules WHERE id = :schedule_id"
        )
        schedule_result = await db.execute(schedule_query, {"schedule_id": schedule_id})
        schedule_row = schedule_result.fetchone()
        if not schedule_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule not found",
            )
        screen_id = schedule_row[0]

        seats_query = text(
            """
            SELECT id, seat_number, row_number, locked_until
            FROM events.seats
            WHERE screen_id = :screen_id
            ORDER BY id
            """
        )
        seats_result = await db.execute(seats_query, {"screen_id": screen_id})
        seats = seats_result.fetchall()

        booked_query = text(
            """
            SELECT seat_ids
            FROM bookings.bookings
            WHERE schedule_id = :schedule_id
              AND status = :status
            """
        )
        booked_result = await db.execute(
            booked_query,
            {"schedule_id": schedule_id, "status": BookingStatus.CONFIRMED.value},
        )
        booked_ids = set()
        for row in booked_result.fetchall():
            booked_ids.update(row[0] or [])

        now = datetime.now(timezone.utc)
        response = []
        for row in seats:
            locked_until = row.locked_until
            if locked_until and locked_until.tzinfo is None:
                locked_until = locked_until.replace(tzinfo=timezone.utc)
            locked = locked_until is not None and locked_until >= now
            booked = row.id in booked_ids
            response.append(
                {
                    "id": row.id,
                    "seat_number": row.seat_number,
                    "row_number": row.row_number,
                    "is_available": not locked and not booked,
                    "is_locked": locked,
                    "is_booked": booked,
                }
            )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching seats: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch seats",
        )


@router.delete("/{booking_id}")
async def cancel_booking(
    booking_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Cancel a booking and initiate refund processing."""
    try:
        result = await db.execute(
            select(Booking).where(
                and_(
                    Booking.id == booking_id,
                    Booking.user_id == user_id,
                )
            )
        )
        booking = result.scalar_one_or_none()
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found",
            )

        cancelled_count = await _cancel_bookings(
            bookings=[booking],
            db=db,
            reason="User cancelled booking",
            initiated_by="USER",
        )
        if cancelled_count == 0:
            return {"message": "Booking is already cancelled or not refundable"}

        logger.info("Booking cancelled by user: %s", booking_id)
        return {
            "message": "Booking cancelled successfully. Refund initiated.",
            "booking_id": booking_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling booking: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel booking",
        )


@router.post("/internal/cancel-by-show/{show_id}")
async def cancel_bookings_by_show(
    show_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Cancel bookings for all schedules associated with a cancelled show."""
    try:
        result = await db.execute(
            text(
                """
                SELECT b.id
                FROM bookings.bookings b
                JOIN events.schedules s ON s.id = b.schedule_id
                WHERE s.show_id = :show_id
                """
            ),
            {"show_id": show_id},
        )
        booking_ids = [row[0] for row in result.fetchall()]
        if not booking_ids:
            return {"cancelled_bookings": 0}

        bookings_result = await db.execute(
            select(Booking).where(Booking.id.in_(booking_ids))
        )
        bookings = bookings_result.scalars().all()

        cancelled_count = await _cancel_bookings(
            bookings=bookings,
            db=db,
            reason=f"Show {show_id} cancelled by admin",
            initiated_by="ADMIN",
        )
        return {"cancelled_bookings": cancelled_count}
    except Exception as e:
        logger.error("Error cancelling show bookings: %s", str(e), exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel show bookings",
        )


@router.post("/internal/cancel-by-venue/{venue_id}")
async def cancel_bookings_by_venue(
    venue_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Cancel bookings for all schedules under an inactive venue."""
    try:
        result = await db.execute(
            text(
                """
                SELECT b.id
                FROM bookings.bookings b
                JOIN events.schedules s ON s.id = b.schedule_id
                JOIN events.screens sc ON sc.id = s.screen_id
                WHERE sc.venue_id = :venue_id
                """
            ),
            {"venue_id": venue_id},
        )
        booking_ids = [row[0] for row in result.fetchall()]
        if not booking_ids:
            return {"cancelled_bookings": 0}

        bookings_result = await db.execute(
            select(Booking).where(Booking.id.in_(booking_ids))
        )
        bookings = bookings_result.scalars().all()

        cancelled_count = await _cancel_bookings(
            bookings=bookings,
            db=db,
            reason=f"Venue {venue_id} marked inactive by admin",
            initiated_by="ADMIN",
        )
        return {"cancelled_bookings": cancelled_count}
    except Exception as e:
        logger.error("Error cancelling venue bookings: %s", str(e), exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel venue bookings",
        )


@router.patch("/{booking_id}/status")
async def update_booking_status(
    booking_id: int,
    status: str = Body(..., embed=True),
    user_id: int = None,
    db: AsyncSession = Depends(get_db),
):
    """Update booking status (used by payment service)."""
    try:
        result = await db.execute(
            select(Booking).where(
                and_(Booking.id == booking_id, Booking.user_id == user_id),
            )
        )
        booking = result.scalar_one_or_none()
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        booking.status = status
        await db.commit()
        await db.refresh(booking)
        return {"message": "Booking status updated", "status": booking.status}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating booking status: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update booking status")
