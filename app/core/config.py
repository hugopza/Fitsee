from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Fittsee Demo Backend"
    API_V1_STR: str = "/api/v1"

    # Docker-friendly defaults (compose service names)
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_SERVER: str = "db"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "fittsee"
    DATABASE_URL: str = ""  # if empty, will be assembled from fields above

    JWT_SECRET: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    ADMIN_EMAIL: str
    ADMIN_PASSWORD: str

    # Storage paths (mounted volume: ./data -> /app/data)
    UPLOAD_DIR: str = "./data/uploads"
    STATIC_DIR: str = "./data/static"

    # Redis (docker-friendly default)
    REDIS_URL: str = "redis://redis:6379/0"

    # Renders
    RENDER_TEMPLATE_MP4: str = "./data/static/templates/template.mp4"
    RENDER_OUTPUT_DIR: str = "./data/renders"

    # Do not require a .env file inside the container; rely on env vars.
    # Local dev can still use pydantic-settings to load .env if present.
    model_config = ConfigDict(case_sensitive=True)

    def __init__(self, **data):
        super().__init__(**data)
        if not self.DATABASE_URL:
            self.DATABASE_URL = (
                f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )


settings = Settings()
