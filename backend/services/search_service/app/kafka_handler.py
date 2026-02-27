"""
Kafka consumer for the Search Service.
Consumes show/venue change events and updates Elasticsearch in real time.
"""

import asyncio

from shared.utils import KafkaConsumerClient, setup_logger
from .config import settings
from .elastic import (
    SHOWS_INDEX,
    VENUES_INDEX,
    delete_document,
    index_document,
)

logger = setup_logger(__name__)


async def handle_show_changed(message: dict):
    """Handle a show change event from the Event Service."""
    action = message.get("action", "")
    show_id = message.get("id")

    if not show_id:
        logger.warning("Received show_changed event without id, skipping")
        return

    status = message.get("status", "")

    if action == "deleted" or status == "CANCELLED":
        await delete_document(SHOWS_INDEX, show_id)
        logger.info("Show %s removed from ES (action=%s)", show_id, action)
    else:
        body = {
            k: v
            for k, v in message.items()
            if k not in ("id", "action", "correlation_id", "timestamp", "retry_count")
        }
        await index_document(SHOWS_INDEX, show_id, body)
        logger.info("Show %s indexed in ES (action=%s)", show_id, action)


async def handle_venue_changed(message: dict):
    """Handle a venue change event from the Event Service."""
    action = message.get("action", "")
    venue_id = message.get("id")

    if not venue_id:
        logger.warning("Received venue_changed event without id, skipping")
        return

    status = message.get("status", "")

    if action == "deleted" or status == "INACTIVE":
        await delete_document(VENUES_INDEX, venue_id)
        logger.info("Venue %s removed from ES (action=%s)", venue_id, action)
    else:
        body = {
            k: v
            for k, v in message.items()
            if k not in ("id", "action", "correlation_id", "timestamp", "retry_count")
        }
        await index_document(VENUES_INDEX, venue_id, body)
        logger.info("Venue %s indexed in ES (action=%s)", venue_id, action)


async def start_kafka_consumers():
    """Start Kafka consumers for show and venue change events."""
    show_consumer = KafkaConsumerClient(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="search-service-show-group",
        topics=["search.show_changed"],
        max_retries=3,
        retry_delay=1,
    )

    venue_consumer = KafkaConsumerClient(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="search-service-venue-group",
        topics=["search.venue_changed"],
        max_retries=3,
        retry_delay=1,
    )

    await show_consumer.start()
    await venue_consumer.start()

    logger.info(
        "Kafka consumers started for search.show_changed and search.venue_changed"
    )

    await asyncio.gather(
        show_consumer.consume(handle_show_changed),
        venue_consumer.consume(handle_venue_changed),
    )


def run_consumers():
    """Run the Kafka consumers in the background."""
    asyncio.create_task(start_kafka_consumers())
