# Flowmind Architecture Overview

## Project Overview

Flowmind is an AI-driven platform that transforms **user intent** into **structured business flows**. The system uses an LLM planner to compose atomic services (atoms) into a DSL-based plan, which is validated and prepared for execution.

## Architecture

The codebase follows a modular architecture with clear separation of concerns:

### Core Components
- **Core** (`/core`): Planner LLM, LLM provider abstraction, plan DSL (`plan.dsl.yaml`), plan validator, executor, and atoms loader
- **API** (`/api`): FastAPI routes and Pydantic request/response models; exposes `POST /plan` (with per-step `input_schema`), `POST /execute` (plan + per-step user inputs), and `GET /health`
- **Atoms** (`/atoms`): Atomic service definitions (`*.json`) and Python implementations organized by packages
- **Web** (`/web`): React + TypeScript frontend with three-column layout (Canvas, ChatPanel, Navigation)

For detailed technical information about each module, refer to the specific documentation:
- Core: `core/AGENTS.md`
- API: `api/AGENTS.md`
- Atoms: `atoms/AGENTS.md`
- Web: `web/AGENTS.md`

## Core Workflow

1. **User Intent** → Natural language description of desired business flow
2. **Planner** → LLM generates structured plan based on available atoms
3. **Validator** → Validates plan structure and semantics against predefined rules
4. **Executor** → Resolves atom callables, resolves input references, executes steps in topological order
5. **Result** → Returns structured execution result with per-step outputs

## Current Scope

**Implemented:** User Intent → Planner → Structured Plan → Validator → Executor → Result

**Not yet implemented:** See [Deferred Work](#deferred-work) below.

## Implementation Status Matrix

| Component | Status | Notes |
| --- | --- | --- |
| Planner (`core/planner.py`) | Implemented | Calls LLM provider and falls back to `_mock_plan()` on provider/parse failures |
| Validator (`core/plan_validator.py`) | Implemented | Returns `validation.valid`, `errors`, `warnings`, `execution_order` |
| API (`api/routes.py`) | Implemented | `POST /plan` (enriches steps with `input_schema`), `POST /execute` (plan + `user_inputs`), `GET /health` |
| Atoms Python functions (`atoms/**`) | Implemented as mock behavior | Current implementations are mock/demo functions with print outputs |
| Executor (`core/executor.py`) | Implemented | Consumes validated plan, resolves callables + references, executes steps sequentially; accepts user inputs via `POST /execute` |
| Human approval (plan-time forms) | Implemented | Frontend renders per-step forms from `input_schema`, user fills and submits; execution uses `user_inputs` |
| Human approval (execution-time HITL) | Planned | Pause at step, wait for input, resume not yet implemented |
| `POST /execute` API endpoint | Implemented | Accepts `plan`, optional `validation`, `user_inputs`; merges into steps, validates, runs executor |

## Planner-Validator-Executor Boundary Contract

Even though Executor is not implemented yet, the boundary contract is fixed by current planner and validator behavior:

1. `POST /plan` returns:
   - `plan`: planner output document
   - `validation`: includes `valid` and either `errors` or `execution_order`
2. `execution_order` is a topologically sorted list of effective step identifiers:
   - use explicit `step_id` when provided
   - otherwise fallback to step index as string (`"0"`, `"1"`, ...)
3. Step input values can be:
   - literal values (string/number/object)
   - references in `${step_id.outputs.output_name}` format
4. Executor consumes the validated plan plus `validation.execution_order`, resolves `${step_id.outputs.output_name}` references from previously produced step outputs, and executes steps in that order.
5. Validation failure is a hard stop for execution. The response includes structured errors (`code`, `message`, `path`) for replanning or user-facing feedback.
6. Executor returns `{ success, step_results[], error? }`. Each step result contains `step_id`, `atom_id`, `status` ("completed"/"failed"), `outputs`, and optional `error`.

## Running the Application

### Prerequisites
- Python 3.10+
- Node.js and npm (for frontend)
- uv package manager

### Setup
1. Install dependencies: `uv sync`
2. Set up environment variables in `.env` file
3. Start the server: `uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000`

### API Usage
- `POST /plan` with `{ "intent": "user intent text" }` → `{ "plan": {...} (steps include input_schema), "validation": {...}, "execution": {...}? }`
- `POST /execute` with `{ "plan": {...}, "validation": {...}?, "user_inputs": { "step_id": { "input_name": "value" } } }` → `{ "plan", "validation", "execution" }`
- `GET /health` for health check

## Deferred Work

Items below are recognized as needed but not yet implemented. They are ordered roughly by dependency/priority.

| # | Item | Description | Blocked by |
|---|------|-------------|------------|
| 1 | **`POST /execute` API endpoint** | Expose the executor via a REST endpoint so the frontend (or any client) can trigger execution of a validated plan | **Done** |
| 2 | **Real user inputs from frontend** | Replace plan-literal mock values with actual user-provided data; define the input injection contract between frontend and executor | **Done** (via `user_inputs` in `POST /execute`) |
| 3 | **Human-in-the-loop (HITL)** | Pause execution at steps that require user input (`WAITING` state), resume on frontend event; the "blocking-waking" workflow mechanism from the product spec | Plan-time form collection done; execution-time pause/resume not yet |
| 4 | **Async / parallel execution** | Independent steps (no mutual dependency) can run concurrently instead of sequentially | — |
| 5 | **Step retry / partial re-execution** | Allow re-running a failed step or resuming execution from a specific point | — |
| 6 | **Execution state persistence** | Persist execution context and step results so that execution can survive process restarts | #3 |
| 7 | **Tests for executor** | Unit tests for `_resolve_callable`, `_resolve_inputs`, `_map_outputs`; integration tests for `execute()` | — |
| 8 | **Tests for planner & validator** | Cover all validator error codes, planner mock fallback, LLM response parsing, atoms loader edge cases | — |
| 9 | **Frontend integration** | Wire ChatInterface → `POST /plan` → `POST /execute` → Canvas visualization | **Done** (plan + per-step forms + execute; Canvas visualization still planned) |
