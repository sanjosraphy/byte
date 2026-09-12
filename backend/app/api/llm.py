"""LLM integration API routes for Phase 12."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.database.schema import User
from app.middleware.auth import get_current_user
from app.services.llm_service import LLMService
from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class UserRequestInput(BaseModel):
    """Natural language user request."""
    request: str


class UnderstandingResponse(BaseModel):
    """LLM's understanding of user request."""
    intent: str
    activity_type: str
    participants: List[str]
    timeframe: str
    required_information: List[str]


class DataRequestSuggestion(BaseModel):
    """Suggested data request based on understanding."""
    data_category: str
    fields: List[str]
    purpose: str
    suggested_permission_type: str


class DataRequestsResponse(BaseModel):
    """Response with suggested data requests."""
    requests: List[DataRequestSuggestion]


class ReasoningInput(BaseModel):
    """Input for LLM reasoning."""
    approved_data: Dict[str, Any]
    task: str


class ReasoningResponse(BaseModel):
    """LLM's reasoning result."""
    reasoning: str
    recommendation: str


router = APIRouter(prefix="/api/llm", tags=["llm"])


@router.post("/understand", response_model=UnderstandingResponse)
async def understand_request(
    input_data: UserRequestInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Use LLM to understand user's natural language request.

    This helps agents understand what the user is trying to accomplish.
    """
    try:
        understanding = LLMService.understand_user_request(input_data.request)
        return UnderstandingResponse(**understanding)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/plan-requests", response_model=DataRequestsResponse)
async def plan_data_requests(
    input_data: UserRequestInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Use LLM to plan what data requests are needed.

    Based on user request, generate structured requests for other agents.
    """
    try:
        understanding = LLMService.understand_user_request(input_data.request)
        requests = LLMService.plan_data_requests(input_data.request, understanding)
        return DataRequestsResponse(
            requests=[DataRequestSuggestion(**req) for req in requests]
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/reason", response_model=ReasoningResponse)
async def reason_over_data(
    input_data: ReasoningInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Use LLM to reason over approved data and produce recommendations.

    This is called after all permissions are approved and data is received.
    """
    try:
        user_context = {
            "user_id": current_user.id,
            "username": current_user.username,
            "name": current_user.full_name
        }
        reasoning = LLMService.reason_over_data(
            input_data.approved_data,
            user_context,
            input_data.task
        )
        return ReasoningResponse(
            reasoning=reasoning,
            recommendation=reasoning
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
