"""Granular field-level permission models."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict
from enum import Enum


class FieldPermissionType(str, Enum):
    """Types of field-level permissions."""
    ACCESSIBLE = "accessible"  # Can be read
    HIDDEN = "hidden"  # Cannot be read
    MINIMIZED = "minimized"  # Partially revealed (e.g., approximate location)
    REDACTED = "redacted"  # Returned but sensitive info removed


class FieldDefinition(BaseModel):
    """Definition of a data field with metadata."""
    field_name: str  # e.g., "exact_gps"
    display_name: str  # e.g., "Exact GPS Coordinates"
    data_category: str  # e.g., "location"
    description: str  # e.g., "User's precise latitude/longitude"
    sensitivity_level: int  # 1=low (public), 5=high (very private)
    default_permission: FieldPermissionType = FieldPermissionType.HIDDEN


class FieldLevelPermissionRequest(BaseModel):
    """Request to grant field-level permissions."""
    grantee_agent_unique_key: str
    data_category: str
    field_permissions: Dict[str, FieldPermissionType]  # {"exact_gps": "HIDDEN", "location_name": "ACCESSIBLE"}
    permission_type: str = "one_hour"
    custom_expiry_minutes: Optional[int] = None
    purpose: Optional[str] = None


class FieldLevelPermissionResponse(BaseModel):
    """Response for field-level permission."""
    id: int
    grantor_id: int
    grantor_name: str
    grantee_agent_id: int
    grantee_agent_name: str
    grantee_user_id: int
    grantee_user_name: str
    data_category: str
    field_permissions: Dict[str, str]  # {"field_name": "permission_type"}
    permission_type: str
    created_at: datetime
    expires_at: Optional[datetime]
    is_revoked: bool

    class Config:
        from_attributes = True


class PermissionTemplate(BaseModel):
    """Predefined permission template for common scenarios."""
    template_name: str  # e.g., "meeting_scheduling", "social_outing"
    description: str
    data_category: str
    recommended_fields: Dict[str, FieldPermissionType]
    recommended_duration: str  # e.g., "one_hour"
    use_case: str  # e.g., "Allows agent to find free time without seeing event details"


class AvailableFieldsResponse(BaseModel):
    """List of all available fields for a data category."""
    data_category: str
    fields: List[FieldDefinition]
    templates: List[PermissionTemplate]
