# Flowmind Architecture Overview

## Project Overview

Flowmind is an AI-driven platform that transforms **user intent** into **structured business flows**. The system uses an LLM planner to compose atomic services (atoms) into a DSL-based plan, which is validated and prepared for execution.

## Architecture

The codebase follows a modular architecture with clear separation of concerns:

### Core Components
- **Core** (`/core`): Planner LLM, LLM provider abstraction, plan DSL (`plan.dsl.yaml`), plan validator, and atoms loader
- **API** (`/api`): FastAPI routes and Pydantic request/response models; exposes `POST /plan` and `GET /health`
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
4. **Response** → Returns validated plan with execution order or error details

## Current Scope

**Implemented:** User Intent → Planner → Structured Plan → Validator → Response

**Planned but not implemented:** Human-in-the-loop approval and Executor for running the generated plans.

## Implementation Status Matrix

| Component | Status | Notes |
| --- | --- | --- |
| Planner (`core/planner.py`) | Implemented | Calls LLM provider and falls back to `_mock_plan()` on provider/parse failures |
| Validator (`core/plan_validator.py`) | Implemented | Returns `validation.valid`, `errors`, `warnings`, `execution_order` |
| API (`api/routes.py`) | Implemented | `POST /plan` and `GET /health` are live |
| Atoms Python functions (`atoms/**`) | Implemented as mock behavior | Current implementations are mock/demo functions with print outputs |
| Human approval | Planned | Not implemented yet |
| Executor | Planned | Not implemented yet; only `execution_order` is produced today |

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
4. Executor (future) should consume the validated plan plus `validation.execution_order`, resolve references from previously produced step outputs, and execute steps in that order.
5. Validation failure is a hard stop for execution. The response includes structured errors (`code`, `message`, `path`) for replanning or user-facing feedback.

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
- `POST /plan` with `{ "intent": "user intent text" }` → `{ "plan": {...}, "validation": {...} }`
- `GET /health` for health check
