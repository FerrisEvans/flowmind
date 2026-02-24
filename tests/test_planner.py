import json

import pytest

from core.plan_validator import validate_plan
from core.planner import (
    _format_atom_for_prompt,
    _mock_plan,
    _parse_plan_response,
    plan,
)


class TestMockPlan:

    def test_structure(self):
        doc = _mock_plan("some intent")
        assert isinstance(doc, dict)
        assert "target" in doc
        assert "plan" in doc
        assert isinstance(doc["plan"]["steps"], list)
        assert len(doc["plan"]["steps"]) > 0
        assert "outputs" in doc["plan"]

    def test_validates(self, atoms_registry):
        doc = _mock_plan("test")
        result = validate_plan(doc, atoms_registry)
        assert result["valid"] is True

    def test_uses_intent_as_target(self):
        doc = _mock_plan("Transfer my files")
        assert doc["target"] == "Transfer my files"


class TestParsePlanResponse:

    def test_valid_json(self):
        raw = json.dumps({"target": "x", "plan": {"steps": []}})
        result = _parse_plan_response(raw)
        assert result["target"] == "x"

    def test_markdown_wrapped(self):
        inner = json.dumps({"target": "wrapped"})
        raw = f"```json\n{inner}\n```"
        result = _parse_plan_response(raw)
        assert result["target"] == "wrapped"

    def test_invalid_json(self):
        with pytest.raises(ValueError):
            _parse_plan_response("not json at all")


class TestFormatAtomForPrompt:

    def test_basic_formatting(self):
        atom = {
            "id": "test.svc.action",
            "description": "Does something",
            "inputs": [
                {"name": "x", "required": True, "description": "input x"},
            ],
            "outputs": [
                {"name": "y", "description": "output y"},
            ],
        }
        text = _format_atom_for_prompt(atom)
        assert "test.svc.action" in text
        assert "Does something" in text
        assert "x" in text
        assert "(required)" in text
        assert "y" in text

    def test_no_outputs(self):
        atom = {"id": "test.svc.noop", "inputs": [], "outputs": []}
        text = _format_atom_for_prompt(atom)
        assert "(none)" in text


class TestPlanFallback:

    def test_falls_back_to_mock_without_env(self, atoms_registry, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        doc = plan("test intent", atoms_registry=atoms_registry)
        assert "target" in doc
        assert "plan" in doc
