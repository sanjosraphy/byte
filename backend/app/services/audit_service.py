"""Audit logging service."""
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.database.communication_schema import AuditLog
from app.database.schema import Agent, User
from typing import List, Optional


class AuditService:
    """Service for audit logging and queries."""

    @staticmethod
    def log_request(
        db: Session,
        requesting_agent_id: int,
        target_user_id: int,
        data_category: str,
        requested_fields: str,
        purpose: str,
        permission_status: str,
        result: str,
        allowed_fields: Optional[str] = None,
        shared_fields: Optional[str] = None,
        user_decision: Optional[str] = None
    ) -> AuditLog:
        """Log a cross-agent data request.

        Args:
            db: Database session
            requesting_agent_id: Agent making the request
            target_user_id: User whose data is being requested
            data_category: Type of data (calendar, preferences, etc.)
            requested_fields: Comma-separated fields requested
            purpose: Why the data was requested
            permission_status: ALLOWED, DENIED, PENDING_CONSENT, EXPIRED, REVOKED
            result: SUCCESS, DENIED, ERROR, PENDING
            allowed_fields: What was allowed by permission
            shared_fields: What was actually shared
            user_decision: User's decision (APPROVED, DENIED, etc.)

        Returns:
            AuditLog object
        """
        audit_log = AuditLog(
            requesting_agent_id=requesting_agent_id,
            target_user_id=target_user_id,
            data_category=data_category,
            requested_fields=requested_fields,
            allowed_fields=allowed_fields,
            shared_fields=shared_fields,
            purpose=purpose,
            permission_status=permission_status,
            user_decision=user_decision,
            result=result,
            created_at=datetime.utcnow()
        )

        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)

        return audit_log

    @staticmethod
    def get_user_audit_logs(
        db: Session,
        user_id: int,
        days_back: int = 30,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs for a user's data access.

        Args:
            db: Database session
            user_id: User whose data access logs to retrieve
            days_back: How many days back to look
            limit: Maximum number of logs to return

        Returns:
            List of AuditLog objects
        """
        cutoff_time = datetime.utcnow() - timedelta(days=days_back)

        return db.query(AuditLog).filter(
            AuditLog.target_user_id == user_id,
            AuditLog.created_at >= cutoff_time
        ).order_by(
            AuditLog.created_at.desc()
        ).limit(limit).all()

    @staticmethod
    def get_agent_audit_logs(
        db: Session,
        agent_id: int,
        days_back: int = 30,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs of requests made BY an agent.

        Args:
            db: Database session
            agent_id: Agent whose requests to log
            days_back: How many days back to look
            limit: Maximum number of logs to return

        Returns:
            List of AuditLog objects
        """
        cutoff_time = datetime.utcnow() - timedelta(days=days_back)

        return db.query(AuditLog).filter(
            AuditLog.requesting_agent_id == agent_id,
            AuditLog.created_at >= cutoff_time
        ).order_by(
            AuditLog.created_at.desc()
        ).limit(limit).all()

    @staticmethod
    def get_audit_summary(
        db: Session,
        user_id: int,
        days_back: int = 7
    ) -> dict:
        """Get summary statistics of data access.

        Args:
            db: Database session
            user_id: User to get summary for
            days_back: How many days back to summarize

        Returns:
            Dictionary with summary statistics
        """
        cutoff_time = datetime.utcnow() - timedelta(days=days_back)

        logs = db.query(AuditLog).filter(
            AuditLog.target_user_id == user_id,
            AuditLog.created_at >= cutoff_time
        ).all()

        # Count by status
        status_counts = {}
        category_counts = {}
        result_counts = {}

        for log in logs:
            status_counts[log.permission_status] = status_counts.get(log.permission_status, 0) + 1
            category_counts[log.data_category] = category_counts.get(log.data_category, 0) + 1
            result_counts[log.result] = result_counts.get(log.result, 0) + 1

        return {
            "period_days": days_back,
            "total_requests": len(logs),
            "by_permission_status": status_counts,
            "by_data_category": category_counts,
            "by_result": result_counts,
            "allowed_count": status_counts.get("ALLOWED", 0),
            "denied_count": status_counts.get("DENIED", 0),
            "pending_count": status_counts.get("PENDING_CONSENT", 0)
        }
