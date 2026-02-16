from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = (
        "postgresql://ticketshow:ticketshow123@ticket-show-postgres:5432/ticketshow"
    )

    # JWT
    JWT_SECRET: str = "test-secret-key-for-jwt-generation"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 6000

    # Service
    SERVICE_NAME: str = "auth-service"
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"

settings = Settings()
