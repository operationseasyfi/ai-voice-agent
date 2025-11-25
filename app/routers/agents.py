from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel

from app.database import get_db
from app.models.agent import Agent
from app.auth.dependencies import get_current_active_user
from app.models.models import User

router = APIRouter()


class AgentResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    voice_config: dict
    routing_config: dict
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True


@router.get("/")
async def list_agents(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all AI agents for the current user's client.
    """
    filters = []
    
    # Client filtering
    if not current_user.is_admin() and current_user.client_id:
        filters.append(Agent.client_id == current_user.client_id)
    
    # Active status filter
    if is_active is not None:
        filters.append(Agent.is_active == is_active)
    
    if filters:
        result = await db.execute(select(Agent).where(and_(*filters)))
    else:
        result = await db.execute(select(Agent))
    
    agents = result.scalars().all()
    
    return {
        "agents": [
            {
                "id": str(a.id),
                "name": a.name,
                "description": a.description,
                "voice_config": a.voice_config,
                "routing_config": a.routing_config,
                "is_active": a.is_active,
                "created_at": a.created_at.isoformat() if a.created_at else None
            }
            for a in agents
        ]
    }


@router.get("/{agent_id}")
async def get_agent(
    agent_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get details for a specific AI agent.
    """
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Check access
    if not current_user.is_admin() and agent.client_id != current_user.client_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "id": str(agent.id),
        "client_id": str(agent.client_id),
        "name": agent.name,
        "description": agent.description,
        "voice_config": agent.voice_config,
        "prompt_config": agent.prompt_config,
        "routing_config": agent.routing_config,
        "is_active": agent.is_active,
        "stats_cache": agent.stats_cache,
        "created_at": agent.created_at.isoformat() if agent.created_at else None,
        "updated_at": agent.updated_at.isoformat() if agent.updated_at else None
    }

