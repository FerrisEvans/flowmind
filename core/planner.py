"""
Planner: given user intent, produce a structured plan (dict) conforming to plan.dsl.yaml.
Currently provides a mock implementation for wiring the main flow; LLM-based planner can replace it later.
"""


def plan(intent: str) -> dict:
    """
    Produce a structured plan from user intent.
    Returns a plan document (dict) with keys: target, plan.steps, plan.outputs (optional).
    """
    return _mock_plan(intent)


def _mock_plan(intent: str) -> dict:
    """
    Mock planner: returns a fixed sample plan for testing the pipeline.
    Uses real atom ids from atoms/common.json and atoms/globalx.json so that validation passes.
    """
    # Sample: query permission then transfer file (depends on globalx atoms)
    return {
        "target": intent.strip() or "Query user permission and transfer file",
        "plan": {
            "steps": [
                {
                    "step_id": "query_perm",
                    "id": "globalx.permission.query_permissions",
                    "target": "Check if user has transfer permission",
                    "inputs": {"user_id": "user_001"},
                },
                {
                    "step_id": "transfer_file",
                    "id": "globalx.transfer.file_transfer",
                    "target": "Transfer file from sender to receiver",
                    "inputs": {
                        "file_path": "/path/to/file",
                        "sender_id": "user_001",
                        "receiver_id": "user_002",
                    },
                    "depends_on": ["query_perm"],
                },
            ],
            "outputs": {"result": "Transfer completed"},
        },
    }
