import asyncio

import httpx
from sqlalchemy import select

from shared.schemas import PaymentStatus, RefundInitiatedEvent
from shared.utils import KafkaConsumerClient, KafkaProducerClient, setup_logger
from .config import settings
from .database import AsyncSessionLocal
from .models import Payment

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

        logger.info(
            "Refund processed for booking %s and credited to wallet",
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
