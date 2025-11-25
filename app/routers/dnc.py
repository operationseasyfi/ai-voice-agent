from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import Optional
from uuid import UUID
from datetime import date, datetime
import csv
import io

from app.database import get_db
from app.models.dnc import DNCEntry
from app.auth.dependencies import get_current_active_user
from app.models.models import User

router = APIRouter()


@router.get("/")
async def list_dnc_entries(
    from_date: Optional[date] = Query(None, description="Start date"),
    to_date: Optional[date] = Query(None, description="End date"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List DNC (Do Not Call) entries for the current user's client.
    """
    filters = []
    
    # Client filtering
    if not current_user.is_admin() and current_user.client_id:
        filters.append(DNCEntry.client_id == current_user.client_id)
    
    # Date filters
    if from_date:
        start_datetime = datetime.combine(from_date, datetime.min.time())
        filters.append(DNCEntry.flagged_at >= start_datetime)
    
    if to_date:
        end_datetime = datetime.combine(to_date, datetime.max.time())
        filters.append(DNCEntry.flagged_at <= end_datetime)
    
    # Count total
    count_query = select(func.count(DNCEntry.id))
    if filters:
        count_query = count_query.where(and_(*filters))
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0
    
    # Get entries
    query = select(DNCEntry).order_by(DNCEntry.flagged_at.desc()).offset(skip).limit(limit)
    if filters:
        query = query.where(and_(*filters))
    
    result = await db.execute(query)
    entries = result.scalars().all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "dnc_entries": [
            {
                "id": str(e.id),
                "phone_number": e.phone_number,
                "reason": e.reason,
                "detection_method": e.detection_method,
                "detected_phrase": e.detected_phrase,
                "call_record_id": str(e.call_record_id) if e.call_record_id else None,
                "flagged_at": e.flagged_at.isoformat() if e.flagged_at else None
            }
            for e in entries
        ]
    }


@router.get("/stats")
async def get_dnc_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get DNC statistics for the current user's client.
    """
    filters = []
    
    if not current_user.is_admin() and current_user.client_id:
        filters.append(DNCEntry.client_id == current_user.client_id)
    
    # Total count
    total_query = select(func.count(DNCEntry.id))
    if filters:
        total_query = total_query.where(and_(*filters))
    total_result = await db.execute(total_query)
    total = total_result.scalar() or 0
    
    # Count by detection method
    method_query = select(
        DNCEntry.detection_method,
        func.count(DNCEntry.id)
    ).group_by(DNCEntry.detection_method)
    if filters:
        method_query = method_query.where(and_(*filters))
    method_result = await db.execute(method_query)
    by_method = {row[0]: row[1] for row in method_result}
    
    # Today's count
    today_start = datetime.combine(date.today(), datetime.min.time())
    today_filters = filters + [DNCEntry.flagged_at >= today_start]
    today_query = select(func.count(DNCEntry.id)).where(and_(*today_filters))
    today_result = await db.execute(today_query)
    today_count = today_result.scalar() or 0
    
    return {
        "total": total,
        "today": today_count,
        "by_method": by_method
    }


@router.get("/export")
async def export_dnc_csv(
    from_date: Optional[date] = Query(None, description="Start date"),
    to_date: Optional[date] = Query(None, description="End date"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Export DNC list as CSV file.
    """
    filters = []
    
    # Client filtering
    if not current_user.is_admin() and current_user.client_id:
        filters.append(DNCEntry.client_id == current_user.client_id)
    
    # Date filters
    if from_date:
        start_datetime = datetime.combine(from_date, datetime.min.time())
        filters.append(DNCEntry.flagged_at >= start_datetime)
    
    if to_date:
        end_datetime = datetime.combine(to_date, datetime.max.time())
        filters.append(DNCEntry.flagged_at <= end_datetime)
    
    # Get all entries
    query = select(DNCEntry).order_by(DNCEntry.flagged_at.desc())
    if filters:
        query = query.where(and_(*filters))
    
    result = await db.execute(query)
    entries = result.scalars().all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        "Phone Number",
        "Reason",
        "Detection Method",
        "Detected Phrase",
        "Flagged At"
    ])
    
    # Data rows
    for entry in entries:
        writer.writerow([
            entry.phone_number,
            entry.reason or "",
            entry.detection_method or "",
            entry.detected_phrase or "",
            entry.flagged_at.isoformat() if entry.flagged_at else ""
        ])
    
    output.seek(0)
    
    # Generate filename
    filename = f"dnc_list_{date.today().isoformat()}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/{entry_id}")
async def get_dnc_entry(
    entry_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get details for a specific DNC entry.
    """
    result = await db.execute(select(DNCEntry).where(DNCEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    
    if not entry:
        raise HTTPException(status_code=404, detail="DNC entry not found")
    
    # Check access
    if not current_user.is_admin() and entry.client_id != current_user.client_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "id": str(entry.id),
        "client_id": str(entry.client_id),
        "phone_number": entry.phone_number,
        "call_record_id": str(entry.call_record_id) if entry.call_record_id else None,
        "reason": entry.reason,
        "detection_method": entry.detection_method,
        "detected_phrase": entry.detected_phrase,
        "flagged_at": entry.flagged_at.isoformat() if entry.flagged_at else None,
        "created_at": entry.created_at.isoformat() if entry.created_at else None
    }

