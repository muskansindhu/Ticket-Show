import enum
from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base


class UserRole(str, enum.Enum):
    """User roles for RBAC"""
    ADMIN = "ADMIN"
    USER = "USER"


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "auth"}

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    username = Column(String(255), nullable=False)
    city = Column(String(100), nullable=True, index=True)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.USER)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    wallet = relationship("Wallet", uselist=False, back_populates="user")


class WalletTransactionType(str, enum.Enum):
    REFUND = "REFUND"
    DEBIT = "DEBIT"


class Wallet(Base):
    __tablename__ = "wallets"
    __table_args__ = {"schema": "auth"}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("auth.users.id"), nullable=False, unique=True, index=True)
    current_amount = Column(Numeric(12, 2), nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="wallet")
    transactions = relationship("WalletTransaction", back_populates="wallet")


class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"
    __table_args__ = {"schema": "auth"}

    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(Integer, ForeignKey("auth.wallets.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("auth.users.id"), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    transaction_type = Column(SQLEnum(WalletTransactionType), nullable=False)
    description = Column(String(500), nullable=False)
    reference_id = Column(String(255), nullable=True, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    wallet = relationship("Wallet", back_populates="transactions")
