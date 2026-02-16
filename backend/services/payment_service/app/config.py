from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://ticketshow:ticketshow123@localhost:5432/ticketshow"

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"

    # Payment
    PAYMENT_PROCESSING_DELAY_SECONDS: int = 2

    # Service
    SERVICE_NAME: str = "payment-service"
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"


settings = Settings()
