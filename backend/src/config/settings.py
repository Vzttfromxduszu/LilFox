from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = "sqlite:///./app.db"
    
    # JWT settings
    SECRET_KEY: str = "your-secret-key-change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["http://localhost", "http://localhost:3000", "http://localhost:5173"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
