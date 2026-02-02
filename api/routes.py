"""
API route definitions.
"""

from fastapi import APIRouter

from api.models import PlanRequest, PlanResponse
from core.atoms_loader import load_atoms_registry
from core.plan_validator import validate_plan
from core.planner import plan as planner_plan

router = APIRouter()

# Global atoms registry cache
_atoms_registry: dict | None = None


def get_atoms_registry() -> dict:
    """Get or load atoms registry (cached)."""
    global _atoms_registry
    if _atoms_registry is None:
        _atoms_registry = load_atoms_registry()
    return _atoms_registry


@router.post("/plan", response_model=PlanResponse)
def create_plan(req: PlanRequest) -> PlanResponse:
    """
    Main flow: User Intent -> Planner -> Structured Plan -> Validator -> response.
    Returns the plan and validation result (valid + errors or execution_order).
    Executor can later use plan + validation.execution_order to run steps.
    """
    intent = (req.intent or "").strip()
    registry = get_atoms_registry()
    plan_doc = planner_plan(intent)
    validation = validate_plan(plan_doc, registry)
    return PlanResponse(plan=plan_doc, validation=validation)


@router.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}
