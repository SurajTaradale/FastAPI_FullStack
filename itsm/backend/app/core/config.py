import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Cache
    CACHE_TYPE: str = "diskcache"
    REDIS_URL: str = "redis://localhost:6379/0"
    DISKCACHE_DIR: str = "/opt/helpdesk_app/itsm/cache"

    # JWT
    SECRET_KEY: str = "change-me-in-production-use-a-long-random-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # CORS - comma-separated list of allowed origins
    CORS_ORIGINS: str = "http://localhost:3000"

    # Database
    DATABASE_URL: str = "mysql+pymysql://otobo:pJDCvTgXthRkFSb4@localhost/otobo"

    class Config:
        env_file = ".env"

    def get_cors_origins(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

settings = Settings()
