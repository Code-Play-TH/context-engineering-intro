from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class BriefTemplate(Base):
    """
    Brief template model for reusable brief structures.
    Templates can be used to quickly generate briefs for campaigns.
    """
    __tablename__ = "brief_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    
    # Template content with placeholders
    content = Column(Text, nullable=False)
    
    # JSON field for template variables and their default values
    # Example: {"campaign_name": "", "deliverables": [], "deadline": "", "budget": ""}
    variables = Column(JSON, default=dict)
    
    # Template metadata
    category = Column(String(100))  # e.g., "fashion", "beauty", "tech"
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    
    # Audit fields
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    creator = relationship("User", back_populates="brief_templates")
    briefs = relationship("Brief", back_populates="template")

    def __repr__(self):
        return f"<BriefTemplate(id={self.id}, name='{self.name}')>"