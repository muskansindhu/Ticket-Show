from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.utils import setup_logger
from .config import settings
from .database import Base, engine
from .kafka_handler import close_kafka_producer, init_kafka_producer
from .routes import router

logger = setup_logger(settings.SERVICE_NAME, settings.LOG_LEVEL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    logger.info(f"{settings.SERVICE_NAME} starting up...")

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

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
    title="Booking Service",
    description="Seat booking service with row-level locking for Ticket Show",
    version="1.0.0",
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
app.include_router(router)


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
