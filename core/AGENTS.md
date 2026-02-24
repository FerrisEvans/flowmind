# Core Module Documentation

## Overview

The Core module contains the fundamental components of the Flowmind platform responsible for generating, validating, and executing structured business flows from user intent. This includes the Planner (LLM integration), Provider (LLM client), Atoms Loader (registry management), Plan Validator (DSL compliance verification), and Executor (step-by-step plan execution).

## Components

### 1. Planner (`core/planner.py`)

The Planner component transforms user intent into structured plans using LLM capabilities.

**Key Functions:**
- `plan(intent, atoms_registry, llm_provider)` - Main entry point for plan generation
- `_build_planning_prompt()` - Constructs LLM prompt with atom definitions
- `_parse_plan_response()` - Parses and validates LLM JSON response
- `_mock_plan()` - Fallback mechanism when LLM is unavailable

**Features:**
- Automatic formatting of atom definitions for prompt context
- Temperature=0.3 for deterministic outputs
- Fallback to mock plan if LLM call fails or response parsing fails
- Structured error handling and recovery

### 2. LLM Provider (`core/provider.py`)

Abstracts LLM interactions to provide a consistent interface across different providers.

**Class:** `LLMProvider`

**Configuration:**
- `OPENAI_API_KEY` - API key for authentication
- `OPENAI_MODEL` - Model identifier (default: gpt-4)
- `OPENAI_BASE_URL` - API endpoint (default: OpenAI API)

**Methods:**
- `call(prompt, system_prompt, ...)` - Returns response text
- `completion(prompt, ...)` - Returns full ChatCompletion object
- Built-in timeout handling

### 3. Atoms Loader (`core/atoms_loader.py`)

Manages the registration and loading of atom definitions from JSON files.

**Function:** `load_atoms_registry(atoms_dir)`

**Process:**
- Discovers `*.json` files in the atoms directory
- Parses each JSON file and extracts atoms from the `atoms` array
- Builds registry mapping `atom_id` to atom definition (skips files that fail to parse)
- Returns registry for use in planning and validation

### 4. Plan Validator (`core/plan_validator.py`)

Validates generated plans against structural and semantic rules implemented in `core/plan_validator.py` and guided by `core/plan.dsl.yaml`.

**Function:** `validate_plan(plan_doc, atoms_registry)`

**Inputs:**
- `plan_doc`: Parsed plan document from LLM, with structure:
  - `target`: string (summary of user intent)
  - `plan`: object containing:
    - `steps`: array of step objects
    - `outputs`: optional object for final results
  - Each step contains: `id` (atom id), `target`, `inputs`; optional: `step_id`, `depends_on`
- `atoms_registry`: Registry mapping atom IDs to their definitions, used to validate step IDs and inputs

**Validation Categories and Rules (current implementation):**

1. **Schema (S1-S7):** Structural and type validation
   - S1: Root object must contain `target` (string)
   - S2: Root object must contain `plan` (object)
   - S3: `plan.steps` must exist and be a non-empty array
   - S4: Each step must be an object with `id` (string), `target` (string), `inputs` (object)
   - S5: If step has `step_id`, it must be a non-empty string
   - S6: If step has `depends_on`, it must be a string array
   - S7: If `plan.outputs` exists, it must be an object

2. **Uniqueness (U1):** step_id uniqueness
   - U1: All explicit `step_id` values must be unique

3. **Atom References (A1-A3):** Registry validation and input requirements
   - A1: Each `step.id` must exist in `atoms_registry`
   - A2: Each step's `inputs` keys must be declared in the corresponding atom's `inputs`
   - A3: Required inputs (marked as `required: true` in atom definition) must be present in the step's `inputs`

4. **References (R1-R3):** Input reference resolution and dependency validation
   - R1: References (e.g., `${step_id.outputs.output_name}`) must point to existing step IDs in the plan
   - R2: Referenced output names must exist in the referenced step's atom definition
   - R3: Referenced steps must come before the current step in execution order (dependency order)

5. **Dependencies (D1-D2):** Dependency graph validation and cycle detection
   - D1: Elements in `depends_on` arrays must be valid step identifiers in the plan
   - D2: The dependency graph must be acyclic (no circular dependencies)

**Important implementation notes:**
- `depends_on` is validated as an array, but element-level type checking is currently lenient (non-string elements are skipped during dependency graph construction).
- Input reference ordering is currently enforced by graph topology and cycle checks; there is no dedicated `REF_BEFORE_DEPENDENCY` error code emitted in the current validator implementation.

**Step Identifier Convention:**
- If a step has an explicit `step_id`, that value is used
- If no `step_id` is provided, the array index (as string) is used (e.g., "0", "1")
- Dependencies and references use these effective identifiers

**Reference Format:**
- Standard format: `${step_id.outputs.output_name}`
- Parser extracts `step_id` and `output_name` to validate references

