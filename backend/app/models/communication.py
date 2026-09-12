"""Agent-to-agent communication models."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any, Dict
from enum import Enum


class RequestStatus(str, Enum):
    """Status of an agent request."""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"
    EXECUTED = "executed"
    ERROR = "error"


class AgentRequestCreate(BaseModel):
    """Create an agent-to-agent request."""
    target_agent_unique_key: str  # e.g., "agent_b"
    request_type: str  # e.g., "calendar_availability", "preference_query"
    requested_data_category: str  # e.g., "calendar", "preferences", "location"
    requested_fields: list[str]  # e.g., ["free_busy", "availability_windows"]
    purpose: str  # e.g., "find_common_meeting_time"
    duration: Optional[str] = None  # e.g., "1 hour", "2 hours"
    context: Optional[Dict[str, Any]] = None  # Additional context for the request


class AgentRequestResponse(BaseModel):
    """Response model for agent requests."""
    id: int
    requesting_agent_id: int
    requesting_agent_name: str
    target_agent_id: int
    target_agent_name: str
    target_user_id: int
    request_type: str
    requested_data_category: str
    requested_fields: list[str]
    purpose: str
    status: RequestStatus
    created_at: datetime
    response_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class AgentRequestReceived(BaseModel):
    """Model for received requests at target agent."""
    id: int
    requesting_agent_id: int
    requesting_agent_name: str
    requesting_user_id: int
    requesting_user_name: str
    request_type: str
    requested_data_category: str
    requested_fields: list[str]
    purpose: str
    created_at: datetime
    status: RequestStatus
    context: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
