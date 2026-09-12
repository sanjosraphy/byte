"""Audit logging API routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.database.schema import User, Agent
from app.database.communication_schema import AuditLog
from app.middleware.auth import get_current_user
from app.services.audit_service import AuditService
from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional


class AuditLogResponse(BaseModel):
    """Audit log response model."""
    id: int
    requesting_agent_id: int
    requesting_agent_name: str
    requesting_user_id: int
    requesting_user_name: str
    target_user_id: int
    target_user_name: str
    data_category: str
    requested_fields: str
    allowed_fields: Optional[str]
    shared_fields: Optional[str]
    purpose: str
    permission_status: str
    user_decision: Optional[str]
    result: str
    created_at: datetime

    class Config:
        from_attributes = True


class AuditSummaryResponse(BaseModel):
    """Audit summary response."""
    period_days: int
    total_requests: int
    by_permission_status: dict
    by_data_category: dict
    by_result: dict
    allowed_count: int
    denied_count: int
    pending_count: int


router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("/logs/my-data", response_model=List[AuditLogResponse])
async def get_my_data_access_logs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = 30,
    limit: int = 100
):
    """Get audit logs of requests for current user's data.

    Returns all cross-agent requests that targeted this user's data.
    """
    try:
        logs = AuditService.get_user_audit_logs(
            db,
            current_user.id,
            days_back=days,
            limit=limit
        )

        result = []
        for log in logs:
            requesting_agent = db.query(Agent).filter(
                Agent.id == log.requesting_agent_id
            ).first()
            requesting_user = None
            if requesting_agent:
                from app.database.schema import User as UserModel
                requesting_user = db.query(UserModel).filter(
                    UserModel.id == requesting_agent.user_id
                ).first()

            target_user = db.query(User).filter(
                User.id == log.target_user_id
            ).first()

            result.append(AuditLogResponse(
                id=log.id,
                requesting_agent_id=log.requesting_agent_id,
                requesting_agent_name=requesting_agent.name if requesting_agent else "Unknown",
                requesting_user_id=requesting_user.id if requesting_user else 0,
                requesting_user_name=requesting_user.full_name if requesting_user else "Unknown",
                target_user_id=log.target_user_id,
                target_user_name=target_user.full_name if target_user else "Unknown",
                data_category=log.data_category,
                requested_fields=log.requested_fields,
                allowed_fields=log.allowed_fields,
                shared_fields=log.shared_fields,
                purpose=log.purpose,
                permission_status=log.permission_status,
                user_decision=log.user_decision,
                result=log.result,
                created_at=log.created_at
            ))

        return result

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/logs/my-requests", response_model=List[AuditLogResponse])
async def get_my_requests_logs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = 30,
    limit: int = 100
):
    """Get audit logs of requests made BY current user's agent.

    Returns all cross-agent requests initiated by this user.
    """
    try:
        # Get user's agent
        agent = db.query(Agent).filter(
            Agent.user_id == current_user.id
        ).first()

        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Your agent not found"
            )

        logs = AuditService.get_agent_audit_logs(
            db,
            agent.id,
            days_back=days,
            limit=limit
        )

        result = []
        for log in logs:
            requesting_agent = db.query(Agent).filter(
                Agent.id == log.requesting_agent_id
            ).first()
            target_user = db.query(User).filter(
                User.id == log.target_user_id
            ).first()

            result.append(AuditLogResponse(
                id=log.id,
                requesting_agent_id=log.requesting_agent_id,
                requesting_agent_name=requesting_agent.name if requesting_agent else "Unknown",
                requesting_user_id=current_user.id,
                requesting_user_name=current_user.full_name,
                target_user_id=log.target_user_id,
                target_user_name=target_user.full_name if target_user else "Unknown",
                data_category=log.data_category,
                requested_fields=log.requested_fields,
                allowed_fields=log.allowed_fields,
                shared_fields=log.shared_fields,
                purpose=log.purpose,
                permission_status=log.permission_status,
                user_decision=log.user_decision,
                result=log.result,
                created_at=log.created_at
            ))

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/summary", response_model=AuditSummaryResponse)
async def get_audit_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = 7
):
    """Get summary statistics of data access for current user.

    Shows total requests, breakdown by status, categories, etc.
    """
    try:
        summary = AuditService.get_audit_summary(
            db,
            current_user.id,
            days_back=days
        )

        return AuditSummaryResponse(**summary)

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