**Output:**
- Success: `{valid: true, warnings: [...], execution_order: [...]}` - Topologically sorted step IDs for execution
- Failure: `{valid: false, errors: [{code, message, path}...]}` - Array of validation errors with location paths

**Error Codes:**
- `MISSING_FIELD`: Required field missing
- `INVALID_TYPE`: Value type doesn't match expected type
- `EMPTY_STEPS`: plan.steps array is empty
- `EMPTY_STEP_ID`: step_id is an empty string
- `DUPLICATE_STEP_ID`: Duplicate step_id found
- `UNKNOWN_ATOM_ID`: Step ID doesn't exist in atoms registry
- `UNKNOWN_INPUT_FIELD`: Input field not defined in atom
- `MISSING_REQUIRED_INPUT`: Required input field is missing
- `UNKNOWN_STEP_REF`: Reference points to non-existent step
- `UNKNOWN_OUTPUT_FIELD`: Reference points to non-existent output
- `UNKNOWN_DEPENDENCY`: depends_on refers to non-existent step
- `CIRCULAR_DEPENDENCY`: Circular dependency detected

Planned/optional future error code:
- `REF_BEFORE_DEPENDENCY`: A stricter explicit reference-order violation code (not currently emitted by `core/plan_validator.py`)

### 5. Executor (`core/executor.py`)

Consumes a validated plan response and executes atom functions in topological order.

**Function:** `execute(plan_response, atoms_registry)`

**Inputs:**
- `plan_response`: Full response dict (same shape as `POST /plan` output) with `plan` and `validation` keys
- `atoms_registry`: Registry mapping atom IDs to their definitions

**Precondition:** `plan_response["validation"]["valid"]` must be `True`; otherwise execution is refused immediately.

**Execution Loop (for each step in `validation.execution_order`):**
1. Look up step definition from `plan.steps` by effective step_id
2. Resolve the atom Python callable via `_resolve_callable(atom_id)`
3. Resolve input values via `_resolve_inputs(inputs, context)` — replace `${step_id.outputs.output_name}` references with concrete values from previous step outputs; literal values pass through
4. Call the atom function with resolved inputs as keyword arguments
5. Map the return value to named outputs via `_map_outputs(return_value, atom_def)`
6. Store outputs in the execution context keyed by step_id

**Callable Resolution (`_resolve_callable`):**
- Atom ID convention: `package.domain.action`
- Module path: `atoms.{package}.{domain}` (imported via `importlib`)
- Function: `getattr(module, action)`
- Raises `ExecutorError("UNRESOLVED_ATOM", ...)` if module or function cannot be found

**Output Mapping (`_map_outputs`):**
- No outputs declared → `{}`
- One output declared → `{ output_name: return_value }`
- Multiple outputs declared → expects dict return, maps by output names

**Return:**
```python
{
    "success": True,  # or False
    "step_results": [
        {
            "step_id": "query_perm",
            "atom_id": "globalx.permission.query_permissions",
            "status": "completed",  # or "failed"
            "outputs": {"has_permission": True},
            "error": None  # or "[ERROR_CODE] message"
        }
    ],
    "error": None  # top-level error message if execution aborted
}
```

**Error Codes:**
- `STEP_NOT_FOUND`: step_id from execution_order not found in plan.steps
- `UNRESOLVED_ATOM`: Cannot resolve atom ID to a Python callable
- `UNRESOLVED_REF`: Input reference points to missing step or output in execution context
- `STEP_EXECUTION_ERROR`: Atom function raised an exception at runtime

**Current Limitations:**
- Execution is synchronous and sequential (no parallel step execution)
- User-facing inputs use plan literal values as mocks
- No human-in-the-loop pausing; all steps run to completion or first failure
- Execution aborts on first step failure (no retry or skip)

## Data Flow

1. **Input:** User intent and atoms registry
2. **Processing:** Planner generates structured plan using LLM
3. **Validation:** Plan validator checks compliance with rules
4. **Execution:** Executor resolves callables, resolves references, runs steps in order
5. **Output:** Execution result with per-step status and outputs

## Error Handling

- LLM unavailability triggers mock plan fallback
- Invalid plan structures return detailed error codes
- Dependency cycles are detected and reported
- Missing required inputs are identified with specific error paths

## Loader Behavior (Current)

- `load_atoms_registry()` scans `atoms/*.json` each load call.
- JSON parse failures are skipped file-by-file.
- Atom registration is best-effort and keyed by `atom.id`.
- Registry caching is currently implemented at the API layer (`api/routes.py`), not inside the loader itself.

## Integration Points

- **API Layer:** Receives user intent, returns validated plans
- **Atoms Registry:** Used by validator for schema checks and by executor for output mapping
- **Atoms Python Implementations:** Executor dynamically imports and calls atom functions
- **Plan DSL:** Validates against schema defined in `plan.dsl.yaml`
