from sqlalchemy import ARRAY, Column, DateTime, Integer, Numeric, String
from sqlalchemy.sql import func

from .database import Base


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = {"schema": "bookings"}
    id = Column(Integer, primary_key=True, index=True)
    idempotency_key = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    schedule_id = Column(Integer, nullable=False)
    seat_ids = Column(ARRAY(Integer), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(20), nullable=False, default="PENDING", index=True)
    correlation_id = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
