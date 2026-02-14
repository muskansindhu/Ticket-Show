from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Service URLs
    AUTH_SERVICE_URL: str = "http://localhost:8001"
    EVENT_SERVICE_URL: str = "http://localhost:8002"

    # JWT
    JWT_SECRET: str = "test-secret-key-for-jwt-generation"

    # Service
    SERVICE_NAME: str = "api-gateway"
    LOG_LEVEL: str = "INFO"

settings = Settings()