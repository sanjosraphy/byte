"""Field-level permissions API routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.database.schema import User, Agent
from app.database.field_permission_schema import FieldLevelPermission
from app.middleware.auth import get_current_user
from app.models.field_permission import (
    FieldLevelPermissionRequest, FieldLevelPermissionResponse,
    AvailableFieldsResponse, FieldDefinition, PermissionTemplate,
    FieldPermissionType
)
from app.services.field_permission_service import FieldPermissionService
from typing import List

router = APIRouter(prefix="/api/field-permissions", tags=["field-permissions"])


@router.get("/available-fields/{data_category}", response_model=AvailableFieldsResponse)
async def get_available_fields(
    data_category: str,
    current_user: User = Depends(get_current_user)
):
    """Get all available fields for a data category.

    Returns:
        List of fields with descriptions and suggested templates
    """
    if data_category not in FieldPermissionService.AVAILABLE_FIELDS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Data category '{data_category}' not found"
        )

    fields_data = FieldPermissionService.AVAILABLE_FIELDS[data_category]
    fields = [
        FieldDefinition(
            field_name=field_name,
            display_name=field_info["display_name"],
            data_category=data_category,
            description=field_info["description"],
            sensitivity_level=field_info["sensitivity_level"],
            default_permission=FieldPermissionType(field_info["default_permission"])
        )
        for field_name, field_info in fields_data.items()
    ]

    # Get relevant templates
    relevant_templates = [
        PermissionTemplate(
            template_name=template_key,
            description=template["description"],
            data_category=template["data_category"],
            recommended_fields=template["fields"],
            recommended_duration=template["recommended_duration"],
            use_case=template["use_case"]
        )
        for template_key, template in FieldPermissionService.TEMPLATES.items()
        if data_category in template["data_category"]
    ]

    return AvailableFieldsResponse(
        data_category=data_category,
        fields=fields,
        templates=relevant_templates
    )


@router.post("/grant", response_model=FieldLevelPermissionResponse)
async def grant_field_permission(
    permission_data: FieldLevelPermissionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Grant field-level permissions for data access.

    Allows fine-grained control over exactly which fields can be accessed.
    """
    try:
        permission = FieldPermissionService.grant_field_level_permission(
            db,
            grantor_user_id=current_user.id,
            grantee_agent_unique_key=permission_data.grantee_agent_unique_key,
            data_category=permission_data.data_category,
            field_permissions={
                k: v for k, v in permission_data.field_permissions.items()
            },
            permission_type=permission_data.permission_type,
            custom_expiry_minutes=permission_data.custom_expiry_minutes
        )

        grantee_agent = db.query(Agent).filter(
            Agent.id == permission.grantee_agent_id
        ).first()
        grantee_user = db.query(User).filter(
            User.id == grantee_agent.user_id
        ).first()

        return FieldLevelPermissionResponse(
            id=permission.id,
            grantor_id=permission.grantor_id,
            grantor_name=current_user.full_name,
            grantee_agent_id=grantee_agent.id,
            grantee_agent_name=grantee_agent.name,
            grantee_user_id=grantee_user.id,
            grantee_user_name=grantee_user.full_name,
            data_category=permission.data_category,
            field_permissions={k: v for k, v in permission.field_permissions.items()},
            permission_type=permission.permission_type,
            created_at=permission.created_at,
            expires_at=permission.expires_at,
            is_revoked=permission.is_revoked
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/my-field-permissions", response_model=List[FieldLevelPermissionResponse])
async def get_my_field_permissions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all field-level permissions granted by current user."""
    try:
        permissions_by_category = FieldPermissionService.get_user_field_permissions(
            db,
            current_user.id
        )

        result = []
        for category, permissions in permissions_by_category.items():
            for perm in permissions:
                grantee_agent = db.query(Agent).filter(
                    Agent.id == perm.grantee_agent_id
                ).first()
                grantee_user = db.query(User).filter(
                    User.id == grantee_agent.user_id
                ).first()

                result.append(FieldLevelPermissionResponse(
                    id=perm.id,
                    grantor_id=perm.grantor_id,
                    grantor_name=current_user.full_name,
                    grantee_agent_id=grantee_agent.id,
                    grantee_agent_name=grantee_agent.name,
                    grantee_user_id=grantee_user.id,
                    grantee_user_name=grantee_user.full_name,
                    data_category=perm.data_category,
                    field_permissions={k: v for k, v in perm.field_permissions.items()},
                    permission_type=perm.permission_type,
                    created_at=perm.created_at,
                    expires_at=perm.expires_at,
                    is_revoked=perm.is_revoked
                ))

        return result

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/revoke/{permission_id}")
async def revoke_field_permission(
    permission_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke a field-level permission."""
    try:
        permission = db.query(FieldLevelPermission).filter(
            FieldLevelPermission.id == permission_id
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

        revoked = FieldPermissionService.revoke_field_permission(db, permission_id)
        grantee_agent = db.query(Agent).filter(
            Agent.id == revoked.grantee_agent_id
        ).first()

        return {
            "status": "revoked",
            "permission_id": revoked.id,
            "message": f"Field-level permission revoked for {grantee_agent.name}"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
