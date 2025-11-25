from sqlalchemy import Column, String, Boolean, DateTime, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.database import BaseModel


class Client(BaseModel):
    """
    Client/Tenant model for multi-tenant support.
    Each client represents a company using the AI voice agent platform.
    """
    __tablename__ = "clients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    
    # Contact info
    billing_email = Column(String(255), nullable=True)
    contact_name = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    
    # Stripe integration (display-only for now)
    stripe_customer_id = Column(String(255), nullable=True)
    
    # Transfer configuration (JSON for flexibility)
    # Example: {"high_did": "+1234567890", "mid_did": "+1234567891", "low_did": "+1234567892"}
    transfer_config = Column(JSON, default={})
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Notes/description
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    agents = relationship("Agent", back_populates="client", lazy="dynamic")
    phone_numbers = relationship("PhoneNumber", back_populates="client", lazy="dynamic")
    call_records = relationship("CallRecord", back_populates="client", lazy="dynamic")
    dnc_entries = relationship("DNCEntry", back_populates="client", lazy="dynamic")
    users = relationship("User", back_populates="client", lazy="dynamic")
    
    def __repr__(self):
        return f"<Client {self.name} ({self.slug})>"

