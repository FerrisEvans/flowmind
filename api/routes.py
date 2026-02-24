"""
API route definitions.
"""

from fastapi import APIRouter

from api.models import PlanRequest, PlanResponse
from core.atoms_loader import load_atoms_registry
from core.executor import execute
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
    Main flow: User Intent -> Planner -> Validator -> Executor -> Response.
    If validation passes, the plan is executed immediately and the result is
    returned alongside the plan and validation output.
    """
    intent = (req.intent or "").strip()
    registry = get_atoms_registry()
    plan_doc = planner_plan(intent, atoms_registry=registry)
    validation = validate_plan(plan_doc, registry)

    execution = None
    if validation.get("valid"):
        plan_response = {"plan": plan_doc, "validation": validation}
        execution = execute(plan_response, registry)

    return PlanResponse(plan=plan_doc, validation=validation, execution=execution)


@router.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}
