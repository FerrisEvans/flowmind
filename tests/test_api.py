from unittest.mock import patch

from fastapi.testclient import TestClient

from core.planner import _mock_plan
from main import app

client = TestClient(app)


def _patched_plan(intent, **kwargs):
    """Bypass LLM call; always return mock plan."""
    return _mock_plan(intent)


class TestHealthEndpoint:

    def test_health(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestPlanEndpoint:

    @patch("api.routes.planner_plan", side_effect=_patched_plan)
    def test_plan_returns_200(self, _mock):
        resp = client.post("/plan", json={"intent": "Transfer a file"})
        assert resp.status_code == 200

    @patch("api.routes.planner_plan", side_effect=_patched_plan)
    def test_plan_response_shape(self, _mock):
        resp = client.post("/plan", json={"intent": "Transfer a file"})
        data = resp.json()
        assert "plan" in data
        assert "validation" in data
        assert "execution" in data

    @patch("api.routes.planner_plan", side_effect=_patched_plan)
    def test_plan_execution_runs_on_valid_plan(self, _mock):
        resp = client.post("/plan", json={"intent": "Transfer a file"})
        data = resp.json()
        assert data["validation"]["valid"] is True
        assert data["execution"] is not None
        assert isinstance(data["execution"]["success"], bool)
        assert isinstance(data["execution"]["step_results"], list)

    @patch("api.routes.planner_plan", side_effect=_patched_plan)
    def test_plan_empty_intent(self, _mock):
        resp = client.post("/plan", json={"intent": ""})
        assert resp.status_code == 200
        data = resp.json()
        assert "plan" in data
