"""Data access service - ensures users can only access their own data."""
from sqlalchemy.orm import Session
from app.database.schema import (
    User, Agent, UserCalendar, UserPreference, UserLocation, UserBudget
)
from typing import List, Optional


class DataAccessService:
    """Service to safely access user data with isolation."""

    @staticmethod
    def get_user_calendar(
        db: Session, user_id: int, requesting_user_id: int
    ) -> List[UserCalendar]:
        """Get calendar events - only if requesting user is the owner."""
        if user_id != requesting_user_id:
            raise PermissionError(
                f"Cannot access calendar for user {user_id}. "
                f"Cross-user data access requires permission engine."
            )

        return db.query(UserCalendar).filter(
            UserCalendar.user_id == user_id
        ).all()

    @staticmethod
    def get_user_preferences(
        db: Session, user_id: int, requesting_user_id: int
    ) -> List[UserPreference]:
        """Get preferences - only if requesting user is the owner."""
        if user_id != requesting_user_id:
            raise PermissionError(
                f"Cannot access preferences for user {user_id}. "
                f"Cross-user data access requires permission engine."
            )

        return db.query(UserPreference).filter(
            UserPreference.user_id == user_id
        ).all()

    @staticmethod
    def get_user_location(
        db: Session, user_id: int, requesting_user_id: int
    ) -> Optional[UserLocation]:
        """Get current location - only if requesting user is the owner."""
        if user_id != requesting_user_id:
            raise PermissionError(
                f"Cannot access location for user {user_id}. "
                f"Cross-user data access requires permission engine."
            )

        return db.query(UserLocation).filter(
            UserLocation.user_id == user_id
        ).order_by(UserLocation.timestamp.desc()).first()

    @staticmethod
    def get_user_budgets(
        db: Session, user_id: int, requesting_user_id: int
    ) -> List[UserBudget]:
        """Get budgets - only if requesting user is the owner."""
        if user_id != requesting_user_id:
            raise PermissionError(
                f"Cannot access budgets for user {user_id}. "
                f"Cross-user data access requires permission engine."
            )

        return db.query(UserBudget).filter(
            UserBudget.user_id == user_id
        ).all()

    @staticmethod
    def get_user_agent(
        db: Session, user_id: int, requesting_user_id: int
    ) -> Optional[Agent]:
        """Get user's agent - only if requesting user is the owner."""
        if user_id != requesting_user_id:
            raise PermissionError(
                f"Cannot access agent for user {user_id}. "
                f"Cross-user data access requires permission engine."
            )

        return db.query(Agent).filter(Agent.user_id == user_id).first()
