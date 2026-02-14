from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


# User Schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8) 
    username: str = Field(..., min_length=1)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    
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
