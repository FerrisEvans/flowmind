"""
Main entry: wire User Intent -> Planner -> Plan -> Validator -> response.
Exposes HTTP API for testing (e.g. Postman); Executor will consume validated plan + execution_order later.
"""

from pathlib import Path

from fastapi import FastAPI

from api.routes import router
from core.atoms_loader import load_atoms_registry
from core.plan_validator import validate_plan
from core.planner import plan as planner_plan

app = FastAPI(title="flowmind", description="AI-driven dynamic business flow generation")

# Register API routes
app.include_router(router)


def run_main_flow(intent: str, atoms_dir: Path | None = None) -> dict:
    """
    Programmatic entry: run the main flow without HTTP.
    Returns { "plan": ..., "validation": { "valid", "errors" or "execution_order", "warnings" } }.
    """
    registry = load_atoms_registry(atoms_dir)
    plan_doc = planner_plan(intent)
    validation = validate_plan(plan_doc, registry)
    return {"plan": plan_doc, "validation": validation}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
