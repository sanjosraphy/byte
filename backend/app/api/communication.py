"""Communication API routes for agent-to-agent requests."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.database.schema import User, Agent
from app.middleware.auth import get_current_user
from app.models.communication import (
    AgentRequestCreate, AgentRequestResponse, AgentRequestReceived, RequestStatus
)
from app.services.communication_service import CommunicationService
from app.database.communication_schema import AgentRequest

router = APIRouter(prefix="/api/communication", tags=["communication"])


@router.post("/request", response_model=AgentRequestResponse)
async def send_request(
    request_data: AgentRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a request from current user's agent to another agent.

    This endpoint:
    1. Creates a new AgentRequest in PENDING status
    2. Does NOT automatically check permissions (that happens in process_request)
    3. Returns the request object for tracking

    Note: The actual permission check and data fetch happens when the
    target agent retrieves and processes the request.
    """
    try:
        # Get current user's agent
        requesting_agent = db.query(Agent).filter(
            Agent.user_id == current_user.id
        ).first()

        if not requesting_agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Your agent not found"
            )

        # Create the request
        agent_request = CommunicationService.create_request(
            db,
            requesting_agent.id,
            request_data.target_agent_unique_key,
            request_data.request_type,
            request_data.requested_data_category,
            request_data.requested_fields,
            request_data.purpose,
            request_data.context
        )

        # Get target agent info for response
        target_agent = db.query(Agent).filter(
            Agent.id == agent_request.target_agent_id
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
            created_at=agent_request.created_at
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/requests/incoming", response_model=list[AgentRequestReceived])
async def get_incoming_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all incoming requests for current user's agent.

    Returns all requests targeting this user's agent, regardless of status.
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

        # Get all requests for this agent
        requests = CommunicationService.get_requests_for_agent(db, agent.id)

        result = []
        for req in requests:
            requesting_agent = db.query(Agent).filter(
                Agent.id == req.requesting_agent_id
            ).first()
            requesting_user = db.query(User).filter(
                User.id == requesting_agent.user_id
            ).first()

            result.append(AgentRequestReceived(
                id=req.id,
                requesting_agent_id=requesting_agent.id,
                requesting_agent_name=requesting_agent.name,
                requesting_user_id=requesting_user.id,
                requesting_user_name=requesting_user.full_name,
                request_type=req.request_type,
                requested_data_category=req.requested_data_category,
                requested_fields=req.requested_fields.split(","),
                purpose=req.purpose,
                created_at=req.created_at,
                status=RequestStatus(req.status),
                context=req.context
            ))

        return result

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/request/{request_id}", response_model=AgentRequestResponse)
async def get_request_status(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get status and details of a specific request.

    The requesting agent can check if their request was processed and what data
    was returned (or why it was denied).
    """
    try:
        agent_request = CommunicationService.get_request_by_id(db, request_id)

        if not agent_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Request not found"
            )

        # Verify the current user is the requesting agent's user
        requesting_agent = db.query(Agent).filter(
            Agent.id == agent_request.requesting_agent_id
        ).first()

        if requesting_agent.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own requests"
            )

        target_agent = db.query(Agent).filter(
            Agent.id == agent_request.target_agent_id
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


@router.post("/request/{request_id}/process")
async def process_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process a request - check permissions and prepare response.

    CRITICAL SECURITY:
    This endpoint checks the Permission Engine for authorization.
    The LLM has NO authority here - the server-side permission engine
    makes the final ALLOW/DENY decision.

    Only the target agent's user can process the request.
    """
    try:
        agent_request = CommunicationService.get_request_by_id(db, request_id)

        if not agent_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Request not found"
            )

        # Verify the current user is the target agent's user
        target_agent = db.query(Agent).filter(
            Agent.id == agent_request.target_agent_id
        ).first()

        if target_agent.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the target user can process this request"
            )

        # Process the request (permission check + data fetch)
        processed_request = CommunicationService.process_request(db, request_id)

        requesting_agent = db.query(Agent).filter(
            Agent.id == processed_request.requesting_agent_id
        ).first()

        return AgentRequestResponse(
            id=processed_request.id,
            requesting_agent_id=requesting_agent.id,
            requesting_agent_name=requesting_agent.name,
            target_agent_id=target_agent.id,
            target_agent_name=target_agent.name,
            target_user_id=target_agent.user_id,
            request_type=processed_request.request_type,
            requested_data_category=processed_request.requested_data_category,
            requested_fields=processed_request.requested_fields.split(","),
            purpose=processed_request.purpose,
            status=RequestStatus(processed_request.status),
            created_at=processed_request.created_at,
            response_data=processed_request.response_data,
            error_message=processed_request.error_message
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
