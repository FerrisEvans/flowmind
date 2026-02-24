"""
Plan validator: validate Planner output (structured plan) against schema and atoms registry.
Input: plan_doc (dict), atoms_registry (dict id -> atom_def).
Output: { valid: bool, errors?: [...], warnings?: [...], execution_order?: [...] }
See core/AGENTS.md for detailed validation rules.
"""

import re
from collections import defaultdict

# Reference format: ${step_id.outputs.output_name}
REF_PATTERN = re.compile(r"^\$\{([^}.]+)\.outputs\.([^}]+)\}$")


def _path(prefix: str, key: str) -> str:
    return f"{prefix}.{key}" if prefix else key


def _is_ref(value) -> bool:
    if not isinstance(value, str):
        return False
    return bool(REF_PATTERN.match(value.strip()))


def _parse_ref(value: str) -> tuple[str, str] | None:
    m = REF_PATTERN.match(value.strip())
    if not m:
        return None
    return m.group(1), m.group(2)


def _step_identifier(step: dict, index: int) -> str:
    sid = step.get("step_id")
    if sid is not None and isinstance(sid, str) and sid.strip():
        return sid.strip()
    return str(index)


def validate_plan(plan_doc: dict, atoms_registry: dict) -> dict:
    """
    Validate plan_doc against schema and atoms_registry.
    Returns { "valid": True, "warnings": [], "execution_order": [...] } or
            { "valid": False, "errors": [ { "code", "message", "path" }, ... ] }.
    """
    errors: list[dict] = []
    warnings: list[dict] = []

    def err(code: str, message: str, path: str) -> None:
        errors.append({"code": code, "message": message, "path": path})

    # --- S1, S2: root target and plan ---
    if not isinstance(plan_doc, dict):
        err("INVALID_TYPE", "Plan document must be an object", "")
        return {"valid": False, "errors": errors}
    if "target" not in plan_doc:
        err("MISSING_FIELD", "Missing required field 'target'", "target")
    elif not isinstance(plan_doc.get("target"), str):
        err("INVALID_TYPE", "Field 'target' must be a string", "target")
    if "plan" not in plan_doc:
        err("MISSING_FIELD", "Missing required field 'plan'", "plan")
    elif not isinstance(plan_doc.get("plan"), dict):
        err("INVALID_TYPE", "Field 'plan' must be an object", "plan")

    raw_plan = plan_doc.get("plan")
    plan = raw_plan if isinstance(raw_plan, dict) else {}
    steps = plan.get("steps")

    # --- S3: plan.steps non-empty array ---
    if steps is None:
        err("MISSING_FIELD", "Missing required field 'plan.steps'", "plan.steps")
    elif not isinstance(steps, list):
        err("INVALID_TYPE", "Field 'plan.steps' must be an array", "plan.steps")
    elif len(steps) == 0:
        err("EMPTY_STEPS", "plan.steps must not be empty", "plan.steps")

    if errors:
        return {"valid": False, "errors": errors}

    # --- S4, S5, S6: each step schema ---
    step_ids: list[str] = []
    for i, step in enumerate(steps):
        base = f"plan.steps[{i}]"
        if not isinstance(step, dict):
            err("INVALID_TYPE", "Step must be an object", base)
            continue
        if "id" not in step:
            err("MISSING_FIELD", "Step must have 'id' (atom id)", f"{base}.id")
        elif not isinstance(step.get("id"), str):
            err("INVALID_TYPE", "Step 'id' must be a string", f"{base}.id")
        if "target" not in step:
            err("MISSING_FIELD", "Step must have 'target'", f"{base}.target")
        elif not isinstance(step.get("target"), str):
            err("INVALID_TYPE", "Step 'target' must be a string", f"{base}.target")
        if "inputs" not in step:
            err("MISSING_FIELD", "Step must have 'inputs'", f"{base}.inputs")
        elif not isinstance(step.get("inputs"), dict):
            err("INVALID_TYPE", "Step 'inputs' must be an object", f"{base}.inputs")
        if "step_id" in step:
            sid = step.get("step_id")
            if not isinstance(sid, str):
                err("INVALID_TYPE", "Step 'step_id' must be a string", f"{base}.step_id")
            elif not (sid and sid.strip()):
                err("EMPTY_STEP_ID", "Step 'step_id' must not be empty", f"{base}.step_id")
        if "depends_on" in step:
            if not isinstance(step.get("depends_on"), list):
                err("INVALID_TYPE", "Step 'depends_on' must be an array", f"{base}.depends_on")
        step_ids.append(_step_identifier(step, i))

    # --- S7: plan.outputs ---
    if "outputs" in plan and plan.get("outputs") is not None and not isinstance(plan.get("outputs"), dict):
        err("INVALID_TYPE", "Field 'plan.outputs' must be an object", "plan.outputs")

    if errors:
        return {"valid": False, "errors": errors}

    # --- U1: step_id uniqueness ---
    seen: set[str] = set()
    for i, sid in enumerate(step_ids):
        if sid in seen:
            err("DUPLICATE_STEP_ID", f"Duplicate step_id: '{sid}'", f"plan.steps[{i}].step_id")
        seen.add(sid)

    # --- Build id -> index and index -> step_id ---
    id_to_index = {step_ids[i]: i for i in range(len(step_ids))}

    # --- A1, A2, A3: atom registry and inputs ---
    for i, step in enumerate(steps):
        if not isinstance(step, dict):
            continue
        base = f"plan.steps[{i}]"
        atom_id = step.get("id")
        if not atom_id:
            continue
        atom = atoms_registry.get(atom_id)
        if not atom:
            err("UNKNOWN_ATOM_ID", f"Unknown atom id: {atom_id!r}", f"{base}.id")
            continue
        atom_inputs = {inp["name"]: inp for inp in (atom.get("inputs") or []) if isinstance(inp, dict) and inp.get("name")}
        atom_outputs = {out["name"] for out in (atom.get("outputs") or []) if isinstance(out, dict) and out.get("name")}
        inputs = step.get("inputs") or {}
        if not isinstance(inputs, dict):
            continue
        for key in inputs:
            if key not in atom_inputs:
                err("UNKNOWN_INPUT_FIELD", f"Unknown input field {key!r} for atom {atom_id}", f"{base}.inputs.{key}")
        for name, inp_def in atom_inputs.items():
            if inp_def.get("required") and name not in inputs:
                err("MISSING_REQUIRED_INPUT", f"Required input {name!r} is missing", f"{base}.inputs")
            elif inp_def.get("required") and name in inputs:
                val = inputs.get(name)
                if val is None or (isinstance(val, str) and not val.strip() and not _is_ref(val)):
                    err("MISSING_REQUIRED_INPUT", f"Required input {name!r} has no value", f"{base}.inputs.{name}")

    # --- Build dependency graph: node = step index; edges from dependency -> dependent ---
    # depends_on: dep -> current. Reference: ref_step -> current.
    graph: dict[int, list[int]] = defaultdict(list)  # node -> list of successors (so edge node -> s)
    in_degree = defaultdict(int)

    for i, step in enumerate(steps):
        if not isinstance(step, dict):
            continue
        # depends_on: each dep must be a known step_id; add edge dep -> i
        for dep in step.get("depends_on") or []:
            if not isinstance(dep, str):
                continue
            dep = dep.strip()
            if dep not in id_to_index:
                err("UNKNOWN_DEPENDENCY", f"Unknown dependency step_id: {dep!r}", f"plan.steps[{i}].depends_on")
                continue
            j = id_to_index[dep]
            graph[j].append(i)
            in_degree[i] = in_degree[i] + 1
        # Input references: ref -> i (implicit dependency)
        inputs = step.get("inputs") or {}
        atom = atoms_registry.get(step.get("id") or "")
        for _key, val in inputs.items():
            if not _is_ref(val):
                continue
            parsed = _parse_ref(val)
            if not parsed:
                continue
            ref_sid, out_name = parsed
            if ref_sid not in id_to_index:
                err("UNKNOWN_STEP_REF", f"Unknown step reference: {ref_sid!r}", f"plan.steps[{i}].inputs")
                continue
            ref_index = id_to_index[ref_sid]
            ref_atom = atoms_registry.get((steps[ref_index] or {}).get("id") or "")
            ref_outputs = {out["name"] for out in (ref_atom.get("outputs") or []) if isinstance(out, dict) and out.get("name")} if ref_atom else set()
            if out_name not in ref_outputs:
                err("UNKNOWN_OUTPUT_FIELD", f"Atom for step {ref_sid!r} has no output {out_name!r}", f"plan.steps[{i}].inputs")
                continue
            # Implicit dependency: ref_sid must run before this step
            if ref_index not in graph or i not in graph[ref_index]:
                graph[ref_index].append(i)
                in_degree[i] = in_degree[i] + 1

    if errors:
        return {"valid": False, "errors": errors}

    # --- D2: topological sort and cycle detection ---
    # in_degree: we only incremented for edges into i; we need full in_degree. Recompute.
    in_degree = {idx: 0 for idx in range(len(steps))}
    for u, succs in graph.items():
        for v in succs:
            in_degree[v] += 1
    queue = [i for i in range(len(steps)) if in_degree[i] == 0]
    order: list[int] = []
    while queue:
        u = queue.pop(0)
        order.append(u)
        for v in graph.get(u, []):
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)
    if len(order) != len(steps):
        # Cycle: find nodes still with in_degree > 0
        cycle_nodes = [step_ids[i] for i in range(len(steps)) if i not in order]
        err("CIRCULAR_DEPENDENCY", f"Circular dependency among steps: {cycle_nodes}", "plan.steps")
        return {"valid": False, "errors": errors}

    execution_order = [step_ids[i] for i in order]
    return {"valid": True, "warnings": warnings, "execution_order": execution_order}
