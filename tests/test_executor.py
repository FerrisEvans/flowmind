import pytest

from core.executor import (
    ExecutorError,
    _map_outputs,
    _resolve_callable,
    _resolve_inputs,
    execute,
)


# ── _resolve_callable ─────────────────────────────────────────────────

class TestResolveCallable:

    def test_valid_atom(self):
        fn = _resolve_callable("globalx.permission.query_permissions")
        assert callable(fn)
        assert fn.__name__ == "query_permissions"

    def test_bad_format(self):
        with pytest.raises(ExecutorError) as exc_info:
            _resolve_callable("bad")
        assert exc_info.value.code == "UNRESOLVED_ATOM"

    def test_missing_module(self):
        with pytest.raises(ExecutorError) as exc_info:
            _resolve_callable("no.such.module")
        assert exc_info.value.code == "UNRESOLVED_ATOM"

    def test_missing_function(self):
        with pytest.raises(ExecutorError) as exc_info:
            _resolve_callable("globalx.permission.nonexistent_fn")
        assert exc_info.value.code == "UNRESOLVED_ATOM"


# ── _resolve_inputs ───────────────────────────────────────────────────

class TestResolveInputs:

    def test_literals_pass_through(self):
        inputs = {"a": "hello", "b": 42, "c": True}
        result = _resolve_inputs(inputs, {})
        assert result == inputs

    def test_reference_resolves(self):
        context = {"s1": {"val": 100}}
        inputs = {"x": "${s1.outputs.val}"}
        result = _resolve_inputs(inputs, context)
        assert result == {"x": 100}

    def test_unresolved_step(self):
        with pytest.raises(ExecutorError) as exc_info:
            _resolve_inputs({"x": "${ghost.outputs.val}"}, {})
        assert exc_info.value.code == "UNRESOLVED_REF"

    def test_unresolved_output(self):
        context = {"s1": {"other": 1}}
        with pytest.raises(ExecutorError) as exc_info:
            _resolve_inputs({"x": "${s1.outputs.missing}"}, context)
        assert exc_info.value.code == "UNRESOLVED_REF"

    def test_mixed_literals_and_refs(self):
        context = {"s1": {"out": "resolved_value"}}
        inputs = {"a": "literal", "b": "${s1.outputs.out}"}
        result = _resolve_inputs(inputs, context)
        assert result == {"a": "literal", "b": "resolved_value"}


# ── _map_outputs ──────────────────────────────────────────────────────

class TestMapOutputs:

    def test_no_outputs_declared(self):
        atom_def = {"id": "x", "outputs": None}
        assert _map_outputs("anything", atom_def) == {}

    def test_empty_outputs_list(self):
        atom_def = {"id": "x", "outputs": []}
        assert _map_outputs("anything", atom_def) == {}

    def test_single_output(self):
        atom_def = {"id": "x", "outputs": [{"name": "result"}]}
        assert _map_outputs(42, atom_def) == {"result": 42}

    def test_multi_output_dict(self):
        atom_def = {"id": "x", "outputs": [{"name": "a"}, {"name": "b"}]}
        assert _map_outputs({"a": 1, "b": 2}, atom_def) == {"a": 1, "b": 2}

    def test_none_atom_def(self):
        assert _map_outputs("anything", None) == {}


# ── execute (integration) ─────────────────────────────────────────────

class TestExecute:

    def test_happy_path(self, valid_plan_response, atoms_registry):
        result = execute(valid_plan_response, atoms_registry)
        assert result["success"] is True
        assert len(result["step_results"]) == 2
        assert result["step_results"][0]["step_id"] == "query_perm"
        assert result["step_results"][0]["status"] == "completed"
        assert result["step_results"][1]["step_id"] == "transfer_file"
        assert result["step_results"][1]["status"] == "completed"

    def test_invalid_plan(self, atoms_registry):
        resp = {"plan": {}, "validation": {"valid": False}}
        result = execute(resp, atoms_registry)
        assert result["success"] is False
        assert "validation failed" in result["error"].lower()

    def test_step_runtime_error(self, atoms_registry):
        """Plan referencing a valid atom, but we sabotage the inputs to trigger a TypeError."""
        plan_doc = {
            "target": "test",
            "plan": {
                "steps": [{
                    "step_id": "bad_call",
                    "id": "globalx.permission.query_permissions",
                    "target": "x",
                    "inputs": {},
                }],
            },
        }
        validation = {"valid": True, "execution_order": ["bad_call"]}
        result = execute({"plan": plan_doc, "validation": validation}, atoms_registry)
        assert result["success"] is False
        assert result["step_results"][0]["status"] == "failed"
        assert "STEP_EXECUTION_ERROR" in result["step_results"][0]["error"]

    def test_execute_with_references(self, atoms_registry):
        """Step 2 references step 1's output."""
        plan_doc = {
            "target": "ref test",
            "plan": {
                "steps": [
                    {
                        "step_id": "check",
                        "id": "globalx.permission.query_permissions",
                        "target": "check perm",
                        "inputs": {"user_id": "u1"},
                    },
                    {
                        "step_id": "quota",
                        "id": "globalx.space.query_quota",
                        "target": "check quota",
                        "inputs": {"user_id": "u1"},
                        "depends_on": ["check"],
                    },
                ],
            },
        }
        validation = {"valid": True, "execution_order": ["check", "quota"]}
        result = execute({"plan": plan_doc, "validation": validation}, atoms_registry)
        assert result["success"] is True
        assert "has_permission" in result["step_results"][0]["outputs"]
        assert "quota" in result["step_results"][1]["outputs"]

    def test_step_not_found(self, atoms_registry):
        plan_doc = {"target": "x", "plan": {"steps": []}}
        validation = {"valid": True, "execution_order": ["ghost"]}
        result = execute({"plan": plan_doc, "validation": validation}, atoms_registry)
        assert result["success"] is False
        assert "STEP_NOT_FOUND" in result["step_results"][0]["error"]
