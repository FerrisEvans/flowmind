"""
Request and response models for API endpoints.
"""

from pydantic import BaseModel


class PlanRequest(BaseModel):
    """Request model for plan creation endpoint."""
    intent: str


class PlanResponse(BaseModel):
    """Response model for plan creation endpoint."""
    plan: dict
    validation: dict
    execution: dict | None = None
