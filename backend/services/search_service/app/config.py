from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://ticketshow:ticketshow123@localhost:5432/ticketshow"
    SERVICE_NAME: str = "search-service"
    LOG_LEVEL: str = "INFO"


settings = Settings()
