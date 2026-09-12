"""Permission management service."""
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.database.schema import User, Agent, Permission
from app.database.communication_schema import AgentRequest, AuditLog
from app.models.permission import PermissionType, ConsentDecision
from typing import Optional, List, Dict, Tuple


class PermissionService:
    """Service for managing permissions and consent."""

    @staticmethod
    def grant_permission(
        db: Session,
        grantor_user_id: int,
        grantee_agent_unique_key: str,
        data_category: str,
        allowed_fields: List[str],
        permission_type: PermissionType = PermissionType.ONE_HOUR,
        custom_expiry_minutes: Optional[int] = None,
        purpose: Optional[str] = None
    ) -> Permission:
        """Grant a permission for data access.

        Args:
            db: Database session
            grantor_user_id: User ID of the data owner (e.g., Bob)
            grantee_agent_unique_key: Unique key of requesting agent (e.g., "agent_a")
            data_category: What data can be accessed (e.g., "calendar")
            allowed_fields: Which specific fields are allowed
            permission_type: Duration type (one_time, one_hour, etc.)
            custom_expiry_minutes: For CUSTOM type, minutes until expiry
            purpose: Why this permission is being granted

        Returns:
            Permission object
        """
        # Find grantee agent
        grantee_agent = db.query(Agent).filter(
            Agent.unique_key == grantee_agent_unique_key
        ).first()

        if not grantee_agent:
            raise ValueError(f"Agent '{grantee_agent_unique_key}' not found")

        # Calculate expiry time
        expires_at = PermissionService._calculate_expiry(
            permission_type,
            custom_expiry_minutes
        )

        # Create permission
        permission = Permission(
            grantor_id=grantor_user_id,
            grantee_agent_id=grantee_agent.id,
            data_category=data_category,
            allowed_fields=",".join(allowed_fields),
            permission_type=permission_type.value,
            created_at=datetime.utcnow(),
            expires_at=expires_at,
            is_revoked=False
        )

        db.add(permission)
        db.commit()
        db.refresh(permission)

        return permission

    @staticmethod
    def _calculate_expiry(
        permission_type: PermissionType,
        custom_minutes: Optional[int] = None
    ) -> Optional[datetime]:
        """Calculate permission expiry time based on type."""
        now = datetime.utcnow()

        if permission_type == PermissionType.ONE_TIME:
            # One-time permissions expire immediately after use
            # But we'll set a reasonable buffer (1 hour)
            return now + timedelta(hours=1)

        elif permission_type == PermissionType.TEN_MINUTES:
            return now + timedelta(minutes=10)

        elif permission_type == PermissionType.ONE_HOUR:
            return now + timedelta(hours=1)

        elif permission_type == PermissionType.TWENTYFOUR_HOURS:
            return now + timedelta(hours=24)

        elif permission_type == PermissionType.UNTIL_TASK:
            # Task-based permissions need external completion signal
            # Set to 7 days by default
            return now + timedelta(days=7)

        elif permission_type == PermissionType.CUSTOM:
            if custom_minutes is None:
                raise ValueError("custom_expiry_minutes required for CUSTOM type")
            return now + timedelta(minutes=custom_minutes)

        else:  # PERMANENT
            return None  # No expiry

    @staticmethod
    def revoke_permission(db: Session, permission_id: int) -> Permission:
        """Revoke an existing permission.

        Args:
            db: Database session
            permission_id: ID of permission to revoke

        Returns:
            Updated Permission object
        """
        permission = db.query(Permission).filter(
            Permission.id == permission_id
        ).first()

        if not permission:
            raise ValueError(f"Permission {permission_id} not found")

        if permission.is_revoked:
            raise ValueError(f"Permission {permission_id} is already revoked")

        permission.is_revoked = True
        permission.revoked_at = datetime.utcnow()
        db.commit()
        db.refresh(permission)

        return permission

    @staticmethod
    def get_user_permissions(
        db: Session,
        user_id: int,
        include_revoked: bool = False,
        include_expired: bool = False
    ) -> Tuple[List[Permission], List[Permission], List[Permission]]:
        """Get all permissions granted BY a user.

        Returns:
            Tuple of (active_permissions, revoked_permissions, expired_permissions)
        """
        all_permissions = db.query(Permission).filter(
            Permission.grantor_id == user_id
        ).all()

        active = []
        revoked = []
        expired = []

        now = datetime.utcnow()

        for perm in all_permissions:
            if perm.is_revoked:
                revoked.append(perm)
            elif perm.expires_at and now > perm.expires_at:
                expired.append(perm)
            else:
                active.append(perm)

        return active, revoked, expired

    @staticmethod
    def handle_consent_decision(
        db: Session,
        agent_request_id: int,
        decision: ConsentDecision,
        custom_expiry_minutes: Optional[int] = None
    ) -> Optional[Permission]:
        """Process user's decision from consent screen.

        Args:
            db: Database session
            agent_request_id: ID of the AgentRequest that prompted consent
            decision: User's decision (ALLOWED, DENIED, etc.)
            custom_expiry_minutes: If decision is CUSTOM

        Returns:
            Permission object if allowed, None if denied
        """
        agent_request = db.query(AgentRequest).filter(
            AgentRequest.id == agent_request_id
        ).first()

        if not agent_request:
            raise ValueError(f"Agent request {agent_request_id} not found")

        target_agent = db.query(Agent).filter(
            Agent.id == agent_request.target_agent_id
        ).first()

        requesting_agent = db.query(Agent).filter(
            Agent.id == agent_request.requesting_agent_id
        ).first()

        # Map decision to permission type
        permission_type_map = {
            ConsentDecision.ALLOWED_ONCE: PermissionType.ONE_TIME,
            ConsentDecision.ALLOWED_FOR_DURATION: PermissionType.ONE_HOUR,
            ConsentDecision.CUSTOM: PermissionType.CUSTOM,
        }

        if decision == ConsentDecision.DENIED:
            # Log the denial
            audit_log = AuditLog(
                requesting_agent_id=requesting_agent.id,
                target_user_id=target_agent.user_id,
                data_category=agent_request.requested_data_category,
                requested_fields=agent_request.requested_fields,
                purpose=agent_request.purpose,
                permission_status="DENIED",
                user_decision="DENIED",
                result="DENIED"
            )
            db.add(audit_log)
            db.commit()
            return None

        elif decision in permission_type_map:
            perm_type = permission_type_map[decision]
            permission = PermissionService.grant_permission(
                db,
                grantor_user_id=target_agent.user_id,
                grantee_agent_unique_key=requesting_agent.unique_key,
                data_category=agent_request.requested_data_category,
                allowed_fields=agent_request.requested_fields.split(","),
                permission_type=perm_type,
                custom_expiry_minutes=custom_expiry_minutes if decision == ConsentDecision.CUSTOM else None,
                purpose=agent_request.purpose
            )

            # Log the approval
            audit_log = AuditLog(
                requesting_agent_id=requesting_agent.id,
                target_user_id=target_agent.user_id,
                data_category=agent_request.requested_data_category,
                requested_fields=agent_request.requested_fields,
                allowed_fields=agent_request.requested_fields,
                purpose=agent_request.purpose,
                permission_status="ALLOWED",
                user_decision=decision.value.upper(),
                result="APPROVED"
            )
            db.add(audit_log)
            db.commit()

            return permission

        else:
            raise ValueError(f"Invalid decision: {decision}")

    @staticmethod
    def prepare_consent_screen(
        db: Session,
        agent_request_id: int
    ) -> Dict:
        """Prepare data for consent screen UI.

        Returns:
            Dictionary with all information needed to render consent screen
        """
        agent_request = db.query(AgentRequest).filter(
            AgentRequest.id == agent_request_id
        ).first()

        if not agent_request:
            raise ValueError(f"Agent request {agent_request_id} not found")

        requesting_agent = db.query(Agent).filter(
            Agent.id == agent_request.requesting_agent_id
        ).first()
        requesting_user = db.query(User).filter(
            User.id == requesting_agent.user_id
        ).first()

        target_agent = db.query(Agent).filter(
            Agent.id == agent_request.target_agent_id
        ).first()
        target_user = db.query(User).filter(
            User.id == target_agent.user_id
        ).first()

        # Determine what WILL and WON'T be shared
        will_share = agent_request.requested_fields.split(",")
        wont_share = PermissionService._get_fields_not_shared(
            agent_request.requested_data_category,
            will_share
        )

        return {
            "agent_request_id": agent_request_id,
            "requesting_agent_name": requesting_agent.name,
            "requesting_user_name": requesting_user.full_name,
            "what_is_requested": PermissionService._format_request_description(
                agent_request.requested_data_category,
                will_share
            ),
            "who_is_requesting": f"{requesting_agent.name} (on behalf of {requesting_user.full_name})",
            "why_is_it_needed": agent_request.purpose,
            "what_will_be_shared": will_share,
            "what_wont_be_shared": wont_share,
            "permission_options": [
                PermissionType.ONE_TIME.value,
                PermissionType.ONE_HOUR.value,
                PermissionType.TWENTYFOUR_HOURS.value,
                PermissionType.CUSTOM.value
            ]
        }

    @staticmethod
    def _format_request_description(data_category: str, fields: List[str]) -> str:
        """Format a human-readable description of what's being requested."""
        field_descriptions = {
            "calendar": {
                "free_busy": "Your busy/free schedule",
                "availability_windows": "Times when you're available",
                "event_names": "Your event titles",
                "event_details": "Full details of your calendar events"
            },
            "preferences": {
                "movie_genre": "Your movie preferences",
                "cuisine": "Your food preferences"
            },
            "location": {
                "left_home": "Whether you've left home",
                "location_name": "Your current location name",
                "exact_gps": "Your exact GPS coordinates"
            },
            "budget": {
                "entertainment": "Your entertainment budget",
                "travel": "Your travel budget"
            }
        }

        descriptions = []
        if data_category in field_descriptions:
            for field in fields:
                if field in field_descriptions[data_category]:
                    descriptions.append(field_descriptions[data_category][field])

        return ", ".join(descriptions) if descriptions else f"{data_category} data"

    @staticmethod
    def _get_fields_not_shared(data_category: str, shared_fields: List[str]) -> List[str]:
        """Get list of fields that won't be shared."""
        all_fields = {
            "calendar": ["free_busy", "availability_windows", "event_names", "event_details"],
            "preferences": ["movie_genre", "cuisine"],
            "location": ["left_home", "location_name", "exact_gps"],
            "budget": ["entertainment", "travel"]
        }

        if data_category not in all_fields:
            return []

        return [
            field for field in all_fields[data_category]
            if field not in shared_fields
        ]
