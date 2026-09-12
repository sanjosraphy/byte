"""Agent-related Pydantic models."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AgentResponse(BaseModel):
    """Agent response."""
    id: int
    user_id: int
    name: str
    unique_key: str
    system_instructions: str
    created_at: datetime

    class Config:
        from_attributes = True


class AgentStatusResponse(BaseModel):
    """Agent status response."""
    agent_id: int
    agent_name: str
    unique_key: str
    user_id: int
    user_name: str
    status: str = "active"
    created_at: datetime
