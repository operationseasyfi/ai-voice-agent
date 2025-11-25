from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # SignalWire
    SIGNALWIRE_PROJECT_ID: str
    SIGNALWIRE_API_TOKEN: str
    SIGNALWIRE_SPACE_URL: str
    SIGNALWIRE_SIGNING_KEY: str

    # ELEVEN LABS
    ELEVEN_LABS_VOICE_ID: str = 'Gqe8GJJLg3haJkTwYj2L'
    
    # OCC CRM (Optional - for future use)
    OCC_CRM_API_URL: Optional[str] = None
    OCC_CRM_API_KEY: Optional[str] = None
    
    # 3-Tier Transfer Routing
    # High tier: Total unsecured debt >= $35,000
    QUEUE_HIGH_DID: Optional[str] = None
    # Mid tier: Total unsecured debt $10,000 - $34,999
    QUEUE_MID_DID: Optional[str] = None
    # Low tier: Total unsecured debt < $10,000
    QUEUE_LOW_DID: Optional[str] = None
    
    # Legacy 2-tier (backwards compatibility)
    QUEUE_A_DID: Optional[str] = None
    QUEUE_B_DID: Optional[str] = None
    
    # Twilio SIP Trunk
    TWILIO_SIP_TRUNK: Optional[str] = None
    TWILIO_SIP_USERNAME: Optional[str] = None
    TWILIO_SIP_PASSWORD: Optional[str] = None
    TWILIO_SIP_DOMAIN: Optional[str] = None
    
    # App
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    WEBHOOK_BASE_URL: Optional[str] = None
    DEBUG: bool = False
    
    # Database components
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_NAME: str = "ai_voice_agent"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Authentication
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256" 
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 180
    
    # Testing
    DISABLE_AGENT_AUTH: bool = False
    
    @property
    def DATABASE_URL(self) -> str:
        """Construct database URL from components."""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """Construct async database URL for SQLAlchemy."""
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra env vars

settings = Settings()
