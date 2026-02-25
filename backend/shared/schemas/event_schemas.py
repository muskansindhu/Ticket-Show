from datetime import datetime, time
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, validator


class VenueStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class ShowStatus(str, Enum):
    ACTIVE = "ACTIVE"
    CANCELLED = "CANCELLED"


# Show Schemas
class ShowCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    duration_minutes: int = Field(..., gt=0)
    price: int = Field(..., gt=0)
    description: str = Field(..., min_length=32)
    language: Optional[str] = Field(None, max_length=50)
    rating: Optional[str] = Field(None, max_length=10)


class ShowResponse(BaseModel):
    id: int
    title: str
    status: ShowStatus
    duration_minutes: int
    price: int
    description: str
    language: Optional[str]
    rating: Optional[str]
    poster_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ShowUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[ShowStatus] = None
    duration_minutes: Optional[int] = Field(None, gt=0)
    price: Optional[int] = Field(None, gt=0)
    description: Optional[str] = Field(None, min_length=32)
    language: Optional[str] = Field(None, max_length=50)
    rating: Optional[str] = Field(None, max_length=10)
    poster_url: Optional[str] = Field(None, max_length=1000)


# Venue Schemas
class VenueCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    location: str = Field(..., min_length=1, max_length=500)
    city: str = Field(..., min_length=1, max_length=100)
    opening_time: time
    closing_time: time
    
    @validator("closing_time")
    def validate_closing_time(cls, v, values):
        if "opening_time" in values and v <= values["opening_time"]:
            raise ValueError("closing_time must be after opening_time")
        return v


class VenueResponse(BaseModel):
    id: int
    name: str
    status: VenueStatus
    location: str
    city: str
    opening_time: time
    closing_time: time
    created_at: datetime

    class Config:
        from_attributes = True


class VenueUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[VenueStatus] = None
    location: Optional[str] = Field(None, min_length=1, max_length=500)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    opening_time: Optional[time] = None
    closing_time: Optional[time] = None


class SearchShowResult(BaseModel):
    id: int
    title: str
    duration_minutes: int
    price: int
    language: Optional[str]
    rating: Optional[str]


class SearchVenueResult(BaseModel):
    id: int
    name: str
    location: str
    city: str
    opening_time: time
    closing_time: time


class SearchResponse(BaseModel):
    query: str
    city: Optional[str] = None
    shows: list[SearchShowResult] = Field(default_factory=list)
    venues: list[SearchVenueResult] = Field(default_factory=list)


# Screen Schemas
class ScreenCreate(BaseModel):
    venue_id: int
    name: str = Field(..., min_length=1, max_length=100)
    capacity: int = Field(..., gt=0)


class ScreenResponse(BaseModel):
    id: int
    venue_id: int
    name: str
    capacity: int
    created_at: datetime

    class Config:
        from_attributes = True


class ScreenUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    capacity: Optional[int] = Field(None, gt=0)


# Schedule Schemas
class ScheduleCreate(BaseModel):
    show_id: int
    screen_id: int
    start_time: datetime
    
    @validator("start_time")
    def validate_start_time(cls, v):
        if v < datetime.utcnow():
            raise ValueError("start_time cannot be in the past")
        return v


class ScheduleResponse(BaseModel):
    id: int
    show_id: int
    screen_id: int
    start_time: datetime
    end_time: datetime
    created_by_admin_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ScheduleUpdate(BaseModel):
    show_id: Optional[int] = None
    screen_id: Optional[int] = None
    start_time: Optional[datetime] = None

    @validator("start_time")
    def validate_start_time(cls, v):
        if v is not None and v < datetime.utcnow():
            raise ValueError("start_time cannot be in the past")
        return v


class ScheduleWithDetails(BaseModel):
    """Schedule with show and screen details"""
    id: int
    show_title: str
    show_duration: int
    screen_name: str
    venue_name: str
    start_time: datetime
    end_time: datetime
    created_at: datetime

    class Config:
        from_attributes = True
