"""Audit log model for tracking user actions."""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlmodel import Field, SQLModel, Column, JSON


class AuditLog(SQLModel, table=True):
    """Audit log model for tracking user actions and system events."""
    
    __tablename__ = "audit_logs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
    action: str = Field(max_length=100, index=True)
    resource: str = Field(max_length=100, index=True)
    resource_id: Optional[int] = None
    details: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    ip_address: Optional[str] = Field(default=None, max_length=45)
    success: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
