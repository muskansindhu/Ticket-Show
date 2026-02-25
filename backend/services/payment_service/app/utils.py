import uuid
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from dodopayments import AsyncDodoPayments


def get_dodo_client(api_key: str, environment: str) -> AsyncDodoPayments:
    if not api_key:
        raise RuntimeError("Dodo API key is not configured")
    return AsyncDodoPayments(
        bearer_token=api_key,
        environment=environment,
    )


def to_dict(value: Any) -> dict:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        dumped = value.model_dump()
        return dumped if isinstance(dumped, dict) else {}
    if hasattr(value, "to_dict"):
        dumped = value.to_dict()
        return dumped if isinstance(dumped, dict) else {}
    if hasattr(value, "__dict__"):
        dumped = dict(value.__dict__)
        return dumped if isinstance(dumped, dict) else {}
    return {}


def extract_checkout_session_fields(session: Any) -> tuple[str, str]:
    payload = to_dict(session)
    checkout_url = (
        payload.get("checkout_url")
        or payload.get("url")
        or getattr(session, "checkout_url", "")
        or getattr(session, "url", "")
        or ""
    )
    session_id = (
        payload.get("session_id")
        or payload.get("id")
        or getattr(session, "session_id", "")
        or getattr(session, "id", "")
        or ""
    )
    if not checkout_url:
        payments = payload.get("payments") or getattr(session, "payments", []) or []
        if isinstance(payments, list) and payments:
            first = payments[0]
            first_payment = to_dict(first)
            checkout_url = (
                first_payment.get("payment_link")
                or getattr(first, "payment_link", "")
                or ""
            )
            if not session_id:
                session_id = (
                    first_payment.get("payment_id")
                    or first_payment.get("id")
                    or getattr(first, "payment_id", "")
                    or getattr(first, "id", "")
                    or ""
                )

    if not checkout_url:
        raise ValueError("Dodo checkout URL missing in response")
    if not session_id:
        session_id = str(uuid.uuid4())
    return str(session_id), str(checkout_url)


def to_positive_int(value: Any) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def is_refund_event(event_type: str) -> bool:
    normalized = (event_type or "").lower()
    return "refund" in normalized


def to_minor_units(amount: float | int | str) -> int:
    normalized = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if normalized <= 0:
        raise ValueError("Amount must be greater than zero")
    return int(normalized * 100)
