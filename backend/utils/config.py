import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # System
    PORT: int = int(os.environ.get("PORT", 8000))
    DEBUG: bool = os.environ.get("DEBUG", "False").lower() == "true"
    
    # GCP / Vertex AI
    GCP_PROJECT_ID: str = os.environ.get("GCP_PROJECT_ID", "")
    GCP_LOCATION: str = os.environ.get("GCP_LOCATION", "us-central1")
    
    # Auth
    SESSION_SECRET_KEY: str = os.environ.get("SESSION_SECRET_KEY", "prod-secret-key-change-me")
    GOOGLE_CLIENT_ID: str = os.environ.get("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.environ.get("GOOGLE_CLIENT_SECRET", "")
    
    # URLs
    BACKEND_URL: str = os.environ.get("BACKEND_URL", "http://localhost:8000")
    FRONTEND_URL: str = os.environ.get("FRONTEND_URL", "http://localhost:5173")
    
    @property
    def GOOGLE_REDIRECT_URI(self) -> str:
        return f"{self.BACKEND_URL}/auth/callback"

settings = Settings()
