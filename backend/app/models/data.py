"""Data models for user information."""
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class CalendarEventResponse(BaseModel):
    """Calendar event response."""
    id: int
    event_id: str
    event_name: str
    description: Optional[str]
    start_time: datetime
    end_time: datetime
    location: Optional[str]
    attendees: Optional[str]
    is_free: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PreferenceResponse(BaseModel):
    """Preference response."""
    id: int
    preference_key: str
    preference_value: str
    created_at: datetime

    class Config:
        from_attributes = True


class LocationResponse(BaseModel):
    """Location response."""
    id: int
    latitude: float
    longitude: float
    location_name: str
    is_home: bool
    timestamp: datetime

    class Config:
        from_attributes = True


class BudgetResponse(BaseModel):
    """Budget response."""
    id: int
    category: str
    amount: float
    currency: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserDataSummaryResponse(BaseModel):
    """Summary of user's personal data."""
    user_id: int
    calendar_events: List[CalendarEventResponse]
    preferences: List[PreferenceResponse]
    current_location: Optional[LocationResponse]
    budgets: List[BudgetResponse]
