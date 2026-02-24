from shared.utils import KafkaProducerClient, setup_logger
from .config import settings

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


async def publish_refund_initiated(event: dict):
    if kafka_producer is None:
        raise RuntimeError("Kafka producer not initialized")

    await kafka_producer.send_message(
        topic="payment.refund_initiated",
        message=event,
        key=str(event["booking_id"]),
        correlation_id=event["correlation_id"],
    )
    logger.info("Published payment.refund_initiated for booking %s", event["booking_id"])


async def publish_refund_notification(event: dict):
    if kafka_producer is None:
        raise RuntimeError("Kafka producer not initialized")

    await kafka_producer.send_message(
        topic="notification.refund_initiated",
        message=event,
        key=str(event["booking_id"]),
        correlation_id=event["correlation_id"],
    )
    logger.info(
        "Published notification.refund_initiated for booking %s",
        event["booking_id"],
    )
