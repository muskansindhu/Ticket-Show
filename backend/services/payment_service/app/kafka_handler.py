import asyncio
from datetime import datetime

import httpx
from sqlalchemy import select

from shared.schemas import (
    BookingFailedEvent,
    PaymentMethod,
    PaymentStatus,
    RefundCompletedEvent,
    RefundInitiatedEvent,
)
from shared.utils import KafkaConsumerClient, KafkaProducerClient, setup_logger
from .config import settings
from .database import AsyncSessionLocal
from .models import Payment
from .utils import get_dodo_client, to_dict

logger = setup_logger(__name__)

kafka_producer: KafkaProducerClient | None = None


async def init_kafka_producer():
    global kafka_producer
    kafka_producer = KafkaProducerClient(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
    )
    await kafka_producer.start()
    logger.info("Kafka producer initialized")


async def close_kafka_producer():
    global kafka_producer
    if kafka_producer:
        await kafka_producer.stop()
        logger.info("Kafka producer closed")


async def publish_booking_successful(event: dict):
    if kafka_producer is None:
        raise RuntimeError("Kafka producer not initialized")

    await kafka_producer.send_message(
        topic="booking.successful",
        message=event,
        key=str(event["booking_id"]),
        correlation_id=event["correlation_id"],
    )

    logger.info(f"Published booking.successful for {event['booking_id']}")


async def publish_booking_failed(event: dict):
    if kafka_producer is None:
        raise RuntimeError("Kafka producer not initialized")

    BookingFailedEvent(**event)
    await kafka_producer.send_message(
        topic="booking.failed",
        message=event,
        key=str(event["booking_id"]),
        correlation_id=event["correlation_id"],
    )

    logger.info(f"Published booking.failed for {event['booking_id']}")


async def publish_refund_completed_notification(event: dict):
    if kafka_producer is None:
        raise RuntimeError("Kafka producer not initialized")

    RefundCompletedEvent(**event)
    await kafka_producer.send_message(
        topic="notification.refund_completed",
        message=event,
        key=str(event["booking_id"]),
        correlation_id=event["correlation_id"],
    )
    logger.info("Published notification.refund_completed for %s", event["booking_id"])


async def publish_refund_initiated(event: dict):
    if kafka_producer is None:
        raise RuntimeError("Kafka producer not initialized")

    RefundInitiatedEvent(**event)
    await kafka_producer.send_message(
        topic="payment.refund_initiated",
        message=event,
        key=str(event["booking_id"]),
        correlation_id=event["correlation_id"],
    )
    logger.info("Published payment.refund_initiated for %s", event["booking_id"])


async def handle_refund_initiated(message: dict):
    event = RefundInitiatedEvent(**message)

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Payment)
            .where(Payment.booking_id == event.booking_id)
            .order_by(Payment.created_at.desc())
        )
        payment = result.scalars().first()

        if not payment:
            logger.warning("No payment found for booking %s", event.booking_id)
            return

        if payment.status == PaymentStatus.REFUNDED.value:
            logger.info("Refund already processed for booking %s", event.booking_id)
            return

        if payment.status != PaymentStatus.COMPLETED.value:
            logger.info(
                "Skipping refund for booking %s due to status %s",
                event.booking_id,
                payment.status,
            )
            return

        payment_method = (payment.payment_method or "").upper()
        refund_id = None

        if payment_method == PaymentMethod.DODO.value:
            if not payment.transaction_id:
                raise RuntimeError(
                    f"Missing Dodo payment transaction id for booking {event.booking_id}"
                )
            dodo_client = get_dodo_client(
                api_key=settings.DODO_PAYMENTS_API_KEY,
                environment=settings.DODO_PAYMENTS_ENVIRONMENT,
            )
            refund_result = await dodo_client.refunds.create(
                payment_id=str(payment.transaction_id),
                reason=event.reason,
                metadata={
                    "booking_id": str(event.booking_id),
                    "correlation_id": event.correlation_id,
                    "user_email": event.user_email or "",
                },
            )
            refund_data = to_dict(refund_result)
            refund_status = str(
                refund_data.get("status")
                or getattr(refund_result, "status", "")
                or ""
            ).lower()
            refund_id = (
                refund_data.get("refund_id")
                or refund_data.get("id")
                or getattr(refund_result, "refund_id", None)
                or getattr(refund_result, "id", None)
            )

            if refund_status in {"pending", "review"}:
                payment.status = PaymentStatus.REFUND_INITIATED.value
                await db.commit()
                logger.info(
                    "Dodo refund initiated for booking %s with status %s",
                    event.booking_id,
                    refund_status,
                )
                return
            if refund_status == "failed":
                raise RuntimeError(f"Dodo refund failed for booking {event.booking_id}")
            if refund_status != "succeeded":
                raise RuntimeError(
                    f"Unexpected Dodo refund status '{refund_status}' for booking {event.booking_id}"
                )
        else:
            async with httpx.AsyncClient() as client:
                wallet_resp = await client.post(
                    f"{settings.AUTH_SERVICE_URL}/auth/wallet/internal/credit",
                    json={
                        "user_id": event.user_id,
                        "amount": float(event.amount),
                        "reference_id": f"refund:{event.booking_id}",
                        "description": event.reason,
                    },
                    timeout=10.0,
                )
                if wallet_resp.status_code >= 400:
                    raise RuntimeError("Failed to credit user wallet")

        payment.status = PaymentStatus.REFUNDED.value
        await db.commit()

        refund_completed_event = {
            "booking_id": event.booking_id,
            "user_id": event.user_id,
            "amount": float(event.amount),
            "correlation_id": event.correlation_id,
            "refunded_at": datetime.utcnow().isoformat(),
            "user_email": event.user_email,
            "refund_id": str(refund_id) if refund_id else None,
            "payment_method": payment.payment_method,
        }
        await publish_refund_completed_notification(refund_completed_event)

        logger.info(
            "Refund processed for booking %s",
            event.booking_id,
        )


async def start_kafka_consumers():
    refund_consumer = KafkaConsumerClient(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="payment-service-refund-group",
        topics=["payment.refund_initiated"],
        max_retries=3,
        retry_delay=1,
    )

    await refund_consumer.start()
    logger.info("Kafka consumer started for payment.refund_initiated")
    await refund_consumer.consume(handle_refund_initiated)


def run_consumers():
    asyncio.create_task(start_kafka_consumers())
