"""
Request and response models for API endpoints.
"""

from typing import Any, Dict

from pydantic import BaseModel


class PlanRequest(BaseModel):
    """Request model for plan creation endpoint."""
    intent: str


class PlanResponse(BaseModel):
    """Response model for plan creation endpoint."""
    plan: dict
    validation: dict
    execution: dict | None = None


class ExecuteRequest(BaseModel):
    """
    Request model for execution endpoint.

    Expects a full plan document (same shape as PlanResponse.plan) and
    optional prior validation plus per-step user inputs.
    """

    plan: Dict[str, Any]
    validation: Dict[str, Any] | None = None
    # Mapping from effective step_id -> { input_name: value }
    user_inputs: Dict[str, Dict[str, Any]]


class ExecuteResponse(BaseModel):
    """
    Response model for execution endpoint.

    Mirrors PlanResponse but execution is required once validation runs.
    """

    plan: dict
    validation: dict
    execution: dict
