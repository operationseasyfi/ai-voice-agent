from sqlalchemy import Column, String, Float, DateTime, JSON, Boolean, Text, ForeignKey, Integer, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum
from app.database import BaseModel


class DisconnectionReason(str, enum.Enum):
    """Reason for call disconnection"""
    TRANSFERRED = "transferred"           # Successfully transferred to agent
    CALLER_HANGUP = "caller_hangup"       # Caller hung up
    AGENT_HANGUP = "agent_hangup"         # AI agent ended call
    DNC_DETECTED = "dnc_detected"         # DNC phrase detected, call ended
    ERROR = "error"                       # System error
    TIMEOUT = "timeout"                   # Call timed out
    NO_ANSWER = "no_answer"               # No answer from transfer destination
    UNKNOWN = "unknown"                   # Unknown reason


class TransferTier(str, enum.Enum):
    """Transfer destination tier based on debt amount"""
    HIGH = "high"    # >= $35,000
    MID = "mid"      # $10,000 - $34,999
    LOW = "low"      # < $10,000
    NONE = "none"    # No transfer attempted


class CallRecord(BaseModel):
    """
    Call record model - tracks all calls with full intake data.
    Multi-tenant with client_id for data isolation.
    """
    __tablename__ = "call_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Multi-tenant fields
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=True, index=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=True, index=True)
    
    # SignalWire call identifiers
    call_sid = Column(String(255), unique=True, index=True)
    
    # Call details
    from_number = Column(String(50), index=True)
    to_number = Column(String(50))
    direction = Column(String(20), default="inbound")
    status = Column(String(50))  # completed, failed, etc.
    
    # Duration
    duration = Column(Float, default=0.0)  # Duration in seconds
    
    # Disconnection tracking
    disconnection_reason = Column(
        Enum(DisconnectionReason),
        default=DisconnectionReason.UNKNOWN
    )
    
    # Transfer information
    transfer_tier = Column(
        Enum(TransferTier),
        default=TransferTier.NONE
    )
    transfer_did = Column(String(50), nullable=True)  # The DID transferred to
    transfer_success = Column(Boolean, default=False)
    transfer_duration = Column(Float, default=0.0)  # Time spent on transfer
    
    # Lost transfers tracking
    transfer_attempt_time = Column(DateTime(timezone=True), nullable=True)  # When transfer was attempted
    transfer_wait_duration = Column(Float, default=0.0)  # How long caller waited
    transfer_answered = Column(Boolean, default=False)  # Whether closer answered
    
    # Disqualification tracking
    disqualification_reason = Column(String(255), nullable=True)  # Why caller was ineligible
    
    # DNC flagging
    is_dnc_flagged = Column(Boolean, default=False)
    dnc_phrase_detected = Column(Text, nullable=True)
    
    # Concurrent call tracking
    concurrent_calls_at_start = Column(Integer, default=0)
    
    # Intake Data - Caller info
    lead_name = Column(String(255), nullable=True)
    
    # Intake Data - Loan request
    loan_amount = Column(Float, nullable=True)
    funds_purpose = Column(Text, nullable=True)
    employment_status = Column(String(100), nullable=True)
    
    # Intake Data - Debt information
    credit_card_debt = Column(Float, default=0.0)
    personal_loan_debt = Column(Float, default=0.0)
    other_debt = Column(Float, default=0.0)
    total_debt = Column(Float, default=0.0)
    
    # Intake Data - Income and verification
    monthly_income = Column(Float, nullable=True)
    ssn_last_four = Column(String(4), nullable=True)
    
    # Full intake data (JSON backup of all collected data)
    intake_data = Column(JSON, default={})
    
    # Recording and transcript
    recording_url = Column(Text, nullable=True)
    recording_duration = Column(Float, nullable=True)
    transcript = Column(Text, nullable=True)
    
    # AI conversation metadata
    conversation_summary = Column(Text, nullable=True)
    steps_completed = Column(JSON, default=[])  # List of completed intake steps
    
    # Timestamps
    call_started_at = Column(DateTime(timezone=True), nullable=True)
    call_ended_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    client = relationship("Client", back_populates="call_records")
    agent = relationship("Agent", back_populates="call_records")
    dnc_entry = relationship("DNCEntry", back_populates="call_record", uselist=False)
    
    def __repr__(self):
        return f"<CallRecord {self.call_sid} ({self.status})>"
    
    def calculate_total_debt(self):
        """Calculate and update total debt from component fields"""
        self.total_debt = (
            (self.credit_card_debt or 0) +
            (self.personal_loan_debt or 0) +
            (self.other_debt or 0)
        )
        return self.total_debt
    
    def determine_transfer_tier(self) -> TransferTier:
        """Determine transfer tier based on total debt"""
        total = self.total_debt or 0
        if total >= 35000:
            return TransferTier.HIGH
        elif total >= 10000:
            return TransferTier.MID
        else:
            return TransferTier.LOW
    
    def to_dashboard_dict(self) -> dict:
        """Return dict suitable for dashboard display"""
        return {
            "id": str(self.id),
            "call_sid": self.call_sid,
            "from_number": self.from_number,
            "to_number": self.to_number,
            "lead_name": self.lead_name or "Unknown",
            "duration": self.duration,
            "duration_formatted": self._format_duration(self.duration),
            "status": self.status,
            "disconnection_reason": self.disconnection_reason.value if self.disconnection_reason else "unknown",
            "transfer_tier": self.transfer_tier.value if self.transfer_tier else "none",
            "transfer_success": self.transfer_success,
            "transfer_answered": self.transfer_answered,
            "transfer_wait_duration": self.transfer_wait_duration,
            "is_dnc_flagged": self.is_dnc_flagged,
            "total_debt": self.total_debt,
            "recording_url": self.recording_url,
            "disqualification_reason": self.disqualification_reason,
            "call_started_at": self.call_started_at.isoformat() if self.call_started_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    @property
    def is_lost_transfer(self) -> bool:
        """Check if this call was a lost transfer (qualified but not answered)"""
        return (
            self.transfer_tier in [TransferTier.HIGH, TransferTier.MID, TransferTier.LOW] and
            self.transfer_tier != TransferTier.NONE and
            not self.transfer_answered and
            self.disconnection_reason in [DisconnectionReason.NO_ANSWER, DisconnectionReason.TIMEOUT, DisconnectionReason.CALLER_HANGUP]
        )
    
    @staticmethod
    def _format_duration(seconds: float) -> str:
        """Format duration in seconds to MM:SS or HH:MM:SS"""
        if not seconds:
            return "0:00"
        seconds = int(seconds)
        if seconds >= 3600:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}:{secs:02d}"
