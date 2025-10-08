"""Audit logging service."""
from typing import Optional, Dict, Any
from sqlmodel import Session
from app.models.audit_log import AuditLog


class AuditService:
    """Service for logging user actions and system events."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def log_login(
        self,
        user_id: int,
        ip_address: Optional[str],
        success: bool
    ) -> AuditLog:
        """
        Log login attempt.
        
        Args:
            user_id: User ID
            ip_address: IP address of the request
            success: Whether login was successful
            
        Returns:
            Created audit log entry
        """
        log = AuditLog(
            user_id=user_id,
            action="login",
            resource="auth",
            ip_address=ip_address,
            success=success
        )
        
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        
        return log
    
    def log_user_action(
        self,
        user_id: int,
        action: str,
        resource: str,
        resource_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        success: bool = True
    ) -> AuditLog:
        """
        Log user action.
        
        Args:
            user_id: User ID
            action: Action performed (create, update, delete, etc.)
            resource: Resource type (user, campaign, kol, etc.)
            resource_id: ID of the affected resource
            details: Additional details about the action
            ip_address: IP address of the request
            success: Whether action was successful
            
        Returns:
            Created audit log entry
        """
        log = AuditLog(
            user_id=user_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            success=success
        )
        
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        
        return log
