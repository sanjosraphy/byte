"""Permission engine - foundation for Phase 4.

This is the core security layer that will control all cross-agent data access.
Phase 2 creates the foundation. Phase 4 will implement full functionality.
"""
from sqlalchemy.orm import Session
from datetime import datetime
from app.database.schema import Permission
from typing import Optional, List


class PermissionEngine:
    """Server-side permission engine - final authority for data access."""

    @staticmethod
    def check_permission(
        db: Session,
        grantor_user_id: int,
        grantee_agent_id: int,
        data_category: str,
        required_fields: Optional[List[str]] = None
    ) -> bool:
        """Check if grantee agent has permission to access data.

        CRITICAL SECURITY RULE:
        This method is the ONLY authority for granting cross-user data access.
        The LLM has NO authorization power.

        Returns:
            True if permission exists and is valid
            False if permission is missing, expired, revoked, or invalid
        """
        permission = db.query(Permission).filter(
            Permission.grantor_id == grantor_user_id,
            Permission.grantee_agent_id == grantee_agent_id,
            Permission.data_category == data_category,
            Permission.is_revoked == False
        ).first()

        if not permission:
            return False

        # Check expiration
        if permission.expires_at and datetime.utcnow() > permission.expires_at:
            return False

        # Check if requested fields are allowed
        if required_fields and permission.allowed_fields:
            allowed = set(permission.allowed_fields.split(","))
            requested = set(required_fields)
            if not requested.issubset(allowed):
                return False

        return True

    @staticmethod
    def get_allowed_fields(
        db: Session,
        grantor_user_id: int,
        grantee_agent_id: int,
        data_category: str
    ) -> Optional[List[str]]:
        """Get list of allowed fields for data access.

        Returns:
            List of field names, or None if no permission
        """
        permission = db.query(Permission).filter(
            Permission.grantor_id == grantor_user_id,
            Permission.grantee_agent_id == grantee_agent_id,
            Permission.data_category == data_category,
            Permission.is_revoked == False
        ).first()

        if not permission:
            return None

        if permission.expires_at and datetime.utcnow() > permission.expires_at:
            return None

        return permission.allowed_fields.split(",") if permission.allowed_fields else []

    @staticmethod
    def grant_permission(
        db: Session,
        grantor_user_id: int,
        grantee_agent_id: int,
        data_category: str,
        allowed_fields: List[str],
        permission_type: str = "duration",
        expires_at: Optional[datetime] = None
    ) -> Permission:
        """Grant permission for data access (will be used in Phase 6)."""
        permission = Permission(
            grantor_id=grantor_user_id,
            grantee_agent_id=grantee_agent_id,
            data_category=data_category,
            allowed_fields=",".join(allowed_fields),
            permission_type=permission_type,
            expires_at=expires_at
        )
        db.add(permission)
        db.commit()
        db.refresh(permission)
        return permission

    @staticmethod
    def revoke_permission(db: Session, permission_id: int) -> None:
        """Revoke a permission (will be used in Phase 8)."""
        permission = db.query(Permission).filter(Permission.id == permission_id).first()
        if permission:
            permission.is_revoked = True
            permission.revoked_at = datetime.utcnow()
            db.commit()
