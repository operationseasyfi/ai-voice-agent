from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import Optional
from datetime import date, datetime, timedelta
from uuid import UUID

from app.database import get_db
from app.models.call_records import CallRecord
from app.models.client import Client
from app.models.agent import Agent
from app.auth.dependencies import get_current_active_user
from app.models.models import User

router = APIRouter()


@router.get("/usage")
async def get_usage(
    from_date: Optional[date] = Query(None, description="Start date (defaults to current billing period)"),
    to_date: Optional[date] = Query(None, description="End date (defaults to today)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current billing period usage for the client.
    Display-only for now - actual billing is manual.
    """
    # Default to current month if no dates
    if not from_date:
        today = date.today()
        from_date = date(today.year, today.month, 1)  # First of month
    if not to_date:
        to_date = date.today()
    
    start_datetime = datetime.combine(from_date, datetime.min.time())
    end_datetime = datetime.combine(to_date, datetime.max.time())
    
    # Build filters
    filters = [
        CallRecord.created_at >= start_datetime,
        CallRecord.created_at <= end_datetime
    ]
    
    if not current_user.is_admin() and current_user.client_id:
        filters.append(CallRecord.client_id == current_user.client_id)
    
    # Get total calls and duration
    stats_result = await db.execute(
        select(
            func.count(CallRecord.id),
            func.sum(CallRecord.duration),
            func.count(CallRecord.id).filter(CallRecord.transfer_success == True)
        ).where(and_(*filters))
    )
    stats = stats_result.one()
    
    total_calls = stats[0] or 0
    total_duration_seconds = stats[1] or 0
    total_transfers = stats[2] or 0
    
    # Calculate minutes
    total_minutes = total_duration_seconds / 60
    
    # Get breakdown by agent
    agent_breakdown = []
    if current_user.client_id or current_user.is_admin():
        # Get agents
        agent_filters = []
        if not current_user.is_admin() and current_user.client_id:
            agent_filters.append(Agent.client_id == current_user.client_id)
        
        agent_query = select(Agent)
        if agent_filters:
            agent_query = agent_query.where(and_(*agent_filters))
        
        agents_result = await db.execute(agent_query)
        agents = agents_result.scalars().all()
        
        for agent in agents:
            agent_call_filter = filters + [CallRecord.agent_id == agent.id]
            agent_stats = await db.execute(
                select(
                    func.count(CallRecord.id),
                    func.sum(CallRecord.duration)
                ).where(and_(*agent_call_filter))
            )
            agent_row = agent_stats.one()
            
            agent_breakdown.append({
                "agent_id": str(agent.id),
                "agent_name": agent.name,
                "total_calls": agent_row[0] or 0,
                "total_minutes": round((agent_row[1] or 0) / 60, 2)
            })
    
    return {
        "period": {
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat()
        },
        "summary": {
            "total_calls": total_calls,
            "total_minutes": round(total_minutes, 2),
            "total_transfers": total_transfers,
            "avg_call_duration_seconds": round(total_duration_seconds / total_calls, 1) if total_calls > 0 else 0
        },
        "breakdown_by_agent": agent_breakdown,
        "billing_note": "Usage-based billing. Contact support for billing inquiries."
    }


@router.get("/profile")
async def get_billing_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get billing profile information for the client.
    """
    if not current_user.client_id:
        return {
            "has_billing_profile": False,
            "message": "No client associated with this user"
        }
    
    result = await db.execute(select(Client).where(Client.id == current_user.client_id))
    client = result.scalar_one_or_none()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    return {
        "has_billing_profile": True,
        "client_id": str(client.id),
        "company_name": client.name,
        "billing_email": client.billing_email,
        "contact_name": client.contact_name,
        "contact_phone": client.contact_phone,
        "stripe_customer_id": client.stripe_customer_id,
        "is_active": client.is_active,
        "payment_method": {
            "status": "configured" if client.stripe_customer_id else "not_configured",
            "message": "Contact support to update payment method"
        }
    }


@router.get("/history")
async def get_billing_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(12, ge=1, le=24),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get billing history (past invoices).
    Note: This is display-only placeholder. Actual invoices are managed manually.
    """
    # For now, return placeholder data
    # In production, this would connect to Stripe or internal billing system
    
    invoices = []
    
    # Generate placeholder historical data
    today = date.today()
    for i in range(min(limit, 6)):  # Last 6 months placeholder
        month = today.month - i - 1
        year = today.year
        if month <= 0:
            month += 12
            year -= 1
        
        period_start = date(year, month, 1)
        if month == 12:
            period_end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            period_end = date(year, month + 1, 1) - timedelta(days=1)
        
        invoices.append({
            "id": f"inv_{year}{month:02d}",
            "period": {
                "from_date": period_start.isoformat(),
                "to_date": period_end.isoformat()
            },
            "status": "paid" if i > 0 else "pending",
            "amount": None,  # Actual amount not available
            "notes": "Contact support for invoice details"
        })
    
    return {
        "invoices": invoices[skip:skip + limit],
        "total": len(invoices),
        "billing_note": "For detailed invoices and payment history, please contact support."
    }

