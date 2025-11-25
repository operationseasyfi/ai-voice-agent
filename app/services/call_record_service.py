"""
Call Record Service - Handles saving call data to the database
"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime
import logging

from app.database import AsyncSessionLocal
from app.models.call_records import CallRecord, DisconnectionReason, TransferTier
from app.models.dnc import DNCEntry
from app.services.recording_service import recording_service

logger = logging.getLogger(__name__)


class CallRecordService:
    """
    Service for managing call records in the database.
    """
    
    async def save_call_record(
        self,
        call_sid: str,
        intake_state: Dict[str, Any],
        client_id: Optional[UUID] = None,
        agent_id: Optional[UUID] = None
    ) -> Optional[CallRecord]:
        """
        Save a completed call record to the database.
        
        Args:
            call_sid: SignalWire call SID
            intake_state: Collected intake data from the call
            client_id: Optional client ID for multi-tenant filtering
            agent_id: Optional agent ID that handled the call
            
        Returns:
            Created CallRecord or None on error
        """
        async with AsyncSessionLocal() as db:
            try:
                # Determine disconnection reason
                disconnection_reason = self._determine_disconnection_reason(intake_state)
                
                # Determine transfer tier
                transfer_tier = self._determine_transfer_tier(intake_state)
                
                # Create call record
                record = CallRecord(
                    call_sid=call_sid,
                    client_id=client_id,
                    agent_id=agent_id,
                    from_number=intake_state.get("caller_number", ""),
                    to_number=intake_state.get("to_number", ""),
                    direction="inbound",
                    status="completed",
                    
                    # Disconnection and transfer
                    disconnection_reason=disconnection_reason,
                    transfer_tier=transfer_tier,
                    transfer_did=intake_state.get("transfer_did"),
                    transfer_success=intake_state.get("transfer_initiated", False),
                    
                    # DNC flag
                    is_dnc_flagged=intake_state.get("is_dnc", False),
                    dnc_phrase_detected=intake_state.get("dnc_phrase"),
                    
                    # Intake data
                    lead_name=intake_state.get("lead_name"),
                    loan_amount=intake_state.get("loan_amount"),
                    funds_purpose=intake_state.get("funds_purpose"),
                    employment_status=intake_state.get("employment_status"),
                    credit_card_debt=intake_state.get("credit_card_debt", 0),
                    personal_loan_debt=intake_state.get("personal_loan_debt", 0),
                    other_debt=intake_state.get("other_debt", 0),
                    total_debt=intake_state.get("total_debt", 0),
                    monthly_income=intake_state.get("monthly_income"),
                    ssn_last_four=intake_state.get("ssn_last_four"),
                    
                    # Full JSON backup
                    intake_data=intake_state,
                    steps_completed=intake_state.get("answered", []),
                    
                    # Timestamps
                    call_started_at=datetime.utcnow(),
                    call_ended_at=datetime.utcnow()
                )
                
                db.add(record)
                await db.commit()
                await db.refresh(record)
                
                logger.info(f"✅ Saved call record {record.id} for call {call_sid}")
                
                # If DNC flagged, create DNC entry
                if intake_state.get("is_dnc", False):
                    await self._create_dnc_entry(
                        db, 
                        record,
                        client_id,
                        intake_state
                    )
                
                # Fetch recording URL asynchronously (non-blocking)
                await self._fetch_and_update_recording(db, record, call_sid)
                
                return record
                
            except Exception as e:
                logger.error(f"❌ Failed to save call record for {call_sid}: {str(e)}")
                await db.rollback()
                return None
    
    async def _fetch_and_update_recording(
        self,
        db: AsyncSession,
        record: CallRecord,
        call_sid: str
    ):
        """Fetch recording URL from SignalWire and update the record."""
        try:
            recording_info = await recording_service.get_call_recording(call_sid)
            
            if recording_info:
                record.recording_url = recording_info.get("recording_url")
                record.recording_duration = float(recording_info.get("duration", 0))
                record.duration = float(recording_info.get("duration", 0))
                await db.commit()
                logger.info(f"📼 Updated recording URL for call {call_sid}")
        except Exception as e:
            logger.warning(f"Failed to fetch recording for {call_sid}: {str(e)}")
    
    async def _create_dnc_entry(
        self,
        db: AsyncSession,
        call_record: CallRecord,
        client_id: Optional[UUID],
        intake_state: Dict[str, Any]
    ):
        """Create a DNC entry when DNC is detected."""
        try:
            dnc_entry = DNCEntry(
                client_id=client_id,
                phone_number=intake_state.get("caller_number", ""),
                call_record_id=call_record.id,
                reason="DNC phrase detected during call",
                detection_method="auto",
                detected_phrase=intake_state.get("dnc_phrase")
            )
            db.add(dnc_entry)
            await db.commit()
            logger.info(f"🚫 Created DNC entry for {dnc_entry.phone_number}")
        except Exception as e:
            logger.error(f"Failed to create DNC entry: {str(e)}")
    
    def _determine_disconnection_reason(self, intake_state: Dict[str, Any]) -> DisconnectionReason:
        """Determine the disconnection reason from intake state."""
        if intake_state.get("is_dnc", False):
            return DisconnectionReason.DNC_DETECTED
        if intake_state.get("transfer_initiated", False):
            return DisconnectionReason.TRANSFERRED
        if intake_state.get("error"):
            return DisconnectionReason.ERROR
        # Default to agent hangup (AI ended the call)
        return DisconnectionReason.AGENT_HANGUP
    
    def _determine_transfer_tier(self, intake_state: Dict[str, Any]) -> TransferTier:
        """Determine the transfer tier from intake state."""
        tier = intake_state.get("transfer_tier", "none")
        try:
            return TransferTier(tier) if tier else TransferTier.NONE
        except ValueError:
            return TransferTier.NONE
    
    async def update_call_duration(
        self,
        call_sid: str,
        duration: float,
        status: Optional[str] = None
    ):
        """Update call duration after call ends."""
        async with AsyncSessionLocal() as db:
            try:
                from sqlalchemy import select
                result = await db.execute(
                    select(CallRecord).where(CallRecord.call_sid == call_sid)
                )
                record = result.scalar_one_or_none()
                
                if record:
                    record.duration = duration
                    if status:
                        record.status = status
                    record.call_ended_at = datetime.utcnow()
                    await db.commit()
                    logger.info(f"Updated duration for call {call_sid}: {duration}s")
            except Exception as e:
                logger.error(f"Failed to update call duration: {str(e)}")


# Singleton instance
call_record_service = CallRecordService()

