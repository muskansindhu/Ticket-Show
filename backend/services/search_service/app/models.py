from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Time
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base


class Show(Base):
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

    schedules = relationship("Schedule", back_populates="show")


class Venue(Base):
    __tablename__ = "venues"
    __table_args__ = {"schema": "events"}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    status = Column(String(20), nullable=False, default="ACTIVE", index=True)
    location = Column(String(500), nullable=False)
    city = Column(String(100), nullable=False, index=True)
    opening_time = Column(Time, nullable=False)
    closing_time = Column(Time, nullable=False)

    screens = relationship("Screen", back_populates="venue")


class Screen(Base):
    __tablename__ = "screens"
    __table_args__ = {"schema": "events"}

    id = Column(Integer, primary_key=True, index=True)
    venue_id = Column(Integer, ForeignKey("events.venues.id"), nullable=False, index=True)

    venue = relationship("Venue", back_populates="screens")
    schedules = relationship("Schedule", back_populates="screen")


class Schedule(Base):
    __tablename__ = "schedules"
    __table_args__ = {"schema": "events"}

    id = Column(Integer, primary_key=True, index=True)
    show_id = Column(Integer, ForeignKey("events.shows.id"), nullable=False, index=True)
    screen_id = Column(Integer, ForeignKey("events.screens.id"), nullable=False, index=True)

    show = relationship("Show", back_populates="schedules")
    screen = relationship("Screen", back_populates="schedules")
