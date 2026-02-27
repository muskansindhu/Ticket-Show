"""
Kafka producer for the Event Service.
Publishes events when shows or venues are created, updated, or deleted,
so the Search Service can update Elasticsearch in real time.
"""

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


async def publish_show_changed(event: dict):
    """Publish a show change event to Kafka for ES indexing."""
    if kafka_producer is None:
        logger.warning("Kafka producer not initialized; skipping show change event")
        return

    await kafka_producer.send_message(
        topic="search.show_changed",
        message=event,
        key=str(event["id"]),
    )
    logger.info(
        "Published search.show_changed (action=%s) for show %s",
        event.get("action"),
        event["id"],
    )


async def publish_venue_changed(event: dict):
    """Publish a venue change event to Kafka for ES indexing."""
    if kafka_producer is None:
        logger.warning("Kafka producer not initialized; skipping venue change event")
        return

    await kafka_producer.send_message(
        topic="search.venue_changed",
        message=event,
        key=str(event["id"]),
    )
    logger.info(
        "Published search.venue_changed (action=%s) for venue %s",
        event.get("action"),
        event["id"],
    )
