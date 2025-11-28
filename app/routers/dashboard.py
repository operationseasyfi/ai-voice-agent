from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import datetime, date, timedelta
from typing import Optional, List
from uuid import UUID

from app.database import get_db
from app.models.call_records import CallRecord, DisconnectionReason, TransferTier
from app.models.agent import Agent
from app.auth.dependencies import get_current_active_user
from app.models.models import User
from app.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats(
    from_date: Optional[date] = Query(None, description="Start date (defaults to today)"),
    to_date: Optional[date] = Query(None, description="End date (defaults to today)"),
    agent_id: Optional[UUID] = Query(None, description="Filter by specific agent"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get dashboard statistics for the current user's client.
    
    Returns:
    - total_calls: Total number of calls
    - successful_transfers: Number of successfully transferred calls
    - total_duration_minutes: Total call duration in minutes
    - avg_duration_seconds: Average call duration in seconds
    - dnc_count: Number of DNC flagged calls
    - calls_by_tier: Breakdown of calls by transfer tier
    """
    # Default to today if no dates provided
    if not from_date:
        from_date = date.today()
    if not to_date:
        to_date = date.today()
    
    # Convert dates to datetime for comparison
    start_datetime = datetime.combine(from_date, datetime.min.time())
    end_datetime = datetime.combine(to_date, datetime.max.time())
    
    # Build base query with client filtering
    base_filter = [
        CallRecord.created_at >= start_datetime,
        CallRecord.created_at <= end_datetime,
    ]
    
    # Add client filter for non-admin users
    if not current_user.is_admin() and current_user.client_id:
        base_filter.append(CallRecord.client_id == current_user.client_id)
    
    # Add agent filter if specified
    if agent_id:
        base_filter.append(CallRecord.agent_id == agent_id)
    
    # Total calls
    total_calls_result = await db.execute(
        select(func.count(CallRecord.id)).where(and_(*base_filter))
    )
    total_calls = total_calls_result.scalar() or 0
    
    # Successful transfers
    transfer_filter = base_filter + [CallRecord.transfer_success == True]
    transfers_result = await db.execute(
        select(func.count(CallRecord.id)).where(and_(*transfer_filter))
    )
    successful_transfers = transfers_result.scalar() or 0
    
    # Total and average duration
    duration_result = await db.execute(
        select(
            func.sum(CallRecord.duration),
            func.avg(CallRecord.duration)
        ).where(and_(*base_filter))
    )
    duration_row = duration_result.one()
    total_duration_seconds = duration_row[0] or 0
    avg_duration_seconds = duration_row[1] or 0
    
    # DNC count
    dnc_filter = base_filter + [CallRecord.is_dnc_flagged == True]
    dnc_result = await db.execute(
        select(func.count(CallRecord.id)).where(and_(*dnc_filter))
    )
    dnc_count = dnc_result.scalar() or 0
    
    # Calls by tier - handle case where column might not exist yet
    calls_by_tier = {
        "high": 0,
        "mid": 0,
        "low": 0,
        "none": 0
    }
    try:
        tier_result = await db.execute(
            select(
                CallRecord.transfer_tier,
                func.count(CallRecord.id)
            ).where(and_(*base_filter))
            .group_by(CallRecord.transfer_tier)
        )
        for row in tier_result:
            if row[0]:
                calls_by_tier[row[0].value] = row[1]
    except Exception as e:
        # If transfer_tier column doesn't exist, return empty tier breakdown
        logger.warning(f"transfer_tier column not found, returning empty breakdown: {e}")
    
    # Calls by disconnection reason - handle case where column might not exist yet
    calls_by_reason = {}
    try:
        reason_result = await db.execute(
            select(
                CallRecord.disconnection_reason,
                func.count(CallRecord.id)
            ).where(and_(*base_filter))
            .group_by(CallRecord.disconnection_reason)
        )
        for row in reason_result:
            if row[0]:
                calls_by_reason[row[0].value] = row[1]
    except Exception as e:
        # If disconnection_reason column doesn't exist, return empty reason breakdown
        logger.warning(f"disconnection_reason column not found, returning empty breakdown: {e}")
    
    return {
        "period": {
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat()
        },
        "total_calls": total_calls,
        "successful_transfers": successful_transfers,
        "transfer_rate": round((successful_transfers / total_calls * 100), 1) if total_calls > 0 else 0,
        "total_duration_minutes": round(total_duration_seconds / 60, 1),
        "avg_duration_seconds": round(avg_duration_seconds, 1),
        "avg_duration_formatted": _format_duration(avg_duration_seconds),
        "dnc_count": dnc_count,
        "calls_by_tier": calls_by_tier,
        "calls_by_reason": calls_by_reason
    }


@router.get("/agents-overview")
async def get_agents_overview(
    from_date: Optional[date] = Query(None, description="Start date (defaults to today)"),
    to_date: Optional[date] = Query(None, description="End date (defaults to today)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get overview stats for all agents belonging to the current user's client.
    """
    # Default to today if no dates provided
    if not from_date:
        from_date = date.today()
    if not to_date:
        to_date = date.today()
    
    start_datetime = datetime.combine(from_date, datetime.min.time())
    end_datetime = datetime.combine(to_date, datetime.max.time())
    
    # Get agents for the client
    agent_filter = [Agent.is_active == True]
    if not current_user.is_admin() and current_user.client_id:
        agent_filter.append(Agent.client_id == current_user.client_id)
    
    agents_result = await db.execute(
        select(Agent).where(and_(*agent_filter))
    )
    agents = agents_result.scalars().all()
    
    agent_stats = []
    for agent in agents:
        # Get stats for this agent
        call_filter = [
            CallRecord.agent_id == agent.id,
            CallRecord.created_at >= start_datetime,
            CallRecord.created_at <= end_datetime
        ]
        
        stats_result = await db.execute(
            select(
                func.count(CallRecord.id),
                func.sum(CallRecord.duration),
                func.count(CallRecord.id).filter(CallRecord.transfer_success == True)
            ).where(and_(*call_filter))
        )
        stats_row = stats_result.one()
        
        total_calls = stats_row[0] or 0
        total_duration = stats_row[1] or 0
        transfers = stats_row[2] or 0
        
        agent_stats.append({
            "id": str(agent.id),
            "name": agent.name,
            "description": agent.description,
            "is_active": agent.is_active,
            "stats": {
                "total_calls": total_calls,
                "successful_transfers": transfers,
                "transfer_rate": round((transfers / total_calls * 100), 1) if total_calls > 0 else 0,
                "total_duration_minutes": round(total_duration / 60, 1),
                "avg_duration_seconds": round(total_duration / total_calls, 1) if total_calls > 0 else 0
            }
        })
    
    return {
        "period": {
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat()
        },
        "agents": agent_stats
    }


@router.get("/transfers")
async def get_successful_transfers(
    from_date: Optional[date] = Query(None, description="Start date"),
    to_date: Optional[date] = Query(None, description="End date"),
    agent_id: Optional[UUID] = Query(None, description="Filter by agent"),
    tier: Optional[str] = Query(None, description="Filter by tier (high, mid, low)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get list of successful transfers with filtering.
    """
    # Default to last 7 days if no dates provided
    if not from_date:
        from_date = date.today() - timedelta(days=7)
    if not to_date:
        to_date = date.today()
    
    start_datetime = datetime.combine(from_date, datetime.min.time())
    end_datetime = datetime.combine(to_date, datetime.max.time())
    
    # Build filter
    filters = [
        CallRecord.transfer_success == True,
        CallRecord.created_at >= start_datetime,
        CallRecord.created_at <= end_datetime
    ]
    
    if not current_user.is_admin() and current_user.client_id:
        filters.append(CallRecord.client_id == current_user.client_id)
    
    if agent_id:
        filters.append(CallRecord.agent_id == agent_id)
    
    if tier:
        tier_enum = TransferTier(tier) if tier in ["high", "mid", "low"] else None
        if tier_enum:
            filters.append(CallRecord.transfer_tier == tier_enum)
    
    # Count total
    count_result = await db.execute(
        select(func.count(CallRecord.id)).where(and_(*filters))
    )
    total = count_result.scalar() or 0
    
    # Get transfers
    result = await db.execute(
        select(CallRecord)
        .where(and_(*filters))
        .order_by(CallRecord.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    transfers = result.scalars().all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "transfers": [t.to_dashboard_dict() for t in transfers]
    }


@router.get("/lost-transfers")
async def get_lost_transfers(
    from_date: Optional[date] = Query(None, description="Start date (defaults to today)"),
    to_date: Optional[date] = Query(None, description="End date (defaults to today)"),
    tier: Optional[str] = Query(None, description="Filter by tier (high, mid, low)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get lost transfers - calls that qualified for transfer but no closer answered.
    These represent missed revenue opportunities.
    """
    if not from_date:
        from_date = date.today()
    if not to_date:
        to_date = date.today()
    
    start_datetime = datetime.combine(from_date, datetime.min.time())
    end_datetime = datetime.combine(to_date, datetime.max.time())
    
    # Lost transfers: had a transfer tier but transfer was not successful
    filters = [
        CallRecord.created_at >= start_datetime,
        CallRecord.created_at <= end_datetime,
        CallRecord.transfer_tier.in_([TransferTier.HIGH, TransferTier.MID, TransferTier.LOW]),
        CallRecord.transfer_success == False,
        or_(
            CallRecord.disconnection_reason == DisconnectionReason.NO_ANSWER,
            CallRecord.disconnection_reason == DisconnectionReason.TIMEOUT,
            CallRecord.disconnection_reason == DisconnectionReason.CALLER_HANGUP
        )
    ]
    
    if not current_user.is_admin() and current_user.client_id:
        filters.append(CallRecord.client_id == current_user.client_id)
    
    if tier:
        try:
            tier_enum = TransferTier(tier)
            filters.append(CallRecord.transfer_tier == tier_enum)
        except ValueError:
            pass
    
    # Count total
    count_result = await db.execute(
        select(func.count(CallRecord.id)).where(and_(*filters))
    )
    total = count_result.scalar() or 0
    
    # Summary by tier
    tier_summary = {"high": 0, "mid": 0, "low": 0}
    try:
        tier_result = await db.execute(
            select(
                CallRecord.transfer_tier,
                func.count(CallRecord.id)
            ).where(and_(*filters))
            .group_by(CallRecord.transfer_tier)
        )
        for row in tier_result:
            if row[0] and row[0].value in tier_summary:
                tier_summary[row[0].value] = row[1]
    except Exception as e:
        logger.warning(f"Error getting tier summary: {e}")
    
    # Get the calls
    result = await db.execute(
        select(CallRecord)
        .where(and_(*filters))
        .order_by(CallRecord.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    lost_calls = result.scalars().all()
    
    # Calculate estimated lost revenue (rough estimate: $500 per High, $300 per Mid, $100 per Low)
    estimated_lost_revenue = (
        tier_summary["high"] * 500 +
        tier_summary["mid"] * 300 +
        tier_summary["low"] * 100
    )
    
    return {
        "period": {
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat()
        },
        "total_lost": total,
        "by_tier": tier_summary,
        "estimated_lost_revenue": estimated_lost_revenue,
        "skip": skip,
        "limit": limit,
        "calls": [c.to_dashboard_dict() for c in lost_calls]
    }


@router.get("/pickup-rates")
async def get_pickup_rates_by_did(
    from_date: Optional[date] = Query(None, description="Start date (defaults to today)"),
    to_date: Optional[date] = Query(None, description="End date (defaults to today)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get pickup rates by destination DID.
    Shows which queues/DIDs have the best and worst answer rates.
    """
    if not from_date:
        from_date = date.today()
    if not to_date:
        to_date = date.today()
    
    start_datetime = datetime.combine(from_date, datetime.min.time())
    end_datetime = datetime.combine(to_date, datetime.max.time())
    
    # Filter for calls that attempted transfer
    filters = [
        CallRecord.created_at >= start_datetime,
        CallRecord.created_at <= end_datetime,
        CallRecord.transfer_did.isnot(None),
        CallRecord.transfer_tier.in_([TransferTier.HIGH, TransferTier.MID, TransferTier.LOW])
    ]
    
    if not current_user.is_admin() and current_user.client_id:
        filters.append(CallRecord.client_id == current_user.client_id)
    
    # Group by DID and calculate pickup rates
    result = await db.execute(
        select(
            CallRecord.transfer_did,
            CallRecord.transfer_tier,
            func.count(CallRecord.id).label('total_attempts'),
            func.count(CallRecord.id).filter(CallRecord.transfer_success == True).label('successful'),
            func.avg(CallRecord.transfer_wait_duration).label('avg_wait')
        ).where(and_(*filters))
        .group_by(CallRecord.transfer_did, CallRecord.transfer_tier)
        .order_by(func.count(CallRecord.id).desc())
    )
    
    did_stats = []
    for row in result:
        total_attempts = row.total_attempts or 0
        successful = row.successful or 0
        pickup_rate = round((successful / total_attempts * 100), 1) if total_attempts > 0 else 0
        
        did_stats.append({
            "did": row.transfer_did,
            "tier": row.transfer_tier.value if row.transfer_tier else "unknown",
            "total_attempts": total_attempts,
            "successful": successful,
            "lost": total_attempts - successful,
            "pickup_rate": pickup_rate,
            "avg_wait_seconds": round(row.avg_wait or 0, 1)
        })
    
    # Sort by pickup rate (worst first for identifying problems)
    did_stats_sorted = sorted(did_stats, key=lambda x: x['pickup_rate'])
    
    return {
        "period": {
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat()
        },
        "did_performance": did_stats_sorted,
        "best_performing": did_stats_sorted[-1] if did_stats_sorted else None,
        "worst_performing": did_stats_sorted[0] if did_stats_sorted else None
    }


@router.get("/time-of-day")
async def get_time_of_day_analysis(
    from_date: Optional[date] = Query(None, description="Start date (defaults to last 7 days)"),
    to_date: Optional[date] = Query(None, description="End date (defaults to today)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get call volume and quality analysis by hour of day.
    Helps identify optimal staffing hours.
    """
    if not from_date:
        from_date = date.today() - timedelta(days=7)
    if not to_date:
        to_date = date.today()
    
    start_datetime = datetime.combine(from_date, datetime.min.time())
    end_datetime = datetime.combine(to_date, datetime.max.time())
    
    filters = [
        CallRecord.created_at >= start_datetime,
        CallRecord.created_at <= end_datetime,
    ]
    
    if not current_user.is_admin() and current_user.client_id:
        filters.append(CallRecord.client_id == current_user.client_id)
    
    # Get all calls in the period
    result = await db.execute(
        select(CallRecord).where(and_(*filters))
    )
    calls = result.scalars().all()
    
    # Initialize hourly buckets
    hourly_stats = {hour: {
        "total_calls": 0,
        "qualified_calls": 0,  # Had transfer tier HIGH or MID
        "successful_transfers": 0,
        "total_debt": 0.0
    } for hour in range(24)}
    
    # Aggregate by hour
    for call in calls:
        if call.call_started_at:
            hour = call.call_started_at.hour
        elif call.created_at:
            hour = call.created_at.hour
        else:
            continue
        
        hourly_stats[hour]["total_calls"] += 1
        
        if call.transfer_tier in [TransferTier.HIGH, TransferTier.MID]:
            hourly_stats[hour]["qualified_calls"] += 1
        
        if call.transfer_success:
            hourly_stats[hour]["successful_transfers"] += 1
        
        if call.total_debt:
            hourly_stats[hour]["total_debt"] += call.total_debt
    
    # Convert to list with derived metrics
    hourly_analysis = []
    for hour in range(24):
        stats = hourly_stats[hour]
        total = stats["total_calls"]
        qualified = stats["qualified_calls"]
        
        hourly_analysis.append({
            "hour": hour,
            "hour_label": f"{hour:02d}:00",
            "total_calls": total,
            "qualified_calls": qualified,
            "successful_transfers": stats["successful_transfers"],
            "qualification_rate": round((qualified / total * 100), 1) if total > 0 else 0,
            "avg_debt": round(stats["total_debt"] / total, 2) if total > 0 else 0
        })
    
    # Find peak hours
    peak_volume_hour = max(hourly_analysis, key=lambda x: x["total_calls"])
    peak_quality_hour = max(hourly_analysis, key=lambda x: x["qualified_calls"])
    
    return {
        "period": {
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat()
        },
        "hourly_breakdown": hourly_analysis,
        "peak_volume_hour": peak_volume_hour,
        "peak_quality_hour": peak_quality_hour
    }


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

