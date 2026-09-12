"""Agent API routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.database.schema import User, Agent
from app.middleware.auth import get_current_user
from app.models.agent import AgentStatusResponse
from datetime import datetime

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.get("/status", response_model=AgentStatusResponse)
async def get_agent_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get status of current user's agent."""
    agent = db.query(Agent).filter(Agent.user_id == current_user.id).first()

    return AgentStatusResponse(
        agent_id=agent.id,
        agent_name=agent.name,
        unique_key=agent.unique_key,
        user_id=agent.user_id,
        user_name=current_user.full_name,
        status="active",
        created_at=agent.created_at
    )
