"""Consent screen API routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.database.schema import User, Agent
from app.database.communication_schema import AgentRequest
from app.middleware.auth import get_current_user
from app.models.permission import (
    ConsentScreenResponse, ConsentDecisionRequest, ConsentDecision
)
from app.models.communication import AgentRequestResponse, RequestStatus
from app.services.permission_service import PermissionService
from app.services.communication_service import CommunicationService

router = APIRouter(prefix="/api/consent", tags=["consent"])


@router.get("/pending", response_model=list[int])
async def get_pending_consents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get IDs of pending agent requests awaiting user consent.

    In Phase 6, requests without permissions automatically require consent.
    This endpoint returns the IDs of such pending requests.
    """
    try:
        # Get current user's agent
        agent = db.query(Agent).filter(
            Agent.user_id == current_user.id
        ).first()

        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Your agent not found"
            )

        # Get pending requests (those without permission)
        pending_requests = db.query(AgentRequest).filter(
            AgentRequest.target_agent_id == agent.id,
            AgentRequest.status == RequestStatus.PENDING.value
        ).all()

        return [req.id for req in pending_requests]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/screen/{agent_request_id}", response_model=ConsentScreenResponse)
async def get_consent_screen(
    agent_request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get consent screen data for a specific request.

    Returns:
        All information needed to render the consent UI
    """
    try:
        agent_request = db.query(AgentRequest).filter(
            AgentRequest.id == agent_request_id
        ).first()

        if not agent_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Request not found"
            )

        # Verify current user is the target
        target_agent = db.query(Agent).filter(
            Agent.id == agent_request.target_agent_id
        ).first()

        if target_agent.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This consent screen is not for you"
            )

        # Prepare consent screen data
        screen_data = PermissionService.prepare_consent_screen(db, agent_request_id)

        return ConsentScreenResponse(**screen_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/decide/{agent_request_id}", response_model=AgentRequestResponse)
async def decide_consent(
    agent_request_id: int,
    decision_data: ConsentDecisionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """User makes a decision on the consent screen.

    If ALLOWED: Permission is granted and request is re-processed
    If DENIED: Request is marked as denied
    """
    try:
        agent_request = db.query(AgentRequest).filter(
            AgentRequest.id == agent_request_id
        ).first()

        if not agent_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Request not found"
            )

        # Verify current user is the target
        target_agent = db.query(Agent).filter(
            Agent.id == agent_request.target_agent_id
        ).first()

        if target_agent.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot make decisions for other users' consent"
            )

        # Process the decision
        if decision_data.decision == ConsentDecision.DENIED:
            agent_request.status = RequestStatus.DENIED.value
            agent_request.error_message = "User denied permission"
            db.commit()
            db.refresh(agent_request)
        else:
            # Grant permission based on decision
            permission = PermissionService.handle_consent_decision(
                db,
                agent_request_id,
                decision_data.decision,
                decision_data.custom_expiry_minutes
            )

            if permission:
                # Re-process the request now that permission is granted
                agent_request = CommunicationService.process_request(db, agent_request_id)

        # Return updated request
        requesting_agent = db.query(Agent).filter(
            Agent.id == agent_request.requesting_agent_id
        ).first()

        return AgentRequestResponse(
            id=agent_request.id,
            requesting_agent_id=requesting_agent.id,
            requesting_agent_name=requesting_agent.name,
            target_agent_id=target_agent.id,
            target_agent_name=target_agent.name,
            target_user_id=target_agent.user_id,
            request_type=agent_request.request_type,
            requested_data_category=agent_request.requested_data_category,
            requested_fields=agent_request.requested_fields.split(","),
            purpose=agent_request.purpose,
            status=RequestStatus(agent_request.status),
            created_at=agent_request.created_at,
            response_data=agent_request.response_data,
            error_message=agent_request.error_message
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
