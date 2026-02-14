from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import settings
from .routes import shows_router, venues_router, screens_router, schedules_router
from .database import engine, Base
from shared.utils import setup_logger

logger = setup_logger(settings.SERVICE_NAME, settings.LOG_LEVEL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    logger.info(f"{settings.SERVICE_NAME} starting up...")
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info(f"{settings.SERVICE_NAME} started successfully")
    
    yield
    
    # Shutdown
    logger.info(f"{settings.SERVICE_NAME} shutting down...")
    await engine.dispose()
    logger.info(f"{settings.SERVICE_NAME} shut down successfully")


# Create FastAPI app
app = FastAPI(
    title="Event Service",
    description="Show, Venue, Screen, and Schedule management service for Ticket Show",
    version="2.0.0",
    lifespan=lifespan
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
        "status": "running"
    }