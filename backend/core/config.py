"""
Application Configuration Module
Centralized configuration management using environment variables
"""
import os
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "InstaBiz Industrial ERP"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    
    # Database - PostgreSQL
    DATABASE_URL: str = "postgresql+asyncpg://erp_user:erp_secure_password@localhost:5432/adhesive_erp"
    
    # Security
    JWT_SECRET: str = "adhesive-erp-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    
    # API
    API_V1_PREFIX: str = "/api"
    
    # CORS
    CORS_ORIGINS: str = "*"
    
    # File Storage
    UPLOAD_DIR: str = "/tmp/uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # External Services
    EMERGENT_LLM_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Export commonly used settings
settings = get_settings()
