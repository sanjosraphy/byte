"""User data API routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.database.schema import User
from app.middleware.auth import get_current_user
from app.models.user import UserResponse
from app.models.agent import AgentResponse
from app.models.data import (
    CalendarEventResponse, PreferenceResponse, LocationResponse,
    BudgetResponse, UserDataSummaryResponse
)
from app.services.data_access_service import DataAccessService

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information."""
    return current_user


@router.get("/me/agent", response_model=AgentResponse)
async def get_user_agent(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's agent."""
    try:
        agent = DataAccessService.get_user_agent(db, current_user.id, current_user.id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found for this user"
            )
        return agent
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/me/calendar", response_model=list[CalendarEventResponse])
async def get_user_calendar(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's calendar events."""
    try:
        return DataAccessService.get_user_calendar(db, current_user.id, current_user.id)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/me/preferences", response_model=list[PreferenceResponse])
async def get_user_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's preferences."""
    try:
        return DataAccessService.get_user_preferences(db, current_user.id, current_user.id)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/me/location", response_model=LocationResponse)
async def get_user_location(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's location."""
    try:
        location = DataAccessService.get_user_location(db, current_user.id, current_user.id)
        if not location:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Location not found"
            )
        return location
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/me/budget", response_model=list[BudgetResponse])
async def get_user_budget(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's budget information."""
    try:
        return DataAccessService.get_user_budgets(db, current_user.id, current_user.id)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
