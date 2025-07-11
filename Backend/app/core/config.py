from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Database settings
    database_url: str = "postgresql://research_user:research_password_123@localhost:5432/research_assistant_db"
    
    # Redis settings  
    redis_url: str = "redis://localhost:6379"
    
    # API settings
    secret_key: str = "dev-secret-key-change-in-production"
    api_v1_str: str = "/api/v1"
    project_name: str = "Research Assistant"
    
    # CORS settings
    allowed_hosts: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    class Config:
        env_file = "../.env"
        extra = "ignore"  # Ignore extra fields from .env file

# Create global settings instance
settings = Settings()