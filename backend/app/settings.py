"""Application configuration and settings."""
from pydantic_settings import BaseSettings
from typing import List, Union
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    DATABASE_URL: str = "postgresql://eas_user:eas_password@localhost:5432/alexandria_eas"
    
    # API Keys (optional)
    FIRMS_API_KEY: str = ""
    WMATA_API_KEY: str = ""
    
    # LLM Configuration
    MODEL_NAME: str = "llama3.2:3b-instruct-q4"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    
    # Application Settings
    TEST_MODE: bool = False
    REFRESH_INTERVAL_SECONDS: int = 300
    LOG_LEVEL: str = "INFO"

    #OPENAI
    OPENAI_API_KEY: str = ""
    
    # CORS - can be a comma-separated string or list
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:3000,http://localhost:8000,http://127.0.0.1:8000,http://127.0.0.1:3000"
    
    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS_ORIGINS from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    # Geographic Configuration
    ALEXANDRIA_CENTER_LAT: float = 38.8048
    ALEXANDRIA_CENTER_LON: float = -77.0469
    ALEXANDRIA_BBOX: dict = {
        "minLon": -77.15,
        "minLat": 38.75,
        "maxLon": -77.00,
        "maxLat": 38.87
    }
    RADIUS_KM: int = 10
    
    # NWIS River Gauge Sites (Alexandria area)
    NWIS_SITES: List[str] = ["01652500", "01646500"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

