from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://ticketshow:ticketshow123@localhost:5432/ticketshow"
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"

    # Booking
    BOOKING_LOCK_TIMEOUT_MINUTES: int = 10

    # Service
    SERVICE_NAME: str = "booking-service"
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"


settings = Settings()
