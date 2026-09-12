"""Permissions API routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.database.db import get_db
from app.database.schema import User, Agent, Permission
from app.database.communication_schema import AgentRequest
from app.middleware.auth import get_current_user
from app.models.permission import (
    PermissionRequest, PermissionResponse, PermissionsListResponse,
    ConsentScreenResponse, ConsentDecisionRequest, ConsentDecision,
    PermissionType
)
from app.services.permission_service import PermissionService
from app.services.audit_service import AuditService
from typing import List

router = APIRouter(prefix="/api/permissions", tags=["permissions"])


@router.post("/grant", response_model=PermissionResponse)
async def grant_permission(
    permission_data: PermissionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Grant a permission for another agent to access current user's data.

    This endpoint allows a user to manually grant permissions.
    In Phase 6, this will also be triggered by consent screen decisions.
    """
    try:
        permission = PermissionService.grant_permission(
            db,
            grantor_user_id=current_user.id,
            grantee_agent_unique_key=permission_data.grantee_agent_unique_key,
            data_category=permission_data.data_category,
            allowed_fields=permission_data.allowed_fields,
            permission_type=permission_data.permission_type,
            custom_expiry_minutes=permission_data.custom_expiry_minutes,
            purpose=permission_data.purpose
        )

        # Get grantee agent and user info
        grantee_agent = db.query(Agent).filter(
            Agent.id == permission.grantee_agent_id
        ).first()
        grantee_user = db.query(User).filter(
            User.id == grantee_agent.user_id
        ).first()

        return PermissionResponse(
            id=permission.id,
            grantor_id=permission.grantor_id,
            grantor_name=current_user.full_name,
            grantee_agent_id=grantee_agent.id,
            grantee_agent_name=grantee_agent.name,
            grantee_user_id=grantee_user.id,
            grantee_user_name=grantee_user.full_name,
            data_category=permission.data_category,
            allowed_fields=permission.allowed_fields.split(","),
            permission_type=permission.permission_type,
            created_at=permission.created_at,
            expires_at=permission.expires_at,
            is_revoked=permission.is_revoked,
            revoked_at=permission.revoked_at
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/my-permissions", response_model=PermissionsListResponse)
async def get_my_permissions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all permissions granted BY current user.

    Returns:
        Active, revoked, and expired permissions
    """
    try:
        active, revoked, expired = PermissionService.get_user_permissions(
            db,
            current_user.id,
            include_revoked=True,
            include_expired=True
        )

        def format_permissions(perms: List[Permission]) -> List[PermissionResponse]:
            result = []
            for perm in perms:
                grantee_agent = db.query(Agent).filter(
                    Agent.id == perm.grantee_agent_id
                ).first()
                grantee_user = db.query(User).filter(
                    User.id == grantee_agent.user_id
                ).first()

                result.append(PermissionResponse(
                    id=perm.id,
                    grantor_id=perm.grantor_id,
                    grantor_name=current_user.full_name,
                    grantee_agent_id=grantee_agent.id,
                    grantee_agent_name=grantee_agent.name,
                    grantee_user_id=grantee_user.id,
                    grantee_user_name=grantee_user.full_name,
                    data_category=perm.data_category,
                    allowed_fields=perm.allowed_fields.split(","),
                    permission_type=perm.permission_type,
                    created_at=perm.created_at,
                    expires_at=perm.expires_at,
                    is_revoked=perm.is_revoked,
                    revoked_at=perm.revoked_at
                ))
            return result

        return PermissionsListResponse(
            active_permissions=format_permissions(active),
            revoked_permissions=format_permissions(revoked),
            expired_permissions=format_permissions(expired),
            total_count=len(active) + len(revoked) + len(expired)
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/revoke/{permission_id}")
async def revoke_permission(
    permission_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke an existing permission."""
    try:
        permission = db.query(Permission).filter(
            Permission.id == permission_id
        ).first()

        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Permission not found"
            )

        if permission.grantor_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only revoke permissions you granted"
            )

        revoked = PermissionService.revoke_permission(db, permission_id)

        grantee_agent = db.query(Agent).filter(
            Agent.id == revoked.grantee_agent_id
        ).first()
        grantee_user = db.query(User).filter(
            User.id == grantee_agent.user_id
        ).first()

        return {
            "status": "revoked",
            "permission_id": revoked.id,
            "message": f"Permission revoked. {grantee_agent.name} no longer has access to {revoked.data_category}."
        }

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
