"""
Generate a styled PDF with ticket cards — one per seat.

Uses only Pillow (PIL) for rendering. Each ticket is drawn as an image,
then all ticket images are combined into a multi-page PDF.
"""

import io
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont


# Dimensions (pixels at 150 DPI)
DPI = 150
PAGE_W = int(8.27 * DPI)   # A4 width
PAGE_H = int(11.69 * DPI)  # A4 height
MARGIN = int(0.6 * DPI)

TICKET_W = PAGE_W - 2 * MARGIN
TICKET_H = int(3.0 * DPI)
GAP = int(0.25 * DPI)

# Colours
BG_COLOR = (255, 255, 255)
CARD_BG = (248, 249, 250)
CARD_BORDER = (210, 210, 215)
GRAD_START = (99, 102, 241)   # #6366f1
GRAD_END = (139, 92, 246)     # #8b5cf6
TEXT_WHITE = (255, 255, 255)
TEXT_DARK = (26, 26, 46)
TEXT_MID = (85, 85, 85)
TEXT_LIGHT = (140, 140, 140)
ACCENT = (79, 70, 229)


def _get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Get a font, falling back to default if needed."""
    try:
        if bold:
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except (OSError, IOError):
        return ImageFont.load_default()


def _draw_gradient_bar(draw: ImageDraw.Draw, x: int, y: int, w: int, h: int):
    """Draw a horizontal gradient rectangle."""
    for i in range(w):
        t = i / max(w - 1, 1)
        r = int(GRAD_START[0] + (GRAD_END[0] - GRAD_START[0]) * t)
        g = int(GRAD_START[1] + (GRAD_END[1] - GRAD_START[1]) * t)
        b = int(GRAD_START[2] + (GRAD_END[2] - GRAD_START[2]) * t)
        draw.line([(x + i, y), (x + i, y + h - 1)], fill=(r, g, b))


def _draw_dashed_line(draw: ImageDraw.Draw, x: int, y1: int, y2: int, dash=8, gap=6):
    """Draw a vertical dashed line."""
    y = y1
    while y < y2:
        end = min(y + dash, y2)
        draw.line([(x, y), (x, end)], fill=CARD_BORDER, width=2)
        y = end + gap


def _format_show_time(show_time: str | None) -> str:
    """Format ISO time string to a human readable format."""
    if not show_time:
        return ""
    try:
        dt = datetime.fromisoformat(show_time)
        return dt.strftime("%d %b %Y, %I:%M %p")
    except Exception:
        return show_time


def _draw_ticket(
    draw: ImageDraw.Draw,
    x: int,
    y: int,
    booking_id: int,
    seat_label: str,
    total_amount: float,
    confirmed_at: str,
    qr_image: Image.Image | None,
    page_img: Image.Image,
    show_name: str | None = None,
    show_time: str | None = None,
):
    """Draw a single ticket card at (x, y) on the page image."""
    border_r = 12

    # Card background with rounded corners
    draw.rounded_rectangle(
        [x, y, x + TICKET_W, y + TICKET_H],
        radius=border_r,
        fill=CARD_BG,
        outline=CARD_BORDER,
        width=2,
    )

    # Gradient header bar
    header_h = int(TICKET_H * 0.24)
    # Create gradient on a temp image and paste with proper clipping
    grad_img = Image.new("RGB", (TICKET_W, header_h))
    grad_draw = ImageDraw.Draw(grad_img)
    _draw_gradient_bar(grad_draw, 0, 0, TICKET_W, header_h)

    # Mask for rounded top corners
    mask = Image.new("L", (TICKET_W, header_h), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle(
        [0, 0, TICKET_W - 1, header_h + border_r],
        radius=border_r,
        fill=255,
    )
    page_img.paste(grad_img, (x, y), mask)

    # Fonts
    font_brand = _get_font(13, bold=True)
    font_booking_id = _get_font(11)
    font_show_name = _get_font(26, bold=True)
    font_show_time = _get_font(16, bold=True)
    font_seat = _get_font(18, bold=True)
    font_detail = _get_font(12)
    font_small = _get_font(10)
    font_scan = _get_font(10)

    # Header — brand name left, booking ID right
    draw.text((x + 16, y + header_h // 2 - 9), "TICKET SHOW", fill=TEXT_WHITE, font=font_brand)
    booking_text = f"Booking #{booking_id}"
    bbox = draw.textbbox((0, 0), booking_text, font=font_booking_id)
    tw = bbox[2] - bbox[0]
    draw.text((x + TICKET_W - tw - 16, y + header_h // 2 - 7), booking_text, fill=TEXT_WHITE, font=font_booking_id)

    # Body content
    content_y = y + header_h + 14

    # Show name — large and bold
    display_name = show_name or "Show"
    draw.text((x + 18, content_y), display_name, fill=TEXT_DARK, font=font_show_name)

    # Show time — bold, slightly smaller
    time_str = _format_show_time(show_time)
    if time_str:
        draw.text((x + 18, content_y + 36), time_str, fill=ACCENT, font=font_show_time)

    # Seat label
    seat_y = content_y + 68
    draw.text((x + 18, seat_y), seat_label, fill=TEXT_DARK, font=font_seat)

    # Amount
    draw.text((x + 18, seat_y + 28), f"\u20b9{total_amount}", fill=TEXT_MID, font=font_detail)

    # Confirmed date (small)
    if confirmed_at:
        try:
            dt = datetime.fromisoformat(confirmed_at)
            date_str = dt.strftime("%d %b %Y, %I:%M %p")
        except Exception:
            date_str = confirmed_at
        draw.text((x + 18, seat_y + 48), f"Booked: {date_str}", fill=TEXT_LIGHT, font=font_small)

    # Dashed vertical separator
    sep_x = x + TICKET_W - int(TICKET_W * 0.35)
    _draw_dashed_line(draw, sep_x, y + header_h + 10, y + TICKET_H - 10)

    # QR code section (right side)
    qr_area_x = sep_x + 20
    qr_size = min(int(TICKET_W * 0.28), TICKET_H - header_h - 50)

    if qr_image:
        qr_resized = qr_image.resize((qr_size, qr_size), Image.LANCZOS)
        qr_y = y + header_h + (TICKET_H - header_h - qr_size) // 2 - 8
        page_img.paste(qr_resized, (qr_area_x, qr_y))
        # "Scan at entrance" label
        scan_bbox = draw.textbbox((0, 0), "Scan at entrance", font=font_scan)
        scan_tw = scan_bbox[2] - scan_bbox[0]
        scan_x = qr_area_x + (qr_size - scan_tw) // 2
        draw.text((scan_x, qr_y + qr_size + 4), "Scan at entrance", fill=TEXT_LIGHT, font=font_scan)
    else:
        draw.text(
            (qr_area_x + 10, y + header_h + (TICKET_H - header_h) // 2 - 8),
            "QR unavailable",
            fill=TEXT_LIGHT,
            font=font_detail,
        )


def generate_ticket_pdf(
    booking_id: int,
    schedule_id: int,
    total_amount: float,
    confirmed_at: str,
    seat_labels: list[dict],
    qr_images: list[bytes | None],
    show_name: str | None = None,
    show_time: str | None = None,
) -> bytes:
    """Generate a PDF with one ticket card per seat, stacked vertically."""

    tickets_per_page = max(1, (PAGE_H - 2 * MARGIN + GAP) // (TICKET_H + GAP))
    pages: list[Image.Image] = []
    current_page: Image.Image | None = None
    current_draw: ImageDraw.Draw | None = None
    slot = 0

    for i, label_info in enumerate(seat_labels):
        if slot == 0 or current_page is None:
            current_page = Image.new("RGB", (PAGE_W, PAGE_H), BG_COLOR)
            current_draw = ImageDraw.Draw(current_page)
            pages.append(current_page)
            slot = 0

        row_num = label_info.get("row_number", "?")
        seat_num = label_info.get("seat_number", "?")
        seat_label = f"Row {row_num}  -  Seat {seat_num}"

        y = MARGIN + slot * (TICKET_H + GAP)

        # Parse QR image
        qr_img = None
        if i < len(qr_images) and qr_images[i]:
            try:
                qr_img = Image.open(io.BytesIO(qr_images[i])).convert("RGB")
            except Exception:
                qr_img = None

        _draw_ticket(
            draw=current_draw,
            x=MARGIN,
            y=y,
            booking_id=booking_id,
            seat_label=seat_label,
            total_amount=total_amount,
            confirmed_at=confirmed_at,
            qr_image=qr_img,
            page_img=current_page,
            show_name=show_name,
            show_time=show_time,
        )

        slot += 1
        if slot >= tickets_per_page:
            slot = 0

    # Save all pages as a single PDF
    buf = io.BytesIO()
    if pages:
        pages[0].save(
            buf,
            format="PDF",
            save_all=True,
            append_images=pages[1:] if len(pages) > 1 else [],
            resolution=DPI,
        )
    return buf.getvalue()
