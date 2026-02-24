"""
API route definitions.
"""

from fastapi import APIRouter

from api.models import ExecuteRequest, ExecuteResponse, PlanRequest, PlanResponse
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

    # Enrich each step with its input schema from the atoms registry so that
    # the frontend can render per-step forms without a separate atoms query.
    plan_obj = (plan_doc.get("plan") or {})
    steps = plan_obj.get("steps") or []
    for step in steps:
        if not isinstance(step, dict):
            continue
        atom_id = step.get("id")
        atom_def = registry.get(atom_id or "")
        if not atom_def:
            continue
        inputs = atom_def.get("inputs") or []
        # Use a shallow copy to avoid leaking internal registry mutation.
        step["input_schema"] = [
            inp for inp in inputs if isinstance(inp, dict) and inp.get("name")
        ]

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


@router.post("/execute", response_model=ExecuteResponse)
def execute_plan(req: ExecuteRequest) -> ExecuteResponse:
    """
    Execute a provided plan with per-step user inputs.

    The client supplies the plan document and a mapping from effective
    step identifiers to input values. The server merges these values
    into each step's inputs, validates the resulting plan, and then
    runs the executor.
    """
    registry = get_atoms_registry()
    plan_doc = req.plan or {}

    # Merge user-provided inputs into each step before validation/execution.
    plan_obj = (plan_doc.get("plan") or {})
    steps = plan_obj.get("steps") or []
    user_inputs = req.user_inputs or {}

    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            continue

        step_id = step.get("step_id")
        if isinstance(step_id, str) and step_id.strip():
            effective_step_id = step_id.strip()
        else:
            effective_step_id = str(index)

        step_user_inputs = user_inputs.get(effective_step_id)
        if not step_user_inputs:
            continue

        existing_inputs = step.get("inputs") or {}
        if not isinstance(existing_inputs, dict):
            existing_inputs = {}

        # User-provided values override any placeholders in the plan.
        merged = {**existing_inputs, **step_user_inputs}
        step["inputs"] = merged

    validation = validate_plan(plan_doc, registry)
    if not validation.get("valid"):
        # When validation fails after injecting user inputs, we still
        # return a structured response but omit execution.
        return ExecuteResponse(plan=plan_doc, validation=validation, execution={"success": False, "step_results": [], "error": "Plan validation failed after applying user inputs."})

    execution = execute({"plan": plan_doc, "validation": validation}, registry)
    return ExecuteResponse(plan=plan_doc, validation=validation, execution=execution)
