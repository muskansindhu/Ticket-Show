import asyncio
import textwrap
from email.message import EmailMessage

import aiosmtplib

from shared.schemas import (
    BookingFailedEvent,
    BookingSuccessfulEvent,
    RefundCompletedEvent,
    RefundInitiatedEvent,
)
from shared.utils import KafkaConsumerClient, setup_logger
from .config import settings

logger = setup_logger(__name__)


def _format_from_address() -> str:
    if settings.SMTP_FROM_NAME:
        return f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
    return settings.SMTP_FROM_EMAIL


def _resolve_recipient_email(event) -> str | None:
    if getattr(event, "user_email", None):
        return event.user_email
    if settings.DEFAULT_TO_EMAIL:
        return settings.DEFAULT_TO_EMAIL
    if settings.DEFAULT_EMAIL_DOMAIN:
        return f"user_{event.user_id}@{settings.DEFAULT_EMAIL_DOMAIN}"
    return None


async def send_email_notification(to_email: str, subject: str, body: str):
    """Send email notification using SMTP"""
    if not settings.SMTP_HOST:
        raise RuntimeError("SMTP_HOST is not configured")

    use_ssl = settings.SMTP_USE_SSL
    use_tls = settings.SMTP_USE_TLS and not use_ssl

    if settings.SMTP_USE_TLS and settings.SMTP_USE_SSL:
        logger.warning("Both SMTP_USE_TLS and SMTP_USE_SSL set; using SSL only")

    message = EmailMessage()
    message["From"] = _format_from_address()
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    await aiosmtplib.send(
        message,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER or None,
        password=settings.SMTP_PASSWORD or None,
        start_tls=use_tls,
        use_tls=use_ssl,
        timeout=settings.SMTP_TIMEOUT,
    )

    logger.info("Email sent to %s: %s", to_email, subject)



async def handle_booking_successful(message: dict):
    """Handle booking.successful event"""
    try:
        event = BookingSuccessfulEvent(**message)
        
        logger.info(
            f"Processing booking successful event for booking {event.booking_id}",
            extra={"correlation_id": event.correlation_id},
        )

        to_email = _resolve_recipient_email(event)
        if not to_email:
            raise ValueError(
                "No recipient email available. Provide user_email in the event or set "
                "DEFAULT_TO_EMAIL/DEFAULT_EMAIL_DOMAIN."
            )
        
        # Send confirmation notification
        subject = "Your Ticket Show booking is confirmed"
        body = textwrap.dedent(
            f"""
            Hi there,

            Awesome news — your booking went through and you’re all set. We can’t wait to see you at the show.
            For your records, your booking ID is {event.booking_id} and the schedule ID is {event.schedule_id}.
            You grabbed {len(event.seat_ids)} seat(s) and the total comes to ₹{event.total_amount}.

            If anything looks off or you have a quick question, just hit reply and we’ll jump in.

            Thanks again for choosing TicketShow,
            The TicketShow Team
            """
        ).strip()

        await send_email_notification(
            to_email=to_email,
            subject=subject,
            body=body,
        )

        logger.info(
            f"Confirmation notification sent for booking {event.booking_id}",
            extra={"correlation_id": event.correlation_id},
        )

    except Exception as e:
        logger.error(
            f"Error handling booking confirmed event: {str(e)}",
            exc_info=True,
        )
        raise


async def handle_booking_failed(message: dict):
    """Handle booking.failed event"""
    try:
        event = BookingFailedEvent(**message)
        
        logger.info(
            f"Processing booking failed event for booking {event.booking_id}",
            extra={"correlation_id": event.correlation_id},
        )

        to_email = _resolve_recipient_email(event)
        if not to_email:
            raise ValueError(
                "No recipient email available. Provide user_email in the event or set "
                "DEFAULT_TO_EMAIL/DEFAULT_EMAIL_DOMAIN."
            )

        # Send failure notification
        subject = "We couldn’t complete your Ticket Show booking"
        body = textwrap.dedent(
            f"""
            Hi there,

            Sorry, we were not able to process your booking this time.
            For reference, your booking ID is {event.booking_id}. The reason we saw was: {event.reason}.

            If you want to try again, go for it. And if it keeps happening, just reply here and we’ll sort it out with you.

            Thanks for your patience,
            The TicketShow Team
            """
        ).strip()

        await send_email_notification(
            to_email=to_email,
            subject=subject,
            body=body,
        )

        logger.info(
            f"Failure notification sent for booking {event.booking_id}",
            extra={"correlation_id": event.correlation_id},
        )

    except Exception as e:
        logger.error(
            f"Error handling booking failed event: {str(e)}",
            exc_info=True,
        )
        raise


