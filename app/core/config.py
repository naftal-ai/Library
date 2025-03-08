from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any, List
from functools import lru_cache


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Library Management System API"
    
    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # MySQL connection
    MYSQL_USER: str
    MYSQL_PASSWORD: str
    MYSQL_SERVER: str
    MYSQL_PORT: str = "3306"
    MYSQL_DB: str
    
    # Admin user
    FIRST_SUPERUSER: str
    FIRST_SUPERUSER_PASSWORD: str
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = []
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
