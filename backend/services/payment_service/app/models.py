from sqlalchemy import Column, DateTime, Integer, Numeric, String
from sqlalchemy.sql import func

from .database import Base


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = {"schema": "payments"}

    id = Column(Integer, primary_key=True, index=True)
    idempotency_key = Column(String(255), unique=True, nullable=False, index=True)
    booking_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(20), nullable=False, default="PENDING", index=True)
    payment_method = Column(String(50))
    transaction_id = Column(String(255))
    correlation_id = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
