"""Demo scenario models for Phase 10."""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Boolean
from datetime import datetime
from app.database.db import Base


class DemoScenario(Base):
    """Demo scenario tracking."""
    __tablename__ = "demo_scenarios"

    id = Column(Integer, primary_key=True, index=True)
    scenario_name = Column(String, index=True)  # e.g., "movie_night", "project_coordination"
    description = Column(Text)
    initiating_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    target_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    initial_request = Column(Text)  # User's initial request in natural language
    status = Column(String, default="in_progress")  # in_progress, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)


class DemoResult(Base):
    """Results of a demo scenario execution."""
    __tablename__ = "demo_results"

    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, ForeignKey("demo_scenarios.id", ondelete="CASCADE"), nullable=False)
    step_number = Column(Integer)  # Sequential step in the demo
    step_description = Column(String)  # What happened
    data_requested = Column(JSON)  # What data was requested
    permission_status = Column(String)  # PENDING_CONSENT, ALLOWED, DENIED
    user_decision = Column(String, nullable=True)  # User's consent decision
    data_shared = Column(JSON, nullable=True)  # What data was actually shared
    agent_reasoning = Column(Text, nullable=True)  # Agent's reasoning (for Phase 12)
    timestamp = Column(DateTime, default=datetime.utcnow)
