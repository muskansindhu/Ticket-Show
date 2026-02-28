from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


# Enums
class BookingStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"


class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    REFUND_INITIATED = "REFUND_INITIATED"
    REFUNDED = "REFUNDED"
    FAILED = "FAILED"


class PaymentMethod(str, Enum):
    CARD = "CARD"
    UPI = "UPI"
    NETBANKING = "NETBANKING"
    WALLET = "WALLET"
    DODO = "DODO"


class WalletTransactionType(str, Enum):
    REFUND = "REFUND"
    DEBIT = "DEBIT"


# User Schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    username: str = Field(..., min_length=1)
    city: Optional[str] = Field(None, min_length=1, max_length=100)


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    city: Optional[str] = Field(None, min_length=1, max_length=100)


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    city: Optional[str] = None
    wallet_balance: Optional[float] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None


class SeatResponse(BaseModel):
    id: int
    event_id: int
    seat_number: str
    row_number: str
    is_available: bool

    class Config:
        from_attributes = True


# Booking Schemas
class BookingCreate(BaseModel):
    schedule_id: int
    seat_ids: List[int] = Field(..., min_items=1)
    idempotency_key: str = Field(..., min_length=1)


class BookingResponse(BaseModel):
    id: int
    user_id: int
    schedule_id: int
    seat_ids: List[int]
    total_amount: float
    status: BookingStatus
    correlation_id: str
    created_at: datetime
    expires_at: datetime
    ticket_qr_urls: Optional[List[str]] = None
    seat_labels: Optional[List[dict]] = None
    show_name: Optional[str] = None
    show_time: Optional[str] = None

    class Config:
        from_attributes = True


# Kafka Event Schemas
class BookingCreatedEvent(BaseModel):
    booking_id: int
    user_id: int
    schedule_id: int
    seat_ids: List[int]
    total_amount: float
    correlation_id: str
    idempotency_key: str
    created_at: datetime


class PaymentCompletedEvent(BaseModel):
    payment_id: int
    booking_id: int
    user_id: int
    amount: float
    status: PaymentStatus
    transaction_id: Optional[str]
    correlation_id: str
    idempotency_key: str
    created_at: datetime


class BookingConfirmedEvent(BaseModel):
    booking_id: int
    user_id: int
    schedule_id: int
    seat_ids: List[int]
    total_amount: float
    correlation_id: str
    confirmed_at: datetime


class BookingSuccessfulEvent(BaseModel):
    booking_id: int
    user_id: int
    user_email: Optional[EmailStr] = None
    schedule_id: int
    seat_ids: List[int]
    total_amount: float
    correlation_id: str
    confirmed_at: datetime
    ticket_qr_urls: Optional[List[str]] = None
    seat_labels: Optional[List[dict]] = None
    show_name: Optional[str] = None
    show_time: Optional[str] = None


class BookingFailedEvent(BaseModel):
    booking_id: int
    user_id: int
    user_email: Optional[EmailStr] = None
    reason: str
    correlation_id: str
    failed_at: datetime


# Payment Schemas
class PaymentResponse(BaseModel):
    id: int
    idempotency_key: str
    booking_id: int
    user_id: int
    amount: float
    status: PaymentStatus
    payment_method: PaymentMethod
    transaction_id: str
    checkout_url: Optional[str] = None
    correlation_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Payment Create Schema
class PaymentCreate(BaseModel):
    booking_id: int
    amount: float
    payment_method: PaymentMethod
    user_id: int
    user_email: Optional[EmailStr] = None


class RefundInitiatedEvent(BaseModel):
    booking_id: int
    user_id: int
    amount: float
    correlation_id: str
    reason: str
    initiated_by: str
    initiated_at: datetime
    user_email: Optional[EmailStr] = None


class RefundCompletedEvent(BaseModel):
    booking_id: int
    user_id: int
    amount: float
    correlation_id: str
    refunded_at: datetime
    user_email: Optional[EmailStr] = None
    refund_id: Optional[str] = None
    payment_method: Optional[str] = None


class WalletTransactionResponse(BaseModel):
    id: int
    user_id: int
    amount: float
    transaction_type: WalletTransactionType
    description: str
    reference_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class WalletResponse(BaseModel):
    user_id: int
    current_amount: float
    updated_at: datetime
    transactions: List[WalletTransactionResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True
