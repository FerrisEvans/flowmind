"""
Planner: given user intent, produce a structured plan (dict) conforming to plan.dsl.yaml.
Uses LLM to generate plans from user intent and available atomic services.
"""

import json
from typing import Optional

from core.atoms_loader import load_atoms_registry
from core.provider import LLMProvider, get_default_provider


def plan(intent: str, atoms_registry: Optional[dict] = None, llm_provider: Optional[LLMProvider] = None) -> dict:
    """
    Produce a structured plan from user intent using LLM.

    Args:
        intent: User's natural language intent/request.
        atoms_registry: Optional atoms registry. If None, loads from atoms/*.json.
        llm_provider: Optional LLM provider. If None, uses default from environment.

    Returns:
        Plan document (dict) with keys: target, plan.steps, plan.outputs (optional).
        Falls back to mock plan if LLM call fails.
    """
    if atoms_registry is None:
        atoms_registry = load_atoms_registry()
    if llm_provider is None:
        try:
            llm_provider = get_default_provider()
        except (ValueError, ImportError, AttributeError) as e:
            # Fallback to mock if LLM provider initialization fails
            print(f"Warning: LLM provider initialization failed ({e}), falling back to mock plan")
            return _mock_plan(intent)

    try:
        prompt = _build_planning_prompt(intent, atoms_registry)
        response = llm_provider.call(
            prompt=prompt,
            system_prompt=_get_system_prompt(),
            temperature=0.3,  # Lower temperature for more deterministic plan generation
            max_tokens=2000,  # Adjust based on expected plan size
        )
        plan_doc = _parse_plan_response(response)
        return plan_doc
    except (ValueError, json.JSONDecodeError, AttributeError, KeyError) as e:
        # Fallback to mock plan on parsing/validation errors
        print(f"Warning: LLM planning failed ({e}), falling back to mock plan")
        return _mock_plan(intent)


def _format_atom_for_prompt(atom: dict) -> str:
    """
    Format a single atom definition into a concise string for LLM prompt.
    Extracts only essential information: id, description, inputs, outputs, preconditions.
    """
    atom_id = atom.get("id", "")
    description = atom.get("description", "")
    inputs = atom.get("inputs") or []
    outputs = atom.get("outputs") or []
    preconditions = (atom.get("constraints") or {}).get("preconditions") or []

    parts = [f"ID: {atom_id}"]
    if description:
        parts.append(f"Description: {description}")

    if preconditions:
        precond_str = ", ".join(preconditions)
        parts.append(f"Preconditions: {precond_str}")

    if inputs:
        input_list = []
        for inp in inputs:
            name = inp.get("name", "")
            required = inp.get("required", False)
            desc = inp.get("description", "")
            req_mark = " (required)" if required else " (optional)"
            input_list.append(f"  - {name}{req_mark}: {desc}")
        parts.append("Inputs:")
        parts.extend(input_list)

    if outputs:
        output_list = []
        for out in outputs:
            name = out.get("name", "")
            desc = out.get("description", "")
            output_list.append(f"  - {name}: {desc}")
        parts.append("Outputs:")
        parts.extend(output_list)
    else:
        parts.append("Outputs: (none)")

    return "\n".join(parts)


def _build_planning_prompt(intent: str, atoms_registry: dict) -> str:
    """
    Build the prompt for LLM planning, including user intent and available atoms.
    """
    atoms_list = []
    for _, atom in sorted(atoms_registry.items()):
        atoms_list.append(_format_atom_for_prompt(atom))

    atoms_section = "\n\n".join(atoms_list)

    prompt = f"""You are a planning assistant that creates execution plans from user intents using available atomic services.

User Intent: {intent}

Available Atomic Services:
{atoms_section}

Task: Analyze the user intent and create a structured execution plan that uses one or more of the available atomic services to fulfill the intent.

Requirements:
1. Select the appropriate atomic services (by their ID) to accomplish the user's intent
2. Arrange them in the correct execution order, considering dependencies and preconditions
3. For each step, provide the required inputs (use placeholder values like "user_001" or "/path/to/file" if specific values aren't provided)
4. If a step needs output from a previous step, use the reference format: ${{step_id.outputs.output_name}}
5. Use depends_on to specify step dependencies when a step must run after another
6. Provide a step_id for each step (short, descriptive names like "query_perm", "transfer_file")
7. Set the plan.outputs to describe what the final result will be

Output Format: Return ONLY a valid JSON object matching this structure:
{{
  "target": "Brief summary of the user intent",
  "plan": {{
    "steps": [
      {{
        "step_id": "unique_step_id",
        "id": "atom.service.id",
        "target": "What this step accomplishes",
        "inputs": {{
          "input_name": "value or ${{step_id.outputs.output_name}}"
        }},
        "depends_on": ["step_id_of_prerequisite"]
      }}
    ],
    "outputs": {{
      "result": "Description of final outcome"
    }}
  }}
}}

Important:
- Return ONLY the JSON object, no markdown code blocks, no explanations
- All atom IDs must exist in the available services list above
- All required inputs must be provided
- Use depends_on to ensure correct execution order
- If a step has no dependencies, omit the depends_on field

Now generate the plan:"""

    return prompt


def _get_system_prompt() -> str:
    """System prompt for the LLM."""
    return """You are an expert at analyzing user intents and creating structured execution plans using atomic services. 
You understand service dependencies, preconditions, and data flow between steps. 
You always output valid JSON that strictly follows the required format."""


def _parse_plan_response(response: str) -> dict:
    """
    Parse LLM response (JSON string) into plan dict.
    Handles JSON wrapped in markdown code blocks (```json ... ```).
    """
    response = response.strip()

    # Remove markdown code blocks if present
    if response.startswith("```"):
        lines = response.split("\n")
        # Find the first line that's not ``` or ```json
        start_idx = 0
        for i, line in enumerate(lines):
            if line.strip() and not line.strip().startswith("```"):
                start_idx = i
                break
        # Find the last line that's not ```
        end_idx = len(lines)
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip() and not lines[i].strip().startswith("```"):
                end_idx = i + 1
                break
        response = "\n".join(lines[start_idx:end_idx])

    try:
        plan_doc = json.loads(response)
        return plan_doc
    except json.JSONDecodeError as e:
        raise ValueError(f'Failed to parse LLM response as JSON: {e}. Response: {response[:200]}') from e


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
