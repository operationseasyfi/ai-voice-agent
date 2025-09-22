from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # SignalWire
    SIGNALWIRE_PROJECT_ID: str
    SIGNALWIRE_API_TOKEN: str
    SIGNALWIRE_SPACE_URL: str
    SIGNALWIRE_SIGNING_KEY: str
    
    # OCC CRM
    OCC_CRM_API_URL: str
    OCC_CRM_API_KEY: str
    
    # 3CX Transfer
    QUEUE_A_DID: str
    QUEUE_B_DID: str
    TWILIO_SIP_TRUNK: str
    
    # Twilio SIP Credentials (optional until Twilio integration is implemented)
    TWILIO_SIP_USERNAME: Optional[str] = None
    TWILIO_SIP_PASSWORD: Optional[str] = None
    TWILIO_SIP_DOMAIN: Optional[str] = None
    
    # App
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    WEBHOOK_BASE_URL: str
    DEBUG: bool = False
    
    # Testing
    DISABLE_AGENT_AUTH: bool = False  # Set to True for local testing
    
    class Config:
        env_file = ".env"

settings = Settings()