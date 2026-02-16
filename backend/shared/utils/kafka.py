import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Callable, Optional

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.errors import KafkaError

logger = logging.getLogger(__name__)


class KafkaProducerClient:
    """Kafka producer client with retry mechanism"""

    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.producer: Optional[AIOKafkaProducer] = None

    async def start(self):
        """Start the Kafka producer"""
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
        )
        await self.producer.start()
        logger.info("Kafka producer started")

    async def stop(self):
        """Stop the Kafka producer"""
        if self.producer:
            await self.producer.stop()
            logger.info("Kafka producer stopped")

    async def send_message(
        self,
        topic: str,
        message: dict,
        key: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ):
        """Send a message to Kafka topic"""
        try:
            # Add metadata
            message_with_metadata = {
                **message,
                "correlation_id": correlation_id or message.get("correlation_id"),
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            result = await self.producer.send_and_wait(
                topic=topic,
                value=message_with_metadata,
                key=key,
            )

            logger.info(
                f"Message sent to topic {topic}",
                extra={
                    "topic": topic,
                    "partition": result.partition,
                    "offset": result.offset,
                    "correlation_id": correlation_id,
                },
            )
            return result
        except KafkaError as e:
            logger.error(
                f"Failed to send message to {topic}: {str(e)}",
                extra={"topic": topic, "correlation_id": correlation_id},
            )
            raise


class KafkaConsumerClient:
    """Kafka consumer client with retry and DLT support"""

    def __init__(
        self,
        bootstrap_servers: str,
        group_id: str,
        topics: list[str],
        max_retries: int = 3,
        retry_delay: int = 1,
    ):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.topics = topics
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.producer: Optional[KafkaProducerClient] = None

    async def start(self):
        """Start the Kafka consumer"""
        self.consumer = AIOKafkaConsumer(
            *self.topics,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            key_deserializer=lambda k: k.decode("utf-8") if k else None,
            auto_offset_reset="earliest",
            enable_auto_commit=False,
        )
        await self.consumer.start()

        # Start producer for DLT
        self.producer = KafkaProducerClient(self.bootstrap_servers)
        await self.producer.start()

        logger.info(f"Kafka consumer started for topics: {self.topics}")

    async def stop(self):
        """Stop the Kafka consumer"""
        if self.consumer:
            await self.consumer.stop()
        if self.producer:
            await self.producer.stop()
        logger.info("Kafka consumer stopped")

    async def consume(self, handler: Callable[[dict], Any]):
        """Consume messages with retry and DLT support"""
        async for message in self.consumer:
            correlation_id = message.value.get("correlation_id")
            retry_count = message.value.get("retry_count", 0)

            try:
                logger.info(
                    f"Processing message from {message.topic}",
                    extra={
                        "topic": message.topic,
                        "partition": message.partition,
                        "offset": message.offset,
                        "correlation_id": correlation_id,
                    }
                )

                # Process the message
                await handler(message.value)

                # Commit offset on success
                await self.consumer.commit()

                logger.info(
                    f"Successfully processed message from {message.topic}",
                    extra={"correlation_id": correlation_id},
                )

            except Exception as e:
                logger.error(
                    f"Error processing message: {str(e)}",
                    extra={
                        "topic": message.topic,
                        "correlation_id": correlation_id,
                        "retry_count": retry_count,
                    },
                    exc_info=True
                )

                # Retry logic with exponential backoff
                if retry_count < self.max_retries:
                    await self._retry_message(message, retry_count + 1)
                else:
                    await self._send_to_dlt(message, str(e))

                # Commit offset to move forward
                await self.consumer.commit()
    
    async def _retry_message(self, message, retry_count: int):
        """Retry failed message with exponential backoff"""
        delay = self.retry_delay * (2 ** (retry_count - 1))
        await asyncio.sleep(delay)

        retry_message = {
            **message.value,
            "retry_count": retry_count,
        }

        await self.producer.send_message(
            topic=message.topic,
            message=retry_message,
            key=message.key,
            correlation_id=message.value.get("correlation_id")
        )

        logger.info(
            f"Message retried (attempt {retry_count})",
            extra={
                "topic": message.topic,
                "retry_count": retry_count,
                "correlation_id": message.value.get("correlation_id"),
            }
        )
    
    async def _send_to_dlt(self, message, error: str):
        """Send failed message to Dead Letter Topic"""
        dlt_topic = "booking.dlt"

        dlt_message = {
            **message.value,
            "original_topic": message.topic,
            "error": error,
            "failed_at": datetime.utcnow().isoformat(),
        }

        await self.producer.send_message(
            topic=dlt_topic,
            message=dlt_message,
            key=message.key,
            correlation_id=message.value.get("correlation_id")
        )

        logger.error(
            f"Message sent to DLT after {self.max_retries} retries",
            extra={
                "original_topic": message.topic,
                "dlt_topic": dlt_topic,
                "correlation_id": message.value.get("correlation_id"),
            }
        )
