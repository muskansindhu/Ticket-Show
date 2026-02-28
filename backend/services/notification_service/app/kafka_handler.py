import asyncio
import textwrap
from email.message import EmailMessage
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib
import httpx

from shared.schemas import (
    BookingFailedEvent,
    BookingSuccessfulEvent,
    RefundCompletedEvent,
    RefundInitiatedEvent,
)
from shared.utils import KafkaConsumerClient, setup_logger
from .config import settings
from .ticket_pdf import generate_ticket_pdf

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


async def send_email_notification(
    to_email: str,
    subject: str,
    body: str,
    attachments: list[tuple[str, bytes, str]] | None = None,
):
    """Send email notification using SMTP.

    attachments: optional list of (filename, data_bytes, mime_type) tuples.
    """
    if not settings.SMTP_HOST:
        raise RuntimeError("SMTP_HOST is not configured")

    use_ssl = settings.SMTP_USE_SSL
    use_tls = settings.SMTP_USE_TLS and not use_ssl

    if settings.SMTP_USE_TLS and settings.SMTP_USE_SSL:
        logger.warning("Both SMTP_USE_TLS and SMTP_USE_SSL set; using SSL only")

    from_addr = _format_from_address()

    if attachments:
        msg = MIMEMultipart("mixed")
        msg["From"] = from_addr
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        for filename, data, mime_type in attachments:
            part = MIMEApplication(data, Name=filename)
            part["Content-Disposition"] = f'attachment; filename="{filename}"'
            msg.attach(part)
    else:
        msg = EmailMessage()
        msg["From"] = from_addr
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.set_content(body)

    await aiosmtplib.send(
        msg,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER or None,
        password=settings.SMTP_PASSWORD or None,
        start_tls=use_tls,
        use_tls=use_ssl,
        timeout=settings.SMTP_TIMEOUT,
    )

    logger.info("Email sent to %s: %s", to_email, subject)


async def _fetch_qr_images(
    ticket_qr_urls: list[str],
    seat_ids: list[int],
) -> list[bytes | None]:
    """Fetch QR images from S3 and return raw bytes (or None on failure)."""
    images: list[bytes | None] = []
    async with httpx.AsyncClient() as client:
        for url, seat_id in zip(ticket_qr_urls, seat_ids):
            try:
                internal_url = url.replace(settings.S3_PUBLIC_URL, settings.S3_INTERNAL_URL)
                resp = await client.get(internal_url, timeout=10.0)
                resp.raise_for_status()
                images.append(resp.content)
            except Exception as e:
                logger.warning("Failed to fetch QR image for seat %s: %s", seat_id, e)
                images.append(None)
    return images


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

        show_name = event.show_name or "your show"
        subject = f"You're in! Booking confirmed for {show_name} 🎬"
        plain_body = textwrap.dedent(
            f"""
            Hey there,

            Great news — your booking is confirmed and your tickets are ready!

            Here's a quick summary:
              Booking ID: {event.booking_id}
              Show: {show_name}
              Seats: {len(event.seat_ids)}
              Total paid: \u20b9{event.total_amount}

            We've attached your tickets as a PDF — just show the QR codes at the entrance and you're good to go.

            Enjoy the show!
            Team TicketShow
            """
        ).strip()

        attachments = None

        if event.ticket_qr_urls and event.seat_labels and len(event.ticket_qr_urls) == len(event.seat_ids):
            qr_images = await _fetch_qr_images(event.ticket_qr_urls, event.seat_ids)

            try:
                pdf_bytes = generate_ticket_pdf(
                    booking_id=event.booking_id,
                    schedule_id=event.schedule_id,
                    total_amount=event.total_amount,
                    confirmed_at=event.confirmed_at.isoformat() if event.confirmed_at else "",
                    seat_labels=event.seat_labels,
                    qr_images=qr_images,
                    show_name=event.show_name,
                    show_time=event.show_time,
                )
                attachments = [
                    (f"tickets-booking-{event.booking_id}.pdf", pdf_bytes, "application/pdf"),
                ]
                logger.info("Generated PDF ticket for booking %s (%d bytes)", event.booking_id, len(pdf_bytes))
            except Exception as pdf_err:
                logger.error("PDF generation failed for booking %s: %s", event.booking_id, pdf_err, exc_info=True)

        await send_email_notification(
            to_email=to_email,
            subject=subject,
            body=plain_body,
            attachments=attachments,
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

        subject = "Heads up — your booking couldn't go through"
        body = textwrap.dedent(
            f"""
            Hey there,

            Unfortunately, we weren't able to complete your booking (#{event.booking_id}). The issue we ran into was: {event.reason}.

            No worries though — you can always try booking again. If it keeps happening, just reply to this email and we'll look into it for you.

            Thanks for your patience,
            Team TicketShow
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

        subject = "Your refund is on its way"
        body = textwrap.dedent(
            f"""
            Hey there,

            Just letting you know — we've initiated a refund of \u20b9{event.amount} for your booking (#{event.booking_id}).
            Reason: {event.reason}

            If you paid via Dodo, the refund will go back to your original payment method. Otherwise, it'll be credited to your TicketShow wallet.

            We'll drop you another email once the refund is fully processed.

            Cheers,
            Team TicketShow
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

        subject = "Refund complete — \u20b9" + str(event.amount) + " is headed your way"
        body = textwrap.dedent(
            f"""
            Hey there,

            Good news — your refund of \u20b9{event.amount} for booking #{event.booking_id} has been processed{refund_ref}.

            The amount has been sent {destination_text}{method_text}. It should reflect in your account shortly.

            If something doesn't look right, just reply to this email and we'll sort it out.

            Cheers,
            Team TicketShow
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
    successful_consumer = KafkaConsumerClient(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="notification-service-successful-group",
        topics=["booking.successful"],
        max_retries=3,
        retry_delay=1,
    )

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

    await asyncio.gather(
        successful_consumer.consume(handle_booking_successful),
        failed_consumer.consume(handle_booking_failed),
        refund_consumer.consume(handle_refund_initiated),
        refund_completed_consumer.consume(handle_refund_completed),
    )


def run_consumers():
    """Run the Kafka consumers in the background"""
    asyncio.create_task(start_kafka_consumers())
