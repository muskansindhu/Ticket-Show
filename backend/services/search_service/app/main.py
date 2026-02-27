from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.utils import setup_logger
from .config import settings
from .database import engine
from .elastic import close_es, init_es
from .kafka_handler import run_consumers
from .routes import router

logger = setup_logger(settings.SERVICE_NAME, settings.LOG_LEVEL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("%s starting up...", settings.SERVICE_NAME)
    await init_es()
    run_consumers()
    yield
    logger.info("%s shutting down...", settings.SERVICE_NAME)
    await close_es()
    await engine.dispose()


app = FastAPI(
    title="Search Service",
    description="Search shows and venues",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.SERVICE_NAME}


@app.get("/")
async def root():
    return {
        "service": settings.SERVICE_NAME,
        "version": "1.0.0",
        "status": "running",
    }
