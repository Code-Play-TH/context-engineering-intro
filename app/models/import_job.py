"""Import job model for CSV/Excel imports."""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlmodel import Field, SQLModel, Column, JSON


class ImportJob(SQLModel, table=True):
    """Import job model for tracking CSV/Excel import progress."""
    
    __tablename__ = "import_jobs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str = Field(max_length=255)
    file_path: str = Field(max_length=500)
    status: str = Field(default="pending", max_length=50)  # pending, validating, processing, completed, failed
    total_rows: int = Field(default=0)
    processed_rows: int = Field(default=0)
    success_count: int = Field(default=0)
    error_count: int = Field(default=0)
    errors: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    created_by: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
