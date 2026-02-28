from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://ticketshow:ticketshow123@localhost:5432/ticketshow"

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    AUTH_SERVICE_URL: str = "http://auth-service:8000"
    BOOKING_SERVICE_URL: str = "http://booking-service:8000"

    # Payment
    PAYMENT_PROCESSING_DELAY_SECONDS: int = 2
    DODO_PAYMENTS_API_KEY: str = ""
    DODO_PAYMENTS_ENVIRONMENT: str = "test_mode"
    DODO_PAYMENTS_PRODUCT_ID: str = ""
    DODO_PAYMENTS_RETURN_URL: str = "http://localhost:5173/bookings"
    DODO_PAYMENTS_WEBHOOK_KEY: str = ""

    # S3 / MinIO
    S3_ENDPOINT_URL: str = "http://minio:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET_NAME: str = "ticket-show-posters"
    S3_PUBLIC_URL: str = "http://localhost:9000"

    # Service
    SERVICE_NAME: str = "payment-service"
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"


settings = Settings()
