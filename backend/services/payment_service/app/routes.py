import json
import uuid
from datetime import datetime

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.schemas import (
    BookingStatus,
    PaymentCreate,
    PaymentMethod,
    PaymentResponse,
    PaymentStatus,
)
from shared.utils import setup_logger
from .config import settings
from .database import get_db
from .kafka_handler import (
    publish_booking_failed,
    publish_refund_initiated,
    publish_booking_successful,
    publish_refund_completed_notification,
)
from .models import Payment
from .utils import (
    extract_checkout_session_fields,
    get_dodo_client,
    is_refund_event,
    to_dict,
    to_minor_units,
    to_positive_int,
)

logger = setup_logger(__name__)
router = APIRouter(prefix="/payments", tags=["payments"])


def _get_dodo_client():
    try:
        return get_dodo_client(
            api_key=settings.DODO_PAYMENTS_API_KEY,
            environment=settings.DODO_PAYMENTS_ENVIRONMENT,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


async def _fetch_booking(booking_id: int, user_id: int) -> dict:
    async with httpx.AsyncClient() as client:
        booking_resp = await client.get(
            f"http://booking-service:8000/bookings/{booking_id}",
            params={"user_id": user_id},
            timeout=10.0,
        )
    if booking_resp.status_code != 200:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking_resp.json()


async def _update_booking_status(
    booking_id: int,
    user_id: int,
    booking_status: BookingStatus,
) -> None:
    async with httpx.AsyncClient() as client:
        resp = await client.patch(
            f"http://booking-service:8000/bookings/{booking_id}/status",
            json={"status": booking_status.value},
            params={"user_id": user_id},
            timeout=10.0,
        )
    if resp.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to sync booking status",
        )


def _to_payment_response(payment: Payment, checkout_url: str | None = None) -> PaymentResponse:
    response = PaymentResponse.model_validate(payment, from_attributes=True)
    if checkout_url:
        response = response.model_copy(update={"checkout_url": checkout_url})
    return response


async def _publish_booking_success_event(
    payment: Payment,
    booking: dict,
    user_email: str | None,
) -> None:
    booking_success_event = {
        "booking_id": payment.booking_id,
        "user_id": payment.user_id,
        "user_email": user_email,
        "schedule_id": booking["schedule_id"],
        "seat_ids": booking["seat_ids"],
        "total_amount": float(payment.amount),
        "correlation_id": payment.correlation_id,
        "confirmed_at": payment.updated_at.isoformat(),
    }
    await publish_booking_successful(booking_success_event)


async def _publish_booking_failed_event(
    payment: Payment,
    reason: str,
    user_email: str | None,
) -> None:
    booking_failed_event = {
        "booking_id": payment.booking_id,
        "user_id": payment.user_id,
        "user_email": user_email,
        "reason": reason,
        "correlation_id": payment.correlation_id,
        "failed_at": payment.updated_at.isoformat(),
    }
    await publish_booking_failed(booking_failed_event)


def _verify_webhook_signature(
    raw_body: bytes,
    signature: str,
    webhook_id: str | None = None,
    webhook_timestamp: str | None = None,
) -> None:
    if not settings.DODO_PAYMENTS_WEBHOOK_KEY:
        raise HTTPException(status_code=500, detail="Dodo webhook key is not configured")

    provided_signature = (signature or "").strip()
    if not provided_signature:
        raise HTTPException(status_code=400, detail="Missing webhook signature")
    headers = {"webhook-signature": provided_signature}
    if webhook_id:
        headers["webhook-id"] = webhook_id.strip()
    if webhook_timestamp:
        headers["webhook-timestamp"] = webhook_timestamp.strip()

    payload = raw_body.decode("utf-8")
    try:
        verifier = _get_dodo_client()
        verifier.webhooks.unwrap(
            payload,
            headers=headers,
            key=settings.DODO_PAYMENTS_WEBHOOK_KEY,
        )
    except Exception as exc:
        logger.warning("Webhook signature validation failed: %s", str(exc))
        raise HTTPException(status_code=400, detail="Invalid webhook signature") from exc


