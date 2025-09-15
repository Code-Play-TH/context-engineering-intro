"""
Audit and logging models.

Defines AuditLog, ERPNextSyncLog, and ExcelOperation models for system tracking.
"""

import json
from datetime import datetime
from typing import Optional, Any

from sqlmodel import Field, Relationship

from app.models.base import BaseModel


class AuditLog(BaseModel, table=True):
    """
    Audit log model for tracking all system changes.
    
    Provides complete audit trail for compliance and debugging.
    """
    
    # Record identification
    table_name: str = Field(
        max_length=100,
        index=True,
        description="Database table name"
    )
    record_id: int = Field(
        index=True,
        description="ID of the affected record"
    )
    
    # User and action information
    user_id: Optional[int] = Field(
        default=None,
        foreign_key="user.id",
        description="User who performed the action"
    )
    action: str = Field(
        max_length=50,
        index=True,
        description="Action performed (create, update, delete)"
    )
    
    # Change tracking
    old_values_json: Optional[str] = Field(
        default=None,
        description="JSON representation of old values"
    )
    new_values_json: Optional[str] = Field(
        default=None,
        description="JSON representation of new values"
    )
    
    # Request metadata
    ip_address: Optional[str] = Field(
        default=None,
        max_length=45,
        description="IP address of the request"
    )
    user_agent: Optional[str] = Field(
        default=None,
        max_length=500,
        description="User agent string"
    )
    
    # Relationships
    user: Optional["User"] = Relationship()
    
    @property
    def old_values(self) -> dict[str, Any]:
        """
        Get old values as dictionary.
        
        Returns:
            dict: Old values or empty dict
        """
        if not self.old_values_json:
            return {}
        try:
            return json.loads(self.old_values_json)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    @old_values.setter
    def old_values(self, value: dict[str, Any]) -> None:
        """
        Set old values from dictionary.
        
        Args:
            value: Old values dictionary
        """
        self.old_values_json = json.dumps(value, default=str)
    
    @property
    def new_values(self) -> dict[str, Any]:
        """
        Get new values as dictionary.
        
        Returns:
            dict: New values or empty dict
        """
        if not self.new_values_json:
            return {}
        try:
            return json.loads(self.new_values_json)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    @new_values.setter
    def new_values(self, value: dict[str, Any]) -> None:
        """
        Set new values from dictionary.
        
        Args:
            value: New values dictionary
        """
        self.new_values_json = json.dumps(value, default=str)
    
    def get_changed_fields(self) -> list[str]:
        """
        Get list of fields that changed.
        
        Returns:
            list[str]: List of changed field names
        """
        old = self.old_values
        new = self.new_values
        
        changed = []
        all_keys = set(old.keys()) | set(new.keys())
        
        for key in all_keys:
            if old.get(key) != new.get(key):
                changed.append(key)
        
        return changed


class ERPNextSyncLog(BaseModel, table=True):
    """
    ERPNext synchronization log model.
    
    Tracks all synchronization attempts with ERPNext system.
    """
    
    # Entity information
    entity_type: str = Field(
        max_length=100,
        index=True,
        description="Type of entity (customer_requirement, product, etc.)"
    )
    entity_id: int = Field(
        index=True,
        description="Local entity ID"
    )
    erpnext_id: Optional[str] = Field(
        default=None,
        max_length=255,
        description="ERPNext document ID"
    )
    
    # Sync operation
    sync_action: str = Field(
        max_length=50,
        description="Sync action (create, update, delete, fetch)"
    )
    sync_status: str = Field(
        max_length=50,
        index=True,
        description="Sync status (success, failed, pending)"
    )
    
    # Error handling
    error_message: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Error message if sync failed"
    )
    retry_count: int = Field(
        default=0,
        ge=0,
        description="Number of retry attempts"
    )
    
    # Timing
    synced_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When sync was attempted"
    )
    
    @property
    def is_successful(self) -> bool:
        """
        Check if sync was successful.
        
        Returns:
            bool: True if sync succeeded
        """
        return self.sync_status == "success"
    
    @property
    def needs_retry(self) -> bool:
        """
        Check if sync needs retry.
        
        Returns:
            bool: True if failed and retry count is reasonable
        """
        return self.sync_status == "failed" and self.retry_count < 3
    
    def mark_success(self, erpnext_id: str) -> None:
        """
        Mark sync as successful.
        
        Args:
            erpnext_id: ERPNext document ID
        """
        self.sync_status = "success"
        self.erpnext_id = erpnext_id
        self.error_message = None
        self.synced_at = datetime.utcnow()
        self.touch()
    
    def mark_failed(self, error_message: str) -> None:
        """
        Mark sync as failed.
        
        Args:
            error_message: Error description
        """
        self.sync_status = "failed"
        self.error_message = error_message
        self.retry_count += 1
        self.synced_at = datetime.utcnow()
        self.touch()


class ExcelOperation(BaseModel, table=True):
    """
    Excel import/export operation log.
    
    Tracks all Excel file operations for auditing and debugging.
    """
    
    # Operation details
    operation_type: str = Field(
        max_length=50,
        index=True,
        description="Operation type (import, export)"
    )
    file_name: str = Field(
        max_length=255,
        description="Original file name"
    )
    file_path: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Stored file path"
    )
    
    # User information
    user_id: int = Field(
        foreign_key="user.id",
        description="User who performed the operation"
    )
    
    # Operation results
    status: str = Field(
        max_length=50,
        index=True,
        description="Operation status (success, failed, partial)"
    )
    records_processed: int = Field(
        default=0,
        ge=0,
        description="Number of records processed"
    )
    records_successful: int = Field(
        default=0,
        ge=0,
        description="Number of successful records"
    )
    records_failed: int = Field(
        default=0,
        ge=0,
        description="Number of failed records"
    )
    
    # Error tracking
    errors_json: Optional[str] = Field(
        default=None,
        description="JSON array of error messages"
    )
    
    # Relationships
    user: "User" = Relationship()
    
    @property
    def errors(self) -> list[dict[str, Any]]:
        """
        Get errors as list of dictionaries.
        
        Returns:
            list[dict]: Error list or empty list
        """
        if not self.errors_json:
            return []
        try:
            return json.loads(self.errors_json)
        except (json.JSONDecodeError, TypeError):
            return []
    
    @errors.setter
    def errors(self, value: list[dict[str, Any]]) -> None:
        """
        Set errors from list of dictionaries.
        
        Args:
            value: Errors list
        """
        self.errors_json = json.dumps(value, default=str)
    
    @property
    def success_rate(self) -> float:
        """
        Calculate success rate percentage.
        
        Returns:
            float: Success rate (0.0 to 100.0)
        """
        if self.records_processed == 0:
            return 0.0
        return (self.records_successful / self.records_processed) * 100.0
    
    def add_error(self, row_number: int, field: str, error_message: str) -> None:
        """
        Add an error to the operation log.
        
        Args:
            row_number: Excel row number where error occurred
            field: Field name that caused the error
            error_message: Error description
        """
        errors = self.errors
        errors.append({
            "row": row_number,
            "field": field,
            "message": error_message,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.errors = errors
        self.records_failed += 1
        self.touch()
    
    def mark_record_successful(self) -> None:
        """Increment successful record count."""
        self.records_successful += 1
        self.records_processed += 1
        self.touch()
    
    def finalize_operation(self) -> None:
        """
        Finalize operation and set status.
        
        Sets status based on success/failure ratio.
        """
        if self.records_failed == 0:
            self.status = "success"
        elif self.records_successful == 0:
            self.status = "failed"
        else:
            self.status = "partial"
        
        self.touch()