async def handle_refund_initiated(message: dict):
    """Handle refund initiated event."""
    try:
        event = RefundInitiatedEvent(**message)
        logger.info(
            "Processing refund initiated event for booking %s",
            event.booking_id,
            extra={"correlation_id": event.correlation_id},
        )

        to_email = _resolve_recipient_email(event)
        if not to_email:
            raise ValueError(
                "No recipient email available. Provide user_email in the event or set "
                "DEFAULT_TO_EMAIL/DEFAULT_EMAIL_DOMAIN."
            )

        subject = "Refund initiated for your Ticket Show booking"
        body = textwrap.dedent(
            f"""
            Hi there,

            Your booking {event.booking_id} has been cancelled and we have initiated a refund of ₹{event.amount}.
            Reason: {event.reason}

            If this payment was made via DODO, the refund will be sent to your original payment method (not your Ticket Show wallet).
            We will notify you again once the refund is completed.

            Thanks,
            The TicketShow Team
            """
        ).strip()
        await send_email_notification(to_email=to_email, subject=subject, body=body)
    except Exception as e:
        logger.error(
            f"Error handling refund initiated event: {str(e)}",
            exc_info=True,
        )
        raise


async def handle_refund_completed(message: dict):
    """Handle refund completed event."""
    try:
        event = RefundCompletedEvent(**message)
        logger.info(
            "Processing refund completed event for booking %s",
            event.booking_id,
            extra={"correlation_id": event.correlation_id},
        )

        to_email = _resolve_recipient_email(event)
        if not to_email:
            raise ValueError(
                "No recipient email available. Provide user_email in the event or set "
                "DEFAULT_TO_EMAIL/DEFAULT_EMAIL_DOMAIN."
            )

        refund_ref = f" (Refund ID: {event.refund_id})" if event.refund_id else ""
        payment_method = str(event.payment_method or "").upper()
        if payment_method == "DODO":
            destination_text = "to your original payment method"
        elif payment_method:
            destination_text = "to your Ticket Show wallet"
        else:
            destination_text = "to your original payment method"
        method_text = f" through {payment_method}" if payment_method else ""

        subject = "Refund completed for your Ticket Show booking"
        body = textwrap.dedent(
            f"""
            Hi there,

            Your refund of ₹s{event.amount} for booking {event.booking_id} has been completed {destination_text}{method_text}{refund_ref}.

            If you have any issues, reply to this email and we will help you out.

            Thanks,
            The TicketShow Team
            """
        ).strip()
        await send_email_notification(to_email=to_email, subject=subject, body=body)
    except Exception as e:
        logger.error(
            f"Error handling refund completed event: {str(e)}",
            exc_info=True,
        )
        raise


async def start_kafka_consumers():
    """Start Kafka consumers for notification events"""
    # Consumer for booking.successful
    successful_consumer = KafkaConsumerClient(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="notification-service-successful-group",
        topics=["booking.successful"],
        max_retries=3,
        retry_delay=1,
    )

    # Consumer for booking.failed
    failed_consumer = KafkaConsumerClient(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="notification-service-failed-group",
        topics=["booking.failed"],
        max_retries=3,
        retry_delay=1,
    )
    refund_consumer = KafkaConsumerClient(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="notification-service-refund-group",
        topics=["notification.refund_initiated"],
        max_retries=3,
        retry_delay=1,
    )
    refund_completed_consumer = KafkaConsumerClient(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="notification-service-refund-completed-group",
        topics=["notification.refund_completed"],
        max_retries=3,
        retry_delay=1,
    )

    await successful_consumer.start()
    await failed_consumer.start()
    await refund_consumer.start()
    await refund_completed_consumer.start()

    logger.info(
        "Kafka consumers started for booking.successful, booking.failed, notification.refund_initiated, and notification.refund_completed"
    )

    # Start consuming in parallel
    await asyncio.gather(
        successful_consumer.consume(handle_booking_successful),
        failed_consumer.consume(handle_booking_failed),
        refund_consumer.consume(handle_refund_initiated),
        refund_completed_consumer.consume(handle_refund_completed),
    )


def run_consumers():
    """Run the Kafka consumers in the background"""
    asyncio.create_task(start_kafka_consumers())
