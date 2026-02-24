"""
Plan executor: consume a validated plan response and run atom functions in topological order.

Input: plan_response dict (same shape as POST /plan response), atoms_registry.
Output: { success: bool, step_results: [...], error?: str }

See core/AGENTS.md § Planner-Validator-Executor Boundary Contract.
"""

import importlib
import re
from typing import Any, Callable

REF_PATTERN = re.compile(r"^\$\{([^}.]+)\.outputs\.([^}]+)\}$")


def execute(plan_response: dict, atoms_registry: dict) -> dict:
    """
    Execute a validated plan.

    Args:
        plan_response: Full response from POST /plan containing:
            - plan: the plan document (target, plan.steps, plan.outputs)
            - validation: { valid, execution_order, ... }
        atoms_registry: Registry mapping atom_id -> atom definition.

    Returns:
        { success: bool, step_results: [...], error?: str }
    """
    validation = plan_response.get("validation") or {}
    if not validation.get("valid"):
        return {
            "success": False,
            "step_results": [],
            "error": "Plan validation failed; refusing to execute.",
        }

    plan_doc = plan_response.get("plan") or {}
    steps = (plan_doc.get("plan") or {}).get("steps") or []
    execution_order: list[str] = validation.get("execution_order") or []

    step_lookup = _build_step_lookup(steps)
    context: dict[str, dict[str, Any]] = {}
    step_results: list[dict] = []

    for step_id in execution_order:
        step = step_lookup.get(step_id)
        if step is None:
            result = _step_failure(
                step_id, "", "STEP_NOT_FOUND",
                f"Step '{step_id}' from execution_order not found in plan.steps",
            )
            step_results.append(result)
            return {"success": False, "step_results": step_results, "error": result["error"]}

        atom_id = step.get("id", "")
        atom_def = atoms_registry.get(atom_id)

        try:
            fn = _resolve_callable(atom_id)
        except ExecutorError as exc:
            result = _step_failure(step_id, atom_id, exc.code, str(exc))
            step_results.append(result)
            return {"success": False, "step_results": step_results, "error": result["error"]}

        try:
            resolved_inputs = _resolve_inputs(step.get("inputs") or {}, context)
        except ExecutorError as exc:
            result = _step_failure(step_id, atom_id, exc.code, str(exc))
            step_results.append(result)
            return {"success": False, "step_results": step_results, "error": result["error"]}

        try:
            return_value = fn(**resolved_inputs)
        except Exception as exc:
            result = _step_failure(
                step_id, atom_id, "STEP_EXECUTION_ERROR",
                f"Atom '{atom_id}' raised: {type(exc).__name__}: {exc}",
            )
            step_results.append(result)
            return {"success": False, "step_results": step_results, "error": result["error"]}

        outputs = _map_outputs(return_value, atom_def)
        context[step_id] = outputs

        step_results.append({
            "step_id": step_id,
            "atom_id": atom_id,
            "status": "completed",
            "outputs": outputs,
            "error": None,
        })

    return {"success": True, "step_results": step_results}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

class ExecutorError(Exception):
    """Structured executor error with an error code."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _build_step_lookup(steps: list[dict]) -> dict[str, dict]:
    """Build step_id -> step dict.  Uses explicit step_id or falls back to index."""
    lookup: dict[str, dict] = {}
    for i, step in enumerate(steps):
        sid = step.get("step_id")
        if isinstance(sid, str) and sid.strip():
            lookup[sid.strip()] = step
        else:
            lookup[str(i)] = step
    return lookup


def _resolve_callable(atom_id: str) -> Callable[..., Any]:
    """
    Map an atom ID to a Python callable.

    Convention (from atoms/AGENTS.md):
        atom_id = "package.domain.action"
        -> module: atoms.package.domain
        -> function: action
    """
    parts = atom_id.split(".")
    if len(parts) < 3:
        raise ExecutorError(
            "UNRESOLVED_ATOM",
            f"Atom ID '{atom_id}' does not follow package.domain.action convention",
        )

    package, domain, action = parts[0], parts[1], ".".join(parts[2:])
    module_path = f"atoms.{package}.{domain}"

    try:
        module = importlib.import_module(module_path)
    except ImportError as exc:
        raise ExecutorError(
            "UNRESOLVED_ATOM",
            f"Cannot import module '{module_path}' for atom '{atom_id}': {exc}",
        ) from exc

    fn = getattr(module, action, None)
    if fn is None or not callable(fn):
        raise ExecutorError(
            "UNRESOLVED_ATOM",
            f"Module '{module_path}' has no callable '{action}' for atom '{atom_id}'",
        )
    return fn


def _resolve_inputs(
    inputs: dict[str, Any],
    context: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """
    Resolve input values: replace ${step_id.outputs.output_name} references
    with concrete values from the execution context.  Literal values pass through.
    """
    resolved: dict[str, Any] = {}
    for key, value in inputs.items():
        if isinstance(value, str):
            m = REF_PATTERN.match(value.strip())
            if m:
                ref_step_id, output_name = m.group(1), m.group(2)
                step_outputs = context.get(ref_step_id)
                if step_outputs is None:
                    raise ExecutorError(
                        "UNRESOLVED_REF",
                        f"Reference '{value}': step '{ref_step_id}' has no outputs in context",
                    )
                if output_name not in step_outputs:
                    raise ExecutorError(
                        "UNRESOLVED_REF",
                        f"Reference '{value}': step '{ref_step_id}' has no output '{output_name}'",
                    )
                resolved[key] = step_outputs[output_name]
                continue
        resolved[key] = value
    return resolved


def _map_outputs(return_value: Any, atom_def: dict | None) -> dict[str, Any]:
    """
    Map a function's return value to named outputs based on the atom definition.

    Rules (from atoms/AGENTS.md):
        - No outputs declared -> {}
        - One output -> { output_name: return_value }
        - Multiple outputs -> return_value is expected to be a dict
    """
    if atom_def is None:
        return {}

    declared = [
        out for out in (atom_def.get("outputs") or [])
        if isinstance(out, dict) and out.get("name")
    ]

    if not declared:
        return {}

    if len(declared) == 1:
        return {declared[0]["name"]: return_value}

    if isinstance(return_value, dict):
        return {out["name"]: return_value.get(out["name"]) for out in declared}

    return {declared[0]["name"]: return_value}


def _step_failure(step_id: str, atom_id: str, code: str, message: str) -> dict:
    return {
        "step_id": step_id,
        "atom_id": atom_id,
        "status": "failed",
        "outputs": {},
        "error": f"[{code}] {message}",
    }
