import pytest

from core.atoms_loader import load_atoms_registry
from core.plan_validator import validate_plan
from core.planner import _mock_plan


@pytest.fixture
def atoms_registry():
    """Real atoms registry loaded from atoms/*.json."""
    return load_atoms_registry()


@pytest.fixture
def valid_plan_doc():
    """A plan document known to pass validation (the mock plan)."""
    return _mock_plan("test intent")


@pytest.fixture
def valid_plan_response(valid_plan_doc, atoms_registry):
    """Fully validated plan response ready for the executor."""
    validation = validate_plan(valid_plan_doc, atoms_registry)
    assert validation["valid"] is True
    return {"plan": valid_plan_doc, "validation": validation}


@pytest.fixture
def minimal_registry():
    """Small inline registry for tests that need precise control over atom defs."""
    return {
        "test.math.add": {
            "id": "test.math.add",
            "inputs": [
                {"name": "a", "type": "int", "required": True},
                {"name": "b", "type": "int", "required": True},
            ],
            "outputs": [
                {"name": "result", "type": "int"},
            ],
        },
        "test.math.noop": {
            "id": "test.math.noop",
            "inputs": [
                {"name": "x", "type": "string", "required": False},
            ],
            "outputs": None,
        },
    }
