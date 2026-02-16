from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.utils import setup_logger
from .config import settings
from .kafka_handler import run_consumers

logger = setup_logger(settings.SERVICE_NAME, settings.LOG_LEVEL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    logger.info(f"{settings.SERVICE_NAME} starting up...")

    # Start Kafka consumers
    run_consumers()

    logger.info(f"{settings.SERVICE_NAME} started successfully")

    yield

    # Shutdown
    logger.info(f"{settings.SERVICE_NAME} shutting down...")
    logger.info(f"{settings.SERVICE_NAME} shut down successfully")


# Create FastAPI app
app = FastAPI(
    title="Notification Service",
    description="Notification service for Ticket Show",
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
