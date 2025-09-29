import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # ICD-11 API Configuration - FIXED the base URL
    ICD11_BASE_URL: str = os.getenv("ICD11_BASE_URL", "https://id.who.int/icd/release/11/2024-01")
    ICD11_CLIENT_ID: str = os.getenv("ICD11_CLIENT_ID")
    ICD11_CLIENT_SECRET: str = os.getenv("ICD11_CLIENT_SECRET")

    # NAMASTE Configuration (using local data, but keeping placeholders)
    NAMASTE_BASE_URL: str = "http://localhost:8000/static/namaste_data.json" # Example, adjust if you have a local server
    NAMASTE_API_KEY: str = os.getenv("NAMASTE_API_KEY") # Still useful for internal logic if needed

    # Cache configuration
    CACHE_TTL: int = 3600  # 1 hour

    # FHIR version
    FHIR_VERSION: str = "R4"

    # Database Configuration (if used)
    # REDIS_URL: str = os.getenv("REDIS_URL")
    # MONGODB_URL: str = os.getenv("MONGODB_URL")

    # Other API Configuration
    API_SECRET_KEY: str = os.getenv("API_SECRET_KEY", "your-secret-key-here")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

settings = Settings()