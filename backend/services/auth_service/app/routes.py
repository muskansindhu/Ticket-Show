from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.schemas import Token, UserCreate, UserLogin, UserResponse, WalletResponse
from shared.schemas import WalletTransactionType as WalletTransactionTypeSchema
from shared.utils import setup_logger
from .auth import create_access_token, get_current_user, get_password_hash, verify_password
from .database import get_db
from .models import User, Wallet, WalletTransaction, WalletTransactionType

logger = setup_logger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


class WalletCreditRequest(BaseModel):
    user_id: int
    amount: float = Field(..., gt=0)
    reference_id: str | None = None
    description: str = "Refund credited"


async def _get_or_create_wallet(user_id: int, db: AsyncSession) -> Wallet:
    result = await db.execute(select(Wallet).where(Wallet.user_id == user_id))
    wallet = result.scalar_one_or_none()
    if wallet:
        return wallet

    wallet = Wallet(user_id=user_id, current_amount=0)
    db.add(wallet)
    await db.commit()
    await db.refresh(wallet)
    return wallet


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    try:
        result = await db.execute(select(User).where(User.email == user_data.email))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        hashed_password = get_password_hash(user_data.password)
        new_user = User(
            email=user_data.email,
            password_hash=hashed_password,
            username=user_data.username,
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        wallet = Wallet(user_id=new_user.id, current_amount=0)
        db.add(wallet)
        await db.commit()

        logger.info(f"User registered: {new_user.email}")

        return {
            "id": new_user.id,
            "email": new_user.email,
            "username": new_user.username,
            "wallet_balance": 0,
            "created_at": new_user.created_at,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering user: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user",
        )


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login and get access token."""
    try:
        result = await db.execute(select(User).where(User.email == user_data.email))
        user = result.scalar_one_or_none()

        if not user or not verify_password(user_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "role": user.role.value,
            },
        )

        logger.info(f"User logged in: {user.email} (Role: {user.role.value})")

        return {"access_token": access_token, "token_type": "bearer"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed",
        )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get current user information."""
    wallet = await _get_or_create_wallet(current_user.id, db)
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "wallet_balance": float(wallet.current_amount),
        "created_at": current_user.created_at,
    }


@router.get("/wallet", response_model=WalletResponse)
async def get_wallet(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get wallet balance and wallet transaction history for current user."""
    wallet = await _get_or_create_wallet(current_user.id, db)

    tx_result = await db.execute(
        select(WalletTransaction)
        .where(WalletTransaction.user_id == current_user.id)
        .order_by(desc(WalletTransaction.created_at))
    )
    transactions = tx_result.scalars().all()

    return {
        "user_id": current_user.id,
        "current_amount": float(wallet.current_amount),
        "updated_at": wallet.updated_at,
        "transactions": [
            {
                "id": tx.id,
                "user_id": tx.user_id,
                "amount": float(tx.amount),
                "transaction_type": WalletTransactionTypeSchema(tx.transaction_type.value),
                "description": tx.description,
                "reference_id": tx.reference_id,
                "created_at": tx.created_at,
            }
            for tx in transactions
        ],
    }


@router.post("/wallet/internal/credit")
async def credit_wallet_internal(payload: WalletCreditRequest, db: AsyncSession = Depends(get_db)):
    """Credit wallet for internal refund processing (used by payment service)."""
    try:
        if payload.reference_id:
            existing_tx_result = await db.execute(
                select(WalletTransaction).where(WalletTransaction.reference_id == payload.reference_id)
            )
            existing_tx = existing_tx_result.scalar_one_or_none()
            if existing_tx:
                wallet = await _get_or_create_wallet(payload.user_id, db)
                return {
                    "status": "already_processed",
                    "wallet_balance": float(wallet.current_amount),
                }

        wallet = await _get_or_create_wallet(payload.user_id, db)

        wallet.current_amount = float(wallet.current_amount) + payload.amount
        transaction = WalletTransaction(
            wallet_id=wallet.id,
            user_id=payload.user_id,
            amount=payload.amount,
            transaction_type=WalletTransactionType.REFUND,
            description=payload.description,
            reference_id=payload.reference_id,
        )
        db.add(transaction)
        await db.commit()
        await db.refresh(wallet)

        return {
            "status": "credited",
            "wallet_balance": float(wallet.current_amount),
        }
    except Exception as e:
        logger.error("Error crediting wallet: %s", str(e), exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to credit wallet",
        )


@router.post("/verify")
async def verify_token_endpoint(current_user: User = Depends(get_current_user)):
    """Verify token validity (used by API Gateway)."""
    return {
        "valid": True,
        "user_id": current_user.id,
        "email": current_user.email,
    }
