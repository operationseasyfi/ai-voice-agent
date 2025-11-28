from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_, func
from typing import Optional
from uuid import UUID
from datetime import date, datetime
import csv
import io

from app.database import get_db
from app.models.call_records import CallRecord, DisconnectionReason, TransferTier
from app.auth.dependencies import get_current_active_user
from app.models.models import User
from app.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/")
async def get_call_history(
    from_date: Optional[date] = Query(None, description="Start date"),
    to_date: Optional[date] = Query(None, description="End date"),
    agent_id: Optional[UUID] = Query(None, description="Filter by agent"),
    status: Optional[str] = Query(None, description="Filter by status"),
    disconnection_reason: Optional[str] = Query(None, description="Filter by disconnection reason"),
    transfer_tier: Optional[str] = Query(None, description="Filter by transfer tier (high, mid, low)"),
    is_dnc: Optional[bool] = Query(None, description="Filter DNC flagged calls"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get call history with comprehensive filtering.
    """
    filters = []
    
    # Client filtering for non-admin users
    if not current_user.is_admin() and current_user.client_id:
        filters.append(CallRecord.client_id == current_user.client_id)
    
    # Date filters
    if from_date:
        start_datetime = datetime.combine(from_date, datetime.min.time())
        filters.append(CallRecord.created_at >= start_datetime)
    
    if to_date:
        end_datetime = datetime.combine(to_date, datetime.max.time())
        filters.append(CallRecord.created_at <= end_datetime)
    
    # Agent filter
    if agent_id:
        filters.append(CallRecord.agent_id == agent_id)
    
    # Status filter
    if status:
        filters.append(CallRecord.status == status)
    
    # Disconnection reason filter
    if disconnection_reason:
        try:
            reason_enum = DisconnectionReason(disconnection_reason)
            filters.append(CallRecord.disconnection_reason == reason_enum)
        except ValueError:
            pass
    
    # Transfer tier filter
    if transfer_tier:
        try:
            tier_enum = TransferTier(transfer_tier)
            filters.append(CallRecord.transfer_tier == tier_enum)
        except ValueError:
            pass
    
    # DNC filter
    if is_dnc is not None:
        filters.append(CallRecord.is_dnc_flagged == is_dnc)
    
    # Count total
    count_query = select(func.count(CallRecord.id))
    if filters:
        count_query = count_query.where(and_(*filters))
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0
    
    # Get calls - handle missing columns gracefully
    try:
        query = select(CallRecord).order_by(desc(CallRecord.created_at)).offset(skip).limit(limit)
        if filters:
            query = query.where(and_(*filters))
        
        result = await db.execute(query)
        calls = result.scalars().all()
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "calls": [call.to_dashboard_dict() for call in calls]
        }
    except Exception as e:
        error_msg = str(e)
        if "does not exist" in error_msg.lower() or "undefinedcolumn" in error_msg.lower():
            logger.error(f"Database columns missing - migrations need to run: {error_msg}")
            # Return empty result with warning instead of crashing
            return {
                "total": 0,
                "skip": skip,
                "limit": limit,
                "calls": [],
                "error": "Database migration required. Please contact support."
            }
        # Re-raise other exceptions
        raise


@router.get("/live/concurrent")
async def get_concurrent_calls(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get count of currently active/in-progress calls.
    Note: This is a simplified implementation. In production, use Redis for real-time tracking.
    """
    filters = [
        CallRecord.status == "in_progress"
    ]
    
    if not current_user.is_admin() and current_user.client_id:
        filters.append(CallRecord.client_id == current_user.client_id)
    
    result = await db.execute(
        select(func.count(CallRecord.id)).where(and_(*filters))
    )
    count = result.scalar() or 0
    
    return {
        "concurrent_calls": count,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/{call_id}")
async def get_call_details(
    call_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get detailed information for a specific call.
    """
    result = await db.execute(select(CallRecord).where(CallRecord.id == call_id))
    call = result.scalar_one_or_none()
    
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    # Check access
    if not current_user.is_admin() and call.client_id != current_user.client_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "id": str(call.id),
        "call_sid": call.call_sid,
        "client_id": str(call.client_id) if call.client_id else None,
        "agent_id": str(call.agent_id) if call.agent_id else None,
        "from_number": call.from_number,
        "to_number": call.to_number,
        "direction": call.direction,
        "status": call.status,
        "duration": call.duration,
        "duration_formatted": CallRecord._format_duration(call.duration),
        "disconnection_reason": call.disconnection_reason.value if call.disconnection_reason else None,
        "transfer_tier": call.transfer_tier.value if call.transfer_tier else None,
        "transfer_did": call.transfer_did,
        "transfer_success": call.transfer_success,
        "is_dnc_flagged": call.is_dnc_flagged,
        "dnc_phrase_detected": call.dnc_phrase_detected,
        "lead_name": call.lead_name,
        "loan_amount": call.loan_amount,
        "funds_purpose": call.funds_purpose,
        "employment_status": call.employment_status,
        "credit_card_debt": call.credit_card_debt,
        "personal_loan_debt": call.personal_loan_debt,
        "other_debt": call.other_debt,
        "total_debt": call.total_debt,
        "monthly_income": call.monthly_income,
        "intake_data": call.intake_data,
        "recording_url": call.recording_url,
        "transcript": call.transcript,
        "conversation_summary": call.conversation_summary,
        "steps_completed": call.steps_completed,
        "call_started_at": call.call_started_at.isoformat() if call.call_started_at else None,
        "call_ended_at": call.call_ended_at.isoformat() if call.call_ended_at else None,
        "created_at": call.created_at.isoformat() if call.created_at else None
    }


@router.get("/{call_id}/recording")
async def get_call_recording(
    call_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get recording URL for a call.
    In production, this would proxy the actual audio file.
    """
    result = await db.execute(select(CallRecord).where(CallRecord.id == call_id))
    call = result.scalar_one_or_none()
    
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    # Check access
    if not current_user.is_admin() and call.client_id != current_user.client_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not call.recording_url:
        raise HTTPException(status_code=404, detail="No recording available for this call")
    
    return {
        "call_id": str(call.id),
        "recording_url": call.recording_url,
        "duration": call.recording_duration
    }


@router.get("/export/csv")
async def export_calls_csv(
    from_date: Optional[date] = Query(None, description="Start date"),
    to_date: Optional[date] = Query(None, description="End date"),
    agent_id: Optional[UUID] = Query(None, description="Filter by agent"),
    status: Optional[str] = Query(None, description="Filter by status"),
    transfer_tier: Optional[str] = Query(None, description="Filter by transfer tier"),
    is_dnc: Optional[bool] = Query(None, description="Filter DNC flagged calls"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Export call records as CSV file.
    Single-click download for data analysis.
    """
    filters = []
    
    # Client filtering for non-admin users
    if not current_user.is_admin() and current_user.client_id:
        filters.append(CallRecord.client_id == current_user.client_id)
    
    # Date filters
    if from_date:
        start_datetime = datetime.combine(from_date, datetime.min.time())
        filters.append(CallRecord.created_at >= start_datetime)
    
    if to_date:
        end_datetime = datetime.combine(to_date, datetime.max.time())
        filters.append(CallRecord.created_at <= end_datetime)
    
    # Optional filters
    if agent_id:
        filters.append(CallRecord.agent_id == agent_id)
    
    if status:
        filters.append(CallRecord.status == status)
    
    if transfer_tier:
        try:
            tier_enum = TransferTier(transfer_tier)
            filters.append(CallRecord.transfer_tier == tier_enum)
        except ValueError:
            pass
    
    if is_dnc is not None:
        filters.append(CallRecord.is_dnc_flagged == is_dnc)
    
    # Get all matching calls (limit to 10000 to prevent OOM)
    query = select(CallRecord).order_by(desc(CallRecord.created_at)).limit(10000)
    if filters:
        query = query.where(and_(*filters))
    
    result = await db.execute(query)
    calls = result.scalars().all()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header row
    writer.writerow([
        "Call ID", "Date/Time", "From Number", "To Number", "Lead Name",
        "Duration (sec)", "Status", "Disconnect Reason", "Transfer Tier",
        "Transfer Success", "Total Debt", "Credit Card Debt", "Personal Loan Debt",
        "Monthly Income", "Employment Status", "DNC Flagged", "DNC Phrase",
        "Recording URL"
    ])
    
    # Data rows
    for call in calls:
        writer.writerow([
            call.call_sid or str(call.id),
            call.call_started_at.isoformat() if call.call_started_at else (call.created_at.isoformat() if call.created_at else ""),
            call.from_number or "",
            call.to_number or "",
            call.lead_name or "",
            call.duration or 0,
            call.status or "",
            call.disconnection_reason.value if call.disconnection_reason else "",
            call.transfer_tier.value if call.transfer_tier else "",
            "Yes" if call.transfer_success else "No",
            call.total_debt or 0,
            call.credit_card_debt or 0,
            call.personal_loan_debt or 0,
            call.monthly_income or "",
            call.employment_status or "",
            "Yes" if call.is_dnc_flagged else "No",
            call.dnc_phrase_detected or "",
            call.recording_url or ""
        ])
    
    output.seek(0)
    
    # Generate filename
    date_suffix = f"{from_date or 'all'}_to_{to_date or 'all'}"
    filename = f"call_records_{date_suffix}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
