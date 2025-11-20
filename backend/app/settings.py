"""Application configuration and settings."""
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Union
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    DATABASE_URL: str = "postgresql://eas_user:eas_password@localhost:5433/alexandria_eas"
    
    # API Keys (optional)
    FIRMS_API_KEY: str = ""
    WMATA_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    
    # LLM Configuration
    MODEL_NAME: str = "llama3.2:3b-instruct-q4"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OPENAI_MODEL: str = "gpt-3.5-turbo"  # Valid OpenAI model names: gpt-3.5-turbo, gpt-4, gpt-4-turbo, gpt-4o, gpt-4o-mini
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    
    # Application Settings
    TEST_MODE: bool = True  # Set to True for Virginia-wide alerts (more alerts for testing)
    REFRESH_INTERVAL_SECONDS: int = 30
    LOG_LEVEL: str = "INFO"
    
    # Authentication Settings
    SECRET_KEY: str = "your-secret-key-change-in-production"  # Should be in .env
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
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


# Calculate .env file paths - check both root and backend
_settings_file = os.path.abspath(__file__)  # backend/app/settings.py
_settings_dir = os.path.dirname(_settings_file)  # backend/app
_backend_dir = os.path.dirname(_settings_dir)  # backend
_project_root = os.path.dirname(_backend_dir)  # project root
_root_env_path = os.path.join(_project_root, ".env")
_backend_env_path = os.path.join(_backend_dir, ".env")

# Prefer root .env, fallback to backend .env
_env_file_path = None
if os.path.exists(_root_env_path):
    _env_file_path = _root_env_path
    print(f"INFO: Loading .env file from root: {_root_env_path}")
elif os.path.exists(_backend_env_path):
    _env_file_path = _backend_env_path
    print(f"INFO: Loading .env file from backend: {_backend_env_path}")
    print(f"WARNING: Consider moving .env to project root for consistency")
else:
    print(f"WARNING: .env file not found at root ({_root_env_path}) or backend ({_backend_env_path})")

# Instantiate Settings with the env_file path
# Pass _env_file parameter to BaseSettings.__init__ to load the .env file
settings = Settings(_env_file=_env_file_path if _env_file_path else None)

# Debug: Check what was actually loaded
import os as os_module
_env_openai_key = os_module.getenv("OPENAI_API_KEY", "")
print(f"DEBUG: OPENAI_API_KEY from os.getenv: {'SET' if _env_openai_key else 'NOT SET'} (length: {len(_env_openai_key)})")
print(f"DEBUG: settings.OPENAI_API_KEY value: {'SET' if settings.OPENAI_API_KEY else 'NOT SET'} (length: {len(settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else 0})")
if settings.OPENAI_API_KEY:
    _key_preview = settings.OPENAI_API_KEY[:7] + "..." + settings.OPENAI_API_KEY[-4:] if len(settings.OPENAI_API_KEY) > 11 else "***"
    print(f"INFO: OpenAI API key loaded: {_key_preview}")
else:
    print("WARNING: OpenAI API key not set - will use Ollama for classification")
    if _env_file_path and os.path.exists(_env_file_path):
        print(f"DEBUG: Checking .env file content...")
        try:
            with open(_env_file_path, 'r') as f:
                lines = f.readlines()
                for i, line in enumerate(lines, 1):
                    if 'OPENAI' in line.upper() or 'API' in line.upper():
                        # Mask the key but show the line structure
                        masked_line = line.strip()
                        if '=' in masked_line:
                            parts = masked_line.split('=', 1)
                            if len(parts) == 2 and len(parts[1]) > 0:
                                masked_line = f"{parts[0]}=***{len(parts[1])} chars***"
                        print(f"DEBUG: Line {i} in .env: {masked_line}")
        except Exception as e:
            print(f"DEBUG: Could not read .env file: {e}")

