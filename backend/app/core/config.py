from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl
from typing import List, Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "TCB-MONGO" 
    SENTRY_DSN: Optional[str] = None
    ENVIRONMENT: str = "local"

    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @property
    def all_cors_origins(self) -> List[str]:
        return [str(o) for o in self.BACKEND_CORS_ORIGINS]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()