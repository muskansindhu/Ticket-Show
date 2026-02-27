from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = (
        "postgresql://ticketshow:ticketshow123@ticket-show-postgres:5432/ticketshow"
    )

    # JWT
    JWT_SECRET: str = "test-secret-key-for-jwt-generation"
    BOOKING_SERVICE_URL: str = "http://booking-service:8000"
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    POSTER_UPLOAD_DIR: str = "/app/uploads/posters"
    MAX_POSTER_SIZE_BYTES: int = 5 * 1024 * 1024

    # Service
    SERVICE_NAME: str = "event-service"
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"


settings = Settings()
