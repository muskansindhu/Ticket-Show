from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9093"

    # Email (SMTP)
    SMTP_HOST: str = "mailpit"
    SMTP_PORT: int = 1025
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = False
    SMTP_USE_SSL: bool = False
    SMTP_TIMEOUT: int = 10
    SMTP_FROM_EMAIL: str = "no-reply@ticketshow.local"
    SMTP_FROM_NAME: str = "Ticket Show"
    DEFAULT_TO_EMAIL: str = ""
    DEFAULT_EMAIL_DOMAIN: str = ""

    # Service
    SERVICE_NAME: str = "notification-service"
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"


settings = Settings()
