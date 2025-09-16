"""
Campaign Services Package

Provides comprehensive campaign management services including:
- Collaboration management and workflow automation
- Campaign brief generation and template management
- Content approval and workflow management
- Performance tracking and analytics
- Communication and notification services
"""

from app.services.campaigns.collaboration_manager import (
    CollaborationManager,
    create_collaboration_manager
)

__all__ = [
    "CollaborationManager",
    "create_collaboration_manager",
]