from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.utils import setup_logger
from .config import settings
from .database import Base, engine
from .kafka_handler import close_kafka_producer, init_kafka_producer, run_consumers
from .routes import router
from .s3_client import init_s3

logger = setup_logger(settings.SERVICE_NAME, settings.LOG_LEVEL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    logger.info(f"{settings.SERVICE_NAME} starting up...")

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Initialize Kafka producer
    await init_kafka_producer()
    run_consumers()

    # Initialize S3 client for QR ticket uploads
    init_s3()

    logger.info(f"{settings.SERVICE_NAME} started successfully")

    yield

    # Shutdown
    logger.info(f"{settings.SERVICE_NAME} shutting down...")
    await close_kafka_producer()
    await engine.dispose()
    logger.info(f"{settings.SERVICE_NAME} shut down successfully")


# Create FastAPI app
app = FastAPI(
    title="Payment Service",
    description="Payment processing service for Ticket Show",
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
