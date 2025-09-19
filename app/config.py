from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # SignalWire
    SIGNALWIRE_PROJECT_ID: str
    SIGNALWIRE_API_TOKEN: str
    SIGNALWIRE_SPACE_URL: str
    
    # OCC CRM
    OCC_CRM_API_URL: str
    OCC_CRM_API_KEY: str
    
    # 3CX Transfer
    QUEUE_A_DID: str
    QUEUE_B_DID: str
    TWILIO_SIP_TRUNK: str
    
    # Twilio SIP Credentials
    TWILIO_SIP_USERNAME: str
    TWILIO_SIP_PASSWORD: str
    TWILIO_SIP_DOMAIN: str
    
    # App
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    WEBHOOK_BASE_URL: str
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"

settings = Settings()