"""Update database schema to include communication tables."""
from app.database.db import Base, engine
from app.database.communication_schema import AgentRequest, AuditLog  # noqa: F401


def create_communication_tables():
    """Create communication tables (AgentRequest, AuditLog)."""
    Base.metadata.create_all(bind=engine)
    print("✅ Communication tables created")
