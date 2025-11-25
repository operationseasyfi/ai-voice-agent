from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum
from app.database import BaseModel


class PhoneNumberType(str, enum.Enum):
    """Type of phone number"""
    AI_INBOUND = "ai_inbound"           # Inbound number for AI agent
    TRANSFER_HIGH = "transfer_high"     # Transfer destination for $35K+ debt
    TRANSFER_MID = "transfer_mid"       # Transfer destination for $10K-$35K debt
    TRANSFER_LOW = "transfer_low"       # Transfer destination for <$10K debt
    OUTBOUND = "outbound"               # Outbound calling number


class PhoneNumber(BaseModel):
    """
    Phone number model - tracks all phone numbers assigned to clients.
    Includes both AI inbound numbers and transfer destination numbers.
    """
    __tablename__ = "phone_numbers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False, index=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=True, index=True)
    
    # Phone number details
    number = Column(String(50), nullable=False, index=True)
    friendly_name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    
    # Type of number
    number_type = Column(
        Enum(PhoneNumberType),
        default=PhoneNumberType.AI_INBOUND,
        nullable=False
    )
    
    # SignalWire reference
    signalwire_sid = Column(String(255), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Usage tracking
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    total_calls = Column(String, default="0")  # Stored as string for large numbers
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    client = relationship("Client", back_populates="phone_numbers")
    agent = relationship("Agent", back_populates="phone_numbers")
    
    def __repr__(self):
        return f"<PhoneNumber {self.number} ({self.number_type.value})>"
    
    @property
    def formatted_number(self) -> str:
        """Return formatted phone number for display"""
        # Remove +1 prefix if present and format
        num = self.number.replace("+1", "").replace("-", "").replace(" ", "")
        if len(num) == 10:
            return f"({num[:3]}) {num[3:6]}-{num[6:]}"
        return self.number