async def _create_checkout_session(
    payment_data: PaymentCreate,
    booking: dict,
    correlation_id: str,
) -> tuple[str, str]:
    if not settings.DODO_PAYMENTS_PRODUCT_ID:
        raise HTTPException(status_code=500, detail="Dodo product id is not configured")

    client = _get_dodo_client()
    seat_count = max(len(booking.get("seat_ids") or []), 1)
    try:
        amount_in_minor_units = to_minor_units(payment_data.amount)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    try:
        product = await client.products.retrieve(settings.DODO_PAYMENTS_PRODUCT_ID)
    except Exception as exc:
        logger.error("Failed to retrieve Dodo product details: %s", str(exc), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to validate Dodo product configuration",
        ) from exc

    product_payload = to_dict(product)
    price_payload = product_payload.get("price")
    pay_what_you_want_enabled = False
    if isinstance(price_payload, dict):
        pay_what_you_want_enabled = bool(price_payload.get("pay_what_you_want"))
    if not pay_what_you_want_enabled:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Dodo product must enable pay_what_you_want to override checkout "
                "amount with booking total"
            ),
        )

    payload = {
        "product_cart": [
            {
                "product_id": settings.DODO_PAYMENTS_PRODUCT_ID,
                "quantity": 1,
                "amount": amount_in_minor_units,
            }
        ],
        "return_url": settings.DODO_PAYMENTS_RETURN_URL,
        "metadata": {
            "booking_id": str(payment_data.booking_id),
            "user_id": str(payment_data.user_id),
            "correlation_id": correlation_id,
            "user_email": payment_data.user_email or "",
            "seat_count": str(seat_count),
            "booking_amount": str(payment_data.amount),
        },
    }
    if payment_data.user_email:
        payload["customer"] = {"email": payment_data.user_email}

    try:
        session = await client.checkout_sessions.create(**payload)
    except Exception as exc:
        logger.error("Failed to create Dodo checkout session: %s", str(exc), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to create Dodo checkout session",
        ) from exc

    try:
        return extract_checkout_session_fields(session)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def make_payment(
    payment_data: PaymentCreate,
    db: AsyncSession = Depends(get_db),
):
    try:
        if payment_data.payment_method != PaymentMethod.DODO:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only DODO payment method is supported",
            )
        booking = await _fetch_booking(payment_data.booking_id, payment_data.user_id)
        if float(booking["total_amount"]) != float(payment_data.amount):
            raise HTTPException(status_code=400, detail="Amount mismatch")

        correlation_id = str(uuid.uuid4())
        transaction_id, checkout_url = await _create_checkout_session(
            payment_data=payment_data,
            booking=booking,
            correlation_id=correlation_id,
        )

        payment = Payment(
            idempotency_key=str(uuid.uuid4()),
            booking_id=payment_data.booking_id,
            user_id=payment_data.user_id,
            amount=payment_data.amount,
            status=PaymentStatus.PENDING.value,
            payment_method=payment_data.payment_method.value,
            transaction_id=transaction_id,
            correlation_id=correlation_id,
        )

        db.add(payment)
        await db.commit()
        await db.refresh(payment)
        return _to_payment_response(payment, checkout_url=checkout_url)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Payment failed: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail="Payment failed")


