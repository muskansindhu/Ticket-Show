from datetime import datetime, timedelta
import uuid
from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy import and_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from shared.schemas import BookingCreate, BookingResponse, BookingStatus
from shared.utils import setup_logger
from .database import get_db
from .models import Booking

logger = setup_logger(__name__)
router = APIRouter(prefix="/bookings", tags=["bookings"])


async def lock_seats(
    db: AsyncSession,
    screen_id: int,
    seat_ids: List[int],
    lock_duration_minutes: int = 10,
):
    """Lock seats for a screen using SELECT FOR UPDATE with row-level locking"""
    try:
        lock_until = datetime.utcnow() + timedelta(minutes=lock_duration_minutes)
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


async def release_seats(db: AsyncSession, screen_id: int, seat_ids: List[int]):
    """Release locked seats for a screen"""
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
        await db.commit()
    except Exception as e:
        logger.error(f"Error releasing seats: {str(e)}", exc_info=True)
        await db.rollback()


@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking_data: BookingCreate,
    user_id: int,  # This would come from JWT token in production
    db: AsyncSession = Depends(get_db),
):
    """Create a new booking with seat locking (using schedule_id)"""
    correlation_id = str(uuid.uuid4())
    try:
        # Check for idempotency
        result = await db.execute(
            select(Booking).where(Booking.idempotency_key == booking_data.idempotency_key)
        )
        existing_booking = result.scalar_one_or_none()
        if existing_booking:
            logger.info(f"Idempotent request detected: {booking_data.idempotency_key}")
            return existing_booking
        # Validate schedule
        schedule_query = text(
            """
            SELECT s.id, s.screen_id, sh.price
            FROM events.schedules s
            JOIN events.shows sh ON s.show_id = sh.id
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
        schedule_id, screen_id, show_price = schedule_row
        total_amount = float(show_price) * len(booking_data.seat_ids)
        # Lock seats for the screen
        success, locked_seat_ids = await lock_seats(
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
    user_id: int,  # This would come from JWT token in production
    db: AsyncSession = Depends(get_db),
):
    """Get all bookings for a user"""
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
    user_id: int,  # This would come from JWT token in production
    db: AsyncSession = Depends(get_db),
):
    """Get booking by ID"""
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


@router.delete("/{booking_id}")
async def cancel_booking(
    booking_id: int,
    user_id: int,  # This would come from JWT token in production
    db: AsyncSession = Depends(get_db),
):
    """Cancel a booking and release seats"""
    try:
        result = await db.execute(
            select(Booking).where(
                and_(
                    Booking.id == booking_id,
                    Booking.user_id == user_id,
                    Booking.status == BookingStatus.PENDING.value,
                )
            )
        )
        booking = result.scalar_one_or_none()
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found or cannot be cancelled",
            )
        # Release seats
        # Get screen_id from schedule
        schedule_query = text("SELECT screen_id FROM events.schedules WHERE id = :schedule_id")
        schedule_result = await db.execute(schedule_query, {"schedule_id": booking.schedule_id})
        schedule_row = schedule_result.fetchone()
        if not schedule_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule not found for booking",
            )
        screen_id = schedule_row[0]
        await release_seats(db, screen_id, booking.seat_ids)
        booking.status = BookingStatus.FAILED.value
        await db.commit()
        logger.info(f"Booking cancelled: {booking_id}")
        return {"message": "Booking cancelled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling booking: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel booking",
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
