import io
import json
from typing import List

import qrcode

from shared.utils import setup_logger
from .s3_client import upload_file

logger = setup_logger(__name__)


def generate_ticket_qrs(
    booking_id: int,
    schedule_id: int,
    seat_ids: List[int],
    correlation_id: str,
    seat_labels: List[dict] | None = None,
) -> List[str]:
    """Generate QR code tickets and upload to S3.

    seat_labels: optional list of {"row_number": "R01", "seat_number": "S001"} dicts.
    """
    urls = []

    for idx, seat_id in enumerate(seat_ids):
        label = seat_labels[idx] if seat_labels and idx < len(seat_labels) else None
        payload = json.dumps({
            "booking_id": booking_id,
            "seat_id": seat_id,
            "schedule_id": schedule_id,
            "correlation_id": correlation_id,
            "row": label["row_number"] if label else None,
            "seat": label["seat_number"] if label else None,
        })

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(payload)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        png_bytes = buf.getvalue()

        key = f"tickets/booking-{booking_id}/seat-{seat_id}.png"
        url = upload_file(png_bytes, key, "image/png")
        urls.append(url)

    logger.info(
        "Generated %d QR ticket(s) for booking %s",
        len(urls),
        booking_id,
    )
    return urls
