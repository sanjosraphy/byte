"""Communication service for agent-to-agent requests."""
from sqlalchemy.orm import Session
from datetime import datetime
from app.database.schema import Agent, User
from app.database.communication_schema import AgentRequest, AuditLog
from app.services.permission_engine import PermissionEngine
from app.services.data_access_service import DataAccessService
from typing import Optional, Dict, Any, List
from enum import Enum


class RequestStatus(str, Enum):
    """Status of an agent request."""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"
    EXECUTED = "executed"
    ERROR = "error"


class CommunicationService:
    """Service for managing agent-to-agent communication."""

    @staticmethod
    def create_request(
        db: Session,
        requesting_agent_id: int,
        target_agent_unique_key: str,
        request_type: str,
        requested_data_category: str,
        requested_fields: List[str],
        purpose: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentRequest:
        """Create a new agent-to-agent request.

        Args:
            db: Database session
            requesting_agent_id: ID of requesting agent
            target_agent_unique_key: Unique key of target agent (e.g., "agent_b")
            request_type: Type of request (e.g., "calendar_availability")
            requested_data_category: Category of data (e.g., "calendar", "preferences")
            requested_fields: List of specific fields needed
            purpose: Why the data is needed
            context: Additional context

        Returns:
            AgentRequest object
        """
        # Find target agent by unique_key
        target_agent = db.query(Agent).filter(
            Agent.unique_key == target_agent_unique_key
        ).first()

        if not target_agent:
            raise ValueError(f"Target agent '{target_agent_unique_key}' not found")

        # Create the request
        agent_request = AgentRequest(
            requesting_agent_id=requesting_agent_id,
            target_agent_id=target_agent.id,
            request_type=request_type,
            requested_data_category=requested_data_category,
            requested_fields=",".join(requested_fields),
            purpose=purpose,
            status=RequestStatus.PENDING.value,
            context=context or {}
        )

        db.add(agent_request)
        db.commit()
        db.refresh(agent_request)

        return agent_request

    @staticmethod
    def get_requests_for_agent(
        db: Session,
        agent_id: int,
        status: Optional[str] = None
    ) -> List[AgentRequest]:
        """Get all requests targeting a specific agent.

        Args:
            db: Database session
            agent_id: ID of target agent
            status: Filter by status (optional)

        Returns:
            List of AgentRequest objects
        """
        query = db.query(AgentRequest).filter(
            AgentRequest.target_agent_id == agent_id
        )

        if status:
            query = query.filter(AgentRequest.status == status)

        return query.order_by(AgentRequest.created_at.desc()).all()

    @staticmethod
    def get_request_by_id(
        db: Session,
        request_id: int
    ) -> Optional[AgentRequest]:
        """Get a specific request by ID."""
        return db.query(AgentRequest).filter(
            AgentRequest.id == request_id
        ).first()

    @staticmethod
    def process_request(
        db: Session,
        request_id: int
    ) -> AgentRequest:
        """Process a request - check permissions and prepare response.

        CRITICAL: This uses PermissionEngine for final authorization decision.
        The LLM has NO authority here.

        Returns:
            Updated AgentRequest with status and response_data
        """
        agent_request = CommunicationService.get_request_by_id(db, request_id)
        if not agent_request:
            raise ValueError(f"Request {request_id} not found")

        # Get target user (the data owner)
        target_agent = db.query(Agent).filter(
            Agent.id == agent_request.target_agent_id
        ).first()
        target_user = db.query(User).filter(
            User.id == target_agent.user_id
        ).first()

        # Get requesting agent info for audit
        requesting_agent = db.query(Agent).filter(
            Agent.id == agent_request.requesting_agent_id
        ).first()

        requested_fields = agent_request.requested_fields.split(",")

        # Check permissions using Permission Engine
        has_permission = PermissionEngine.check_permission(
            db,
            target_user.id,
            requesting_agent.id,
            agent_request.requested_data_category,
            requested_fields
        )

        # Log the request attempt
        audit_log = AuditLog(
            requesting_agent_id=requesting_agent.id,
            target_user_id=target_user.id,
            data_category=agent_request.requested_data_category,
            requested_fields=agent_request.requested_fields,
            purpose=agent_request.purpose,
            permission_status="ALLOWED" if has_permission else "DENIED",
            result="APPROVED" if has_permission else "DENIED"
        )
        db.add(audit_log)

        # If permission denied, update request and return
        if not has_permission:
            agent_request.status = RequestStatus.DENIED.value
            agent_request.error_message = (
                f"Permission denied. Target user has not authorized "
                f"{agent_request.requested_data_category} access for this agent."
            )
            agent_request.responded_at = datetime.utcnow()
            db.commit()
            db.refresh(agent_request)
            db.commit()  # Commit audit log
            return agent_request

        # Permission granted - get the data
        try:
            response_data = CommunicationService._fetch_requested_data(
                db,
                target_user.id,
                agent_request.requested_data_category,
                requested_fields
            )

            allowed_fields = PermissionEngine.get_allowed_fields(
                db,
                target_user.id,
                requesting_agent.id,
                agent_request.requested_data_category
            )

            audit_log.allowed_fields = ",".join(allowed_fields) if allowed_fields else ""
            audit_log.shared_fields = ",".join(response_data.keys()) if response_data else ""

            agent_request.status = RequestStatus.EXECUTED.value
            agent_request.response_data = response_data
            agent_request.responded_at = datetime.utcnow()

        except Exception as e:
            agent_request.status = RequestStatus.ERROR.value
            agent_request.error_message = str(e)
            agent_request.responded_at = datetime.utcnow()
            audit_log.result = "ERROR"

        db.commit()
        db.refresh(agent_request)
        return agent_request

    @staticmethod
    def _fetch_requested_data(
        db: Session,
        user_id: int,
        data_category: str,
        requested_fields: List[str]
    ) -> Dict[str, Any]:
        """Fetch and filter the requested data.

        This is where DATA MINIMIZATION happens - only return authorized fields.
        """
        if data_category == "calendar":
            return CommunicationService._get_calendar_data(db, user_id, requested_fields)
        elif data_category == "preferences":
            return CommunicationService._get_preferences_data(db, user_id, requested_fields)
        elif data_category == "location":
            return CommunicationService._get_location_data(db, user_id, requested_fields)
        elif data_category == "budget":
            return CommunicationService._get_budget_data(db, user_id, requested_fields)
        else:
            raise ValueError(f"Unknown data category: {data_category}")

    @staticmethod
    def _get_calendar_data(
        db: Session,
        user_id: int,
        requested_fields: List[str]
    ) -> Dict[str, Any]:
        """Extract and filter calendar data.

        Possible fields: free_busy, availability_windows, event_names, descriptions,
                        attendees, locations
        """
        events = DataAccessService.get_user_calendar(db, user_id, user_id)

        response = {}

        if "free_busy" in requested_fields:
            # Return only free/busy status
            free_busy = []
            for event in events:
                free_busy.append({
                    "start_time": event.start_time.isoformat(),
                    "end_time": event.end_time.isoformat(),
                    "is_busy": not event.is_free
                })
            response["free_busy"] = free_busy

        if "availability_windows" in requested_fields:
            # Return periods when user is free
            availability = []
            for event in events:
                if event.is_free:
                    availability.append({
                        "start_time": event.start_time.isoformat(),
                        "end_time": event.end_time.isoformat()
                    })
            response["availability_windows"] = availability

        if "event_names" in requested_fields:
            # Return event names (but no other details)
            response["event_names"] = [
                event.event_name for event in events if not event.is_free
            ]

        if "event_details" in requested_fields:
            # Return full event details (if authorized)
            response["event_details"] = [
                {
                    "event_name": event.event_name,
                    "description": event.description,
                    "start_time": event.start_time.isoformat(),
                    "end_time": event.end_time.isoformat(),
                    "location": event.location,
                    "attendees": event.attendees
                }
                for event in events if not event.is_free
            ]

        return response

    @staticmethod
    def _get_preferences_data(
        db: Session,
        user_id: int,
        requested_fields: List[str]
    ) -> Dict[str, Any]:
        """Extract and filter preferences data."""
        preferences = DataAccessService.get_user_preferences(db, user_id, user_id)

        response = {}
        for pref in preferences:
            if pref.preference_key in requested_fields:
                response[pref.preference_key] = pref.preference_value

        return response

    @staticmethod
    def _get_location_data(
        db: Session,
        user_id: int,
        requested_fields: List[str]
    ) -> Dict[str, Any]:
        """Extract and filter location data.

        Possible fields: left_home, general_area, approximate_distance, exact_gps
        """
        location = DataAccessService.get_user_location(db, user_id, user_id)

        response = {}

        if location:
            if "left_home" in requested_fields:
                response["left_home"] = not location.is_home

            if "location_name" in requested_fields:
                response["location_name"] = location.location_name

            if "exact_gps" in requested_fields:
                response["exact_gps"] = {
                    "latitude": location.latitude,
                    "longitude": location.longitude
                }

        return response

    @staticmethod
    def _get_budget_data(
        db: Session,
        user_id: int,
        requested_fields: List[str]
    ) -> Dict[str, Any]:
        """Extract and filter budget data."""
        budgets = DataAccessService.get_user_budgets(db, user_id, user_id)

        response = {}
        for budget in budgets:
            if budget.category in requested_fields:
                response[budget.category] = {
                    "amount": budget.amount,
                    "currency": budget.currency
                }

        return response
