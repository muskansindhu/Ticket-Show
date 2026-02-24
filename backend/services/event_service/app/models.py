from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Time, text
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base


class Show(Base):
    """Movie/Event show"""
    __tablename__ = "shows"
    __table_args__ = {"schema": "events"}

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    status = Column(String(20), nullable=False, default="ACTIVE", index=True)
    description = Column(Text, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)
    language = Column(String(50))
    rating = Column(String(10))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    schedules = relationship("Schedule", back_populates="show")


class Venue(Base):
    """Physical venue/theater"""
    __tablename__ = "venues"
    __table_args__ = {"schema": "events"}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    status = Column(String(20), nullable=False, default="ACTIVE", index=True)
    location = Column(String(500), nullable=False)
    opening_time = Column(Time, nullable=False)
    closing_time = Column(Time, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    screens = relationship("Screen", back_populates="venue")


class Screen(Base):
    """Screen within a venue"""
    __tablename__ = "screens"
    __table_args__ = {"schema": "events"}

    id = Column(Integer, primary_key=True, index=True)
    venue_id = Column(Integer, ForeignKey("events.venues.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    capacity = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    venue = relationship("Venue", back_populates="screens")
    schedules = relationship("Schedule", back_populates="screen")
    seats = relationship("Seat", back_populates="screen")


class Schedule(Base):
    """Show schedule on a specific screen"""
    __tablename__ = "schedules"
    __table_args__ = (
        # CRITICAL: PostgreSQL exclusion constraint to prevent overlapping schedules
        # This ensures no two schedules overlap on the same screen
        ExcludeConstraint(
            (text("screen_id"), "="),
            (text("tstzrange(start_time, end_time)"), "&&"),
            name="no_overlapping_schedules",
            using="gist",
        ),
        {"schema": "events"},
    )

    id = Column(Integer, primary_key=True, index=True)
    show_id = Column(Integer, ForeignKey("events.shows.id"), nullable=False, index=True)
    screen_id = Column(Integer, ForeignKey("events.screens.id"), nullable=False, index=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    created_by_admin_id = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    show = relationship("Show", back_populates="schedules")
    screen = relationship("Screen", back_populates="schedules")


class Seat(Base):
    """Seat in a screen"""
    __tablename__ = "seats"
    __table_args__ = {"schema": "events"}

    id = Column(Integer, primary_key=True, index=True)
    screen_id = Column(Integer, ForeignKey("events.screens.id"), nullable=False, index=True)
    seat_number = Column(String(10), nullable=False)
    row_number = Column(String(5), nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    screen = relationship("Screen", back_populates="seats")
