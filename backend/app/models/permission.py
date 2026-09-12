"""Permission-related Pydantic models."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from enum import Enum


class PermissionType(str, Enum):
    """Types of permissions."""
    ONE_TIME = "one_time"
    TEN_MINUTES = "ten_minutes"
    ONE_HOUR = "one_hour"
    TWENTYFOUR_HOURS = "twentyfour_hours"
    UNTIL_TASK = "until_task"
    PERMANENT = "permanent"
    CUSTOM = "custom"


class ConsentDecision(str, Enum):
    """User's consent decision."""
    PENDING = "pending"
    ALLOWED = "allowed"
    DENIED = "denied"
    ALLOWED_ONCE = "allowed_once"
    ALLOWED_FOR_DURATION = "allowed_for_duration"
    CUSTOM = "custom"


class PermissionRequest(BaseModel):
    """Request to grant a permission."""
    grantee_agent_unique_key: str  # e.g., "agent_a"
    data_category: str  # e.g., "calendar"
    allowed_fields: List[str]  # e.g., ["free_busy", "availability_windows"]
    permission_type: PermissionType = PermissionType.ONE_HOUR
    custom_expiry_minutes: Optional[int] = None  # For CUSTOM type
    purpose: Optional[str] = None  # Optional: what is this permission for


class ConsentScreenRequest(BaseModel):
    """Data for consent screen - what Agent A is asking for."""
    requesting_agent_id: int
    requesting_agent_name: str
    requesting_user_id: int
    requesting_user_name: str
    data_category: str
    requested_fields: List[str]
    purpose: str
    permission_types_offered: List[PermissionType] = [
        PermissionType.ONE_TIME,
        PermissionType.ONE_HOUR,
        PermissionType.TWENTYFOUR_HOURS,
        PermissionType.CUSTOM
    ]


class ConsentDecisionRequest(BaseModel):
    """User's decision on consent screen."""
    agent_request_id: int
    decision: ConsentDecision
    custom_expiry_minutes: Optional[int] = None  # If decision is CUSTOM


class PermissionResponse(BaseModel):
    """Permission response."""
    id: int
    grantor_id: int
    grantor_name: str
    grantee_agent_id: int
    grantee_agent_name: str
    grantee_user_id: int
    grantee_user_name: str
    data_category: str
    allowed_fields: List[str]
    permission_type: str
    created_at: datetime
    expires_at: Optional[datetime]
    is_revoked: bool
    revoked_at: Optional[datetime]

    class Config:
        from_attributes = True


class PermissionsListResponse(BaseModel):
    """List of active permissions for a user."""
    active_permissions: List[PermissionResponse]
    revoked_permissions: List[PermissionResponse]
    expired_permissions: List[PermissionResponse]
    total_count: int


class ConsentScreenResponse(BaseModel):
    """Response containing consent screen information."""
    agent_request_id: int
    requesting_agent_name: str
    requesting_user_name: str
    what_is_requested: str  # e.g., "Calendar free/busy times"
    who_is_requesting: str  # e.g., "Agent A (on behalf of Alice)"
    why_is_it_needed: str  # e.g., "To schedule a movie night"
    what_will_be_shared: List[str]  # Specific fields that will be shared
    what_wont_be_shared: List[str]  # Fields that will NOT be shared
    permission_options: List[PermissionType]
