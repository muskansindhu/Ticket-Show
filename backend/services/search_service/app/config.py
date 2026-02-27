from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://ticketshow:ticketshow123@localhost:5432/ticketshow"
    ELASTICSEARCH_URL: str = "http://localhost:9200"
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    SERVICE_NAME: str = "search-service"
    LOG_LEVEL: str = "INFO"


settings = Settings()
