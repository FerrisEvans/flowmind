import pytest

from core.plan_validator import validate_plan


def _make_step(step_id="s1", atom_id="globalx.permission.query_permissions",
               target="do something", inputs=None, depends_on=None):
    """Helper to build a minimal valid step dict."""
    step = {"id": atom_id, "target": target, "inputs": {"user_id": "u1"} if inputs is None else inputs}
    if step_id is not None:
        step["step_id"] = step_id
    if depends_on is not None:
        step["depends_on"] = depends_on
    return step


def _plan_doc(steps=None, target="test", outputs=None):
    doc = {"target": target, "plan": {"steps": steps or [_make_step()]}}
    if outputs is not None:
        doc["plan"]["outputs"] = outputs
    return doc


# ── Schema S1-S7 ──────────────────────────────────────────────────────

class TestSchemaValidation:

    def test_s1_missing_target(self, atoms_registry):
        doc = {"plan": {"steps": [_make_step()]}}
        result = validate_plan(doc, atoms_registry)
        assert result["valid"] is False
        assert any(e["code"] == "MISSING_FIELD" and "target" in e["path"] for e in result["errors"])

    def test_s1_target_wrong_type(self, atoms_registry):
        doc = {"target": 123, "plan": {"steps": [_make_step()]}}
        result = validate_plan(doc, atoms_registry)
        assert result["valid"] is False
        assert any(e["code"] == "INVALID_TYPE" for e in result["errors"])

    def test_s2_missing_plan(self, atoms_registry):
        doc = {"target": "x"}
        result = validate_plan(doc, atoms_registry)
        assert result["valid"] is False
        assert any(e["code"] == "MISSING_FIELD" and "plan" in e["path"] for e in result["errors"])

    def test_s2_plan_wrong_type(self, atoms_registry):
        doc = {"target": "x", "plan": "not_a_dict"}
        result = validate_plan(doc, atoms_registry)
        assert result["valid"] is False
        assert any(e["code"] == "INVALID_TYPE" for e in result["errors"])

    def test_s3_missing_steps(self, atoms_registry):
        doc = {"target": "x", "plan": {}}
        result = validate_plan(doc, atoms_registry)
        assert result["valid"] is False
        assert any(e["code"] == "MISSING_FIELD" and "steps" in e["path"] for e in result["errors"])

    def test_s3_empty_steps(self, atoms_registry):
        doc = {"target": "x", "plan": {"steps": []}}
        result = validate_plan(doc, atoms_registry)
        assert result["valid"] is False
        assert any(e["code"] == "EMPTY_STEPS" for e in result["errors"])

    def test_s4_step_missing_fields(self, atoms_registry):
        doc = {"target": "x", "plan": {"steps": [{"something": "else"}]}}
        result = validate_plan(doc, atoms_registry)
        assert result["valid"] is False
        codes = {e["code"] for e in result["errors"]}
        assert "MISSING_FIELD" in codes

    def test_s5_empty_step_id(self, atoms_registry):
        step = _make_step(step_id="")
        doc = _plan_doc(steps=[step])
        result = validate_plan(doc, atoms_registry)
        assert result["valid"] is False
        assert any(e["code"] == "EMPTY_STEP_ID" for e in result["errors"])

    def test_s6_depends_on_wrong_type(self, atoms_registry):
        step = _make_step(depends_on="not_a_list")
        doc = _plan_doc(steps=[step])
        result = validate_plan(doc, atoms_registry)
        assert result["valid"] is False
        assert any(e["code"] == "INVALID_TYPE" and "depends_on" in e["path"] for e in result["errors"])

    def test_s7_outputs_wrong_type(self, atoms_registry):
        doc = _plan_doc(outputs="not_a_dict")
        result = validate_plan(doc, atoms_registry)
        assert result["valid"] is False
        assert any(e["code"] == "INVALID_TYPE" and "outputs" in e["path"] for e in result["errors"])


# ── Uniqueness U1 ─────────────────────────────────────────────────────

