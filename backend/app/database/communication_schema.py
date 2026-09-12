"""Agent request model for database."""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from datetime import datetime
from app.database.db import Base


class AgentRequest(Base):
    """Model for agent-to-agent requests."""
    __tablename__ = "agent_requests"

    id = Column(Integer, primary_key=True, index=True)
    requesting_agent_id = Column(Integer, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    target_agent_id = Column(Integer, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    request_type = Column(String, index=True)  # e.g., "calendar_availability"
    requested_data_category = Column(String, index=True)  # e.g., "calendar", "preferences"
    requested_fields = Column(String)  # Comma-separated: "free_busy,availability_windows"
    purpose = Column(String)  # e.g., "find_common_meeting_time"
    status = Column(String, default="pending", index=True)  # pending, approved, denied, executed, error
    response_data = Column(JSON, nullable=True)  # The actual data returned (after permission check)
    error_message = Column(Text, nullable=True)  # Error details if request failed
    context = Column(JSON, nullable=True)  # Additional context
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    responded_at = Column(DateTime, nullable=True)


class AuditLog(Base):
    """Audit log for all cross-agent requests."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    requesting_agent_id = Column(Integer, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    target_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    data_category = Column(String, index=True)
    requested_fields = Column(String)  # Comma-separated
    allowed_fields = Column(String, nullable=True)  # What was actually allowed
    shared_fields = Column(String, nullable=True)  # What was actually shared
    purpose = Column(String)
    permission_status = Column(String)  # ALLOWED, DENIED, PENDING_CONSENT, EXPIRED, REVOKED
    user_decision = Column(String, nullable=True)  # APPROVED, DENIED (for consent screens)
    result = Column(String)  # SUCCESS, DENIED, ERROR, PENDING
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    class Config:
        from_attributes = True
