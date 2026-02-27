from pathlib import Path

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from shared.utils import setup_logger
from .config import settings
from .database import Base, engine
from .kafka_handler import close_kafka_producer, init_kafka_producer
from .routes import schedules_router, screens_router, shows_router, venues_router

logger = setup_logger(settings.SERVICE_NAME, settings.LOG_LEVEL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    logger.info(f"{settings.SERVICE_NAME} starting up...")

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(
            text(
                """
                ALTER TABLE IF EXISTS events.shows
                ADD COLUMN IF NOT EXISTS poster_url VARCHAR(1000)
                """
            )
        )
        await conn.execute(
            text(
                """
                ALTER TABLE IF EXISTS events.venues
                ADD COLUMN IF NOT EXISTS city VARCHAR(100)
                """
            )
        )
        await conn.execute(
            text(
                """
                UPDATE events.venues
                SET city = COALESCE(
                    NULLIF(trim(split_part(location, ',', 2)), ''),
                    NULLIF(trim(split_part(location, ',', 1)), ''),
                    'Unknown'
                )
                WHERE city IS NULL
                """
            )
        )
        await conn.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS idx_venues_city
                ON events.venues(city)
                """
            )
        )

    Path(settings.POSTER_UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

    await init_kafka_producer()

    logger.info(f"{settings.SERVICE_NAME} started successfully")

    yield

    # Shutdown
    logger.info(f"{settings.SERVICE_NAME} shutting down...")
    await close_kafka_producer()
    await engine.dispose()
    logger.info(f"{settings.SERVICE_NAME} shut down successfully")


# Create FastAPI app
app = FastAPI(
    title="Event Service",
    description="Show, Venue, Screen, and Schedule management service for Ticket Show",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(shows_router)
app.include_router(venues_router)
app.include_router(screens_router)
app.include_router(schedules_router)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": settings.SERVICE_NAME}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.SERVICE_NAME,
        "version": "1.0.0",
        "status": "running",
    }
