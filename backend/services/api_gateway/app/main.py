from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

from .config import settings
from .routes import (
    auth_router,
    bookings_router,
    payments_router,
    schedules_router,
    screens_router,
    shows_router,
    venues_router,
)

# Create FastAPI app
app = FastAPI(
    title="Ticket Show API Gateway",
    description="API Gateway for Ticket Show microservices platform",
    version="1.0.0",
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
app.include_router(auth_router)
app.include_router(shows_router)
app.include_router(venues_router)
app.include_router(screens_router)
app.include_router(schedules_router)
app.include_router(bookings_router)
app.include_router(payments_router)


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
        "description": "Ticket Show API Gateway - Your gateway to amazing events!",
    }


@app.get("/{path:path}")
async def spa_fallback(path: str, request: Request):
    """Redirect browser requests to the frontend dev server when present."""
    accept = request.headers.get("accept", "")
    if settings.FRONTEND_URL and "text/html" in accept:
        target = f"{settings.FRONTEND_URL.rstrip('/')}/{path}"
        return RedirectResponse(target)
    return JSONResponse({"detail": "Not Found"}, status_code=404)