class TestUniqueness:

    def test_u1_duplicate_step_id(self, atoms_registry):
        steps = [_make_step(step_id="dup"), _make_step(step_id="dup")]
        doc = _plan_doc(steps=steps)
        result = validate_plan(doc, atoms_registry)
        assert result["valid"] is False
        assert any(e["code"] == "DUPLICATE_STEP_ID" for e in result["errors"])


# ── Atom references A1-A3 ─────────────────────────────────────────────

class TestAtomReferences:

    def test_a1_unknown_atom_id(self, atoms_registry):
        step = _make_step(atom_id="no.such.atom", inputs={"x": "1"})
        doc = _plan_doc(steps=[step])
        result = validate_plan(doc, atoms_registry)
        assert result["valid"] is False
        assert any(e["code"] == "UNKNOWN_ATOM_ID" for e in result["errors"])

    def test_a2_unknown_input_field(self, atoms_registry):
        step = _make_step(inputs={"user_id": "u1", "nonexistent_field": "val"})
        doc = _plan_doc(steps=[step])
        result = validate_plan(doc, atoms_registry)
        assert result["valid"] is False
        assert any(e["code"] == "UNKNOWN_INPUT_FIELD" for e in result["errors"])

    def test_a3_missing_required_input(self, atoms_registry):
        step = _make_step(inputs={})
        doc = _plan_doc(steps=[step])
        result = validate_plan(doc, atoms_registry)
        assert result["valid"] is False
        assert any(e["code"] == "MISSING_REQUIRED_INPUT" for e in result["errors"])


# ── References R1-R2 ──────────────────────────────────────────────────

class TestReferences:

    def test_r1_unknown_step_ref(self, atoms_registry):
        step = _make_step(inputs={"user_id": "${nonexistent.outputs.val}"})
        doc = _plan_doc(steps=[step])
        result = validate_plan(doc, atoms_registry)
        assert result["valid"] is False
        assert any(e["code"] == "UNKNOWN_STEP_REF" for e in result["errors"])

    def test_r2_unknown_output_field(self, atoms_registry):
        s1 = _make_step(step_id="s1")
        s2 = _make_step(
            step_id="s2",
            inputs={"user_id": "${s1.outputs.nonexistent_output}"},
            depends_on=["s1"],
        )
        doc = _plan_doc(steps=[s1, s2])
        result = validate_plan(doc, atoms_registry)
        assert result["valid"] is False
        assert any(e["code"] == "UNKNOWN_OUTPUT_FIELD" for e in result["errors"])


# ── Dependencies D1-D2 ────────────────────────────────────────────────

class TestDependencies:

    def test_d1_unknown_dependency(self, atoms_registry):
        step = _make_step(depends_on=["ghost_step"])
        doc = _plan_doc(steps=[step])
        result = validate_plan(doc, atoms_registry)
        assert result["valid"] is False
        assert any(e["code"] == "UNKNOWN_DEPENDENCY" for e in result["errors"])

    def test_d2_circular_dependency(self, atoms_registry):
        s1 = _make_step(step_id="a", depends_on=["b"])
        s2 = _make_step(step_id="b", depends_on=["a"])
        doc = _plan_doc(steps=[s1, s2])
        result = validate_plan(doc, atoms_registry)
        assert result["valid"] is False
        assert any(e["code"] == "CIRCULAR_DEPENDENCY" for e in result["errors"])


# ── Happy path ────────────────────────────────────────────────────────

class TestHappyPath:

    def test_valid_plan(self, valid_plan_doc, atoms_registry):
        result = validate_plan(valid_plan_doc, atoms_registry)
        assert result["valid"] is True
        assert "execution_order" in result
        assert isinstance(result["execution_order"], list)
        assert len(result["execution_order"]) == 2

    def test_execution_order_respects_dependencies(self, valid_plan_doc, atoms_registry):
        result = validate_plan(valid_plan_doc, atoms_registry)
        order = result["execution_order"]
        assert order.index("query_perm") < order.index("transfer_file")