@router.post("/webhook")
async def dodo_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    raw_body = await request.body()
    signature = request.headers.get("webhook-signature") or request.headers.get("x-webhook-signature")
    webhook_id = request.headers.get("webhook-id")
    webhook_timestamp = request.headers.get("webhook-timestamp")
    _verify_webhook_signature(raw_body, signature or "", webhook_id, webhook_timestamp)

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid webhook payload") from exc

    event_type = str(payload.get("type", "")).lower()
    raw_data = payload.get("data") or {}
    event_data = raw_data.get("object") if isinstance(raw_data, dict) and raw_data.get("object") else raw_data
    metadata = (event_data.get("metadata") if isinstance(event_data, dict) else None) or {}
    if not isinstance(metadata, dict):
        metadata = {}

    booking_id = to_positive_int(
        metadata.get("booking_id")
        or (event_data.get("booking_id") if isinstance(event_data, dict) else None)
        or (raw_data.get("booking_id") if isinstance(raw_data, dict) else None)
    )

    payment = None
    if booking_id:
        result = await db.execute(
            select(Payment)
            .where(Payment.booking_id == booking_id)
            .order_by(Payment.created_at.desc())
            .limit(1)
        )
        payment = result.scalar_one_or_none()

    if payment is None:
        references: list[str] = []
        if isinstance(event_data, dict):
            for key in ("checkout_session_id", "payment_id", "id"):
                value = event_data.get(key)
                if value:
                    references.append(str(value))
        if isinstance(raw_data, dict):
            for key in ("checkout_session_id", "payment_id", "id"):
                value = raw_data.get(key)
                if value:
                    references.append(str(value))

        for reference in references:
            result = await db.execute(
                select(Payment)
                .where(Payment.transaction_id == reference)
                .order_by(Payment.created_at.desc())
                .limit(1)
            )
            payment = result.scalar_one_or_none()
            if payment:
                break

    if not payment:
        logger.warning("Webhook ignored: payment not found for event")
        return {"status": "ignored", "reason": "payment_not_found_for_event"}

    event_data_dict = event_data if isinstance(event_data, dict) else {}
    user_email = metadata.get("user_email") or None

    if is_refund_event(event_type):
        refund_id = event_data_dict.get("refund_id") or event_data_dict.get("id")

        if "pending" in event_type or "review" in event_type:
            if payment.status != PaymentStatus.REFUND_INITIATED.value:
                payment.status = PaymentStatus.REFUND_INITIATED.value
                await db.commit()
                await db.refresh(payment)
            await _update_booking_status(payment.booking_id, payment.user_id, BookingStatus.CANCELLED)
            return {"status": "processed", "result": "refund_initiated"}

        if "succeeded" in event_type:
            already_refunded = payment.status == PaymentStatus.REFUNDED.value
            if not already_refunded:
                payment.status = PaymentStatus.REFUNDED.value
                await db.commit()
                await db.refresh(payment)

            await _update_booking_status(payment.booking_id, payment.user_id, BookingStatus.CANCELLED)

            if not already_refunded:
                refund_completed_event = {
                    "booking_id": payment.booking_id,
                    "user_id": payment.user_id,
                    "amount": float(payment.amount),
                    "correlation_id": payment.correlation_id,
                    "refunded_at": payment.updated_at.isoformat(),
                    "user_email": user_email,
                    "refund_id": str(refund_id) if refund_id else None,
                    "payment_method": payment.payment_method,
                }
                await publish_refund_completed_notification(refund_completed_event)
            return {"status": "processed", "result": "refund_completed"}

        if "failed" in event_type or "cancelled" in event_type:
            if payment.status != PaymentStatus.COMPLETED.value:
                payment.status = PaymentStatus.COMPLETED.value
                await db.commit()
                await db.refresh(payment)
            await _update_booking_status(payment.booking_id, payment.user_id, BookingStatus.CANCELLED)
            return {"status": "processed", "result": "refund_failed"}

        return {"status": "ignored", "reason": "refund_event_not_handled"}

    external_payment_id = event_data_dict.get("payment_id") or event_data_dict.get("id")
    if external_payment_id:
        payment.transaction_id = str(external_payment_id)

    if "succeeded" in event_type:
        booking = await _fetch_booking(payment.booking_id, payment.user_id)
        if booking.get("status") == BookingStatus.CANCELLED.value:
            if payment.status == PaymentStatus.PENDING.value:
                payment.status = PaymentStatus.COMPLETED.value
                await db.commit()
                await db.refresh(payment)

            if payment.status not in {
                PaymentStatus.REFUND_INITIATED.value,
                PaymentStatus.REFUNDED.value,
            }:
                refund_event = {
                    "booking_id": payment.booking_id,
                    "user_id": payment.user_id,
                    "amount": float(payment.amount),
                    "correlation_id": payment.correlation_id,
                    "reason": "Booking cancelled before payment confirmation",
                    "initiated_by": "SYSTEM",
                    "initiated_at": datetime.utcnow().isoformat(),
                    "user_email": user_email,
                }
                await publish_refund_initiated(refund_event)

            return {
                "status": "processed",
                "result": "payment_completed_for_cancelled_booking",
            }

        already_completed = payment.status == PaymentStatus.COMPLETED.value
        if not already_completed:
            payment.status = PaymentStatus.COMPLETED.value
            await db.commit()
            await db.refresh(payment)
        await _update_booking_status(payment.booking_id, payment.user_id, BookingStatus.CONFIRMED)
        if not already_completed:
            await _publish_booking_success_event(payment, booking, user_email)
        return {"status": "processed", "result": "completed"}

    if "failed" in event_type or "cancelled" in event_type:
        already_failed = payment.status == PaymentStatus.FAILED.value
        if payment.status != PaymentStatus.FAILED.value:
            payment.status = PaymentStatus.FAILED.value
            await db.commit()
            await db.refresh(payment)
        await _update_booking_status(payment.booking_id, payment.user_id, BookingStatus.FAILED)
        if not already_failed:
            default_reason = (
                "Payment was cancelled"
                if "cancelled" in event_type
                else "Payment could not be completed"
            )
            reason = str(event_data_dict.get("error_message") or default_reason)
            await _publish_booking_failed_event(payment, reason, user_email)
        return {"status": "processed", "result": "failed"}

    return {"status": "ignored", "reason": "event_not_handled"}


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
