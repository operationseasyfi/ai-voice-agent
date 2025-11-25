from sqlalchemy import Column, String, Boolean, DateTime, JSON, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.database import BaseModel


class Agent(BaseModel):
    """
    AI Agent model - represents an individual AI voice agent.
    Each client can have multiple agents with different configurations.
    """
    __tablename__ = "agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False, index=True)
    
    # Agent identity
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Voice configuration (JSON for flexibility)
    # Example: {"voice": "elevenlabs.rachel", "speed": 1.0, "language": "en-US"}
    voice_config = Column(JSON, default={
        "voice": "elevenlabs.rachel:eleven_flash_v2_5",
        "language": "en-US",
        "speed": 1.0
    })
    
    # Prompt/personality configuration
    # Example: {"personality": "Professional loan specialist", "script_steps": [...]}
    prompt_config = Column(JSON, default={})
    
    # Transfer routing config (can override client defaults)
    # Example: {"high_threshold": 35000, "mid_threshold": 10000}
    routing_config = Column(JSON, default={
        "high_threshold": 35000,
        "mid_threshold": 10000
    })
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Statistics cache (updated periodically)
    stats_cache = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    client = relationship("Client", back_populates="agents")
    call_records = relationship("CallRecord", back_populates="agent", lazy="dynamic")
    phone_numbers = relationship("PhoneNumber", back_populates="agent", lazy="dynamic")
    
    def __repr__(self):
        return f"<Agent {self.name} (client={self.client_id})>"

