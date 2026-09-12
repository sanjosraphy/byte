"""Database schema models."""
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.db import Base, engine


class User(Base):
    """User model."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    agent = relationship("Agent", back_populates="user", uselist=False, cascade="all, delete-orphan")
    calendars = relationship("UserCalendar", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreference", back_populates="user", cascade="all, delete-orphan")
    locations = relationship("UserLocation", back_populates="user", cascade="all, delete-orphan")
    budgets = relationship("UserBudget", back_populates="user", cascade="all, delete-orphan")
    permissions_granted = relationship(
        "Permission",
        foreign_keys="Permission.grantor_id",
        back_populates="grantor",
        cascade="all, delete-orphan"
    )


class Agent(Base):
    """AI Agent model."""
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    name = Column(String, index=True)
    unique_key = Column(String, unique=True, index=True)  # e.g., "agent_a", "agent_b"
    system_instructions = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="agent")


class UserCalendar(Base):
    """User calendar events."""
    __tablename__ = "user_calendars"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    event_id = Column(String, index=True)
    event_name = Column(String)
    description = Column(Text)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    location = Column(String)
    attendees = Column(String)  # Comma-separated email addresses
    is_free = Column(Boolean, default=True)  # free/busy indicator
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="calendars")


class UserPreference(Base):
    """User preferences."""
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    preference_key = Column(String, index=True)  # e.g., "movie_genre", "music_taste"
    preference_value = Column(String)  # e.g., "action,sci-fi", "indie"
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="preferences")


class UserLocation(Base):
    """User location data."""
    __tablename__ = "user_locations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)
    location_name = Column(String)  # e.g., "Home", "Office"
    is_home = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="locations")


class UserBudget(Base):
    """User budget information."""
    __tablename__ = "user_budgets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category = Column(String, index=True)  # e.g., "entertainment", "travel"
    amount = Column(Float)  # Maximum budget amount
    currency = Column(String, default="INR")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="budgets")


class Permission(Base):
    """Permission model for agent-to-agent data access."""
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    grantor_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    grantee_agent_id = Column(Integer, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    data_category = Column(String, index=True)  # e.g., "calendar", "location", "preferences"
    allowed_fields = Column(String)  # Comma-separated: "free_busy,event_name"
    permission_type = Column(String)  # "one_time", "duration", "until_task", "permanent"
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    is_revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime, nullable=True)

    # Relationships
    grantor = relationship(
        "User",
        foreign_keys=[grantor_id],
        back_populates="permissions_granted"
    )


def create_tables():
    """Create all tables."""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")
