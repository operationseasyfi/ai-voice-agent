from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.database import BaseModel


class DNCEntry(BaseModel):
    """
    Do Not Call (DNC) list entry.
    Tracks callers who have requested to be removed from calling lists.
    """
    __tablename__ = "dnc_list"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False, index=True)
    
    # The phone number that should not be called
    phone_number = Column(String(50), nullable=False, index=True)
    
    # Reference to the call that triggered this DNC flag
    call_record_id = Column(UUID(as_uuid=True), ForeignKey("call_records.id"), nullable=True)
    
    # Reason for DNC (detected phrase or manual entry)
    reason = Column(Text, nullable=True)
    
    # Detection method
    # "auto" = AI detected DNC phrase during call
    # "manual" = Manually added by admin
    # "import" = Imported from external list
    detection_method = Column(String(50), default="auto")
    
    # The exact phrase detected (if auto)
    detected_phrase = Column(Text, nullable=True)
    
    # Who added this entry (if manual)
    added_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    flagged_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    client = relationship("Client", back_populates="dnc_entries")
    call_record = relationship("CallRecord", back_populates="dnc_entry")
    
    def __repr__(self):
        return f"<DNCEntry {self.phone_number} (client={self.client_id})>"
    
    def to_export_dict(self) -> dict:
        """Return dict suitable for CSV export"""
        return {
            "phone_number": self.phone_number,
            "reason": self.reason or "",
            "detection_method": self.detection_method,
            "detected_phrase": self.detected_phrase or "",
            "flagged_at": self.flagged_at.isoformat() if self.flagged_at else ""
        }

