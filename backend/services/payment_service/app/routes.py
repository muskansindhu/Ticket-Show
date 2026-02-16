import uuid

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.schemas import BookingStatus, PaymentCreate, PaymentResponse, PaymentStatus
from shared.utils import setup_logger
from .database import get_db
from .kafka_handler import publish_booking_successful
from .models import Payment

logger = setup_logger(__name__)
router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def make_payment(
    payment_data: PaymentCreate,
    db: AsyncSession = Depends(get_db),
):
    try:
        # 1. Fetch booking
        async with httpx.AsyncClient() as client:
            booking_resp = await client.get(
                f"http://booking-service:8000/bookings/{payment_data.booking_id}",
                params={"user_id": payment_data.user_id},
                timeout=10.0,
            )

        if booking_resp.status_code != 200:
            raise HTTPException(status_code=404, detail="Booking not found")

        booking = booking_resp.json()

        if float(booking["total_amount"]) != float(payment_data.amount):
            raise HTTPException(status_code=400, detail="Amount mismatch")

        # 2. Create payment
        correlation_id = str(uuid.uuid4())

        payment = Payment(
            idempotency_key=str(uuid.uuid4()),
            booking_id=payment_data.booking_id,
            user_id=payment_data.user_id,
            amount=payment_data.amount,
            status=PaymentStatus.COMPLETED.value,
            payment_method=payment_data.payment_method.value,
            transaction_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
        )

        db.add(payment)
        await db.commit()
        await db.refresh(payment)

        # 3. Update booking status
        async with httpx.AsyncClient() as client:
            await client.patch(
                f"http://booking-service:8000/bookings/{payment_data.booking_id}/status",
                json={"status": BookingStatus.CONFIRMED.value},
                params={"user_id": payment_data.user_id},
                timeout=10.0,
            )

        # 4. Publish Kafka Event
        booking_success_event = {
            "booking_id": payment.booking_id,
            "user_id": payment.user_id,
            "user_email": payment_data.user_email,
            "schedule_id": booking["schedule_id"],
            "seat_ids": booking["seat_ids"],
            "total_amount": float(payment.amount),
            "correlation_id": correlation_id,
            "confirmed_at": payment.created_at.isoformat(),
        }

        await publish_booking_successful(booking_success_event)

        return payment

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Payment failed: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail="Payment failed")


@router.get("/booking/{booking_id}", response_model=PaymentResponse)
async def get_payment_by_booking(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get payment by booking ID"""
    try:
        result = await db.execute(
            select(Payment).where(Payment.booking_id == booking_id)
        )
        payment = result.scalar_one_or_none()

        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found",
            )

        return payment

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching payment: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch payment",
        )


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get payment by ID"""
    try:
        result = await db.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        payment = result.scalar_one_or_none()

        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found",
            )

        return payment

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching payment: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch payment",
        )
