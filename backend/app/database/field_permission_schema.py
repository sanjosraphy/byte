"""Update schema to include field-level permissions."""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Boolean
from datetime import datetime
from app.database.db import Base


class FieldLevelPermission(Base):
    """Field-level permission model - more granular than category permissions."""
    __tablename__ = "field_level_permissions"

    id = Column(Integer, primary_key=True, index=True)
    grantor_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    grantee_agent_id = Column(Integer, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    data_category = Column(String, index=True)  # e.g., "location"
    field_permissions = Column(JSON)  # {"exact_gps": "hidden", "location_name": "accessible"}
    permission_type = Column(String)  # one_time, one_hour, etc.
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime, nullable=True, index=True)
    is_revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime, nullable=True)
