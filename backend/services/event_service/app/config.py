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
    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET_NAME: str = "ticket-show-posters"
    S3_PUBLIC_URL: str = "http://localhost:9000"
    MAX_POSTER_SIZE_BYTES: int = 5 * 1024 * 1024

    # Service
    SERVICE_NAME: str = "event-service"
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"


settings = Settings()
