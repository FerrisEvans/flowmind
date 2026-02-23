# Flowmind: AI-Driven Dynamic Business Flow Generation Platform

## 1. Project Overview

Flowmind is a system that dynamically orchestrates **business logic flows** based on **user semantic intent** and generates corresponding **interactive UIs** in real-time. The system contains a series of "skill packages" divided by business dimension, each containing atomic services. Each atomic service is not a predetermined business, but rather APIs similar to CRUD operations, upload, download, etc. Atomic services can be freely combined to form business processes.

For example, in the real-life "food delivery" scenario, existing software services follow the process: user selects restaurant → chooses dishes → enters address → payment → delivery. With our system, we might have atomic services like "nearby restaurant recommendation", "dish taste filtering", "address verification", "payment method selection", etc. AI can dynamically assemble these atomic services based on user needs to form business flows. We don't define the business processes in any way for the AI, but rather let the AI learn user needs by itself and generate business processes automatically.

---

## 2. Execution Flow

```
User Intent (obtained from front-end Chat Window - temporarily implemented via Postman API calls for testing)
   ↓
Planner LLM (initialize inference model)
   ↓
Structured Plan (call model to generate structure plan compliant with DSL protocol)
   ↓
Plan Validation (structural and semantic validation of the plan against atom registry and DSL rules)
   ↓
Human Approval (use Human in the Loop to convert structured data into user-understandable semantic input for confirmation. Currently only user confirmation is supported, user cannot modify the plan themselves)
   ↓
Executor (parse generated plan, find corresponding atomic services and execute them in sequence. During execution, user input may be required, requiring the front-end to generate forms for user completion.)
   ↓
Execution Feedback (execution process feedback)
   ↓
Planner LLM (if errors occur or abnormal returns occur during execution, replan is required. If completed successfully, notify the user.)
```

## 3. Technical Solution

- **Atomic service capability definition**: `project folder/atoms/*.json`. Defines atomic service capabilities and business boundaries.
- **LLM understanding**: Let the inference model understand atomic services, analyze user intent and decide which services to call to fulfill user intent.
- **Orchestration**: The inference model orchestrates these atomic services and outputs an Intermediate Representation (IR) compliant with the custom protocol. (DSL file: `project folder/core/plan.dsl.yaml`)
- **Plan validation**: Structural and semantic validation of generated plans before proceeding to Human Approval / Executor. Input/output and validation logic are implemented in `core/plan_validator.py` and guided by `core/plan.dsl.yaml`.

Currently implemented up to the Plan Validation step in the execution flow (User Intent → Planner → Structured Plan → Validator → Response); subsequent steps (Human Approval, Executor, etc.) are not implemented yet.

## 4. Notes

1. When generating plans, establish the convention that "all step outputs automatically enter a shared context, subsequent steps can reference by name".
2. Providing all atomic service definitions to the model may lead to token explosion and context explosion issues.
   - 2.1 Categorize by package/category and provide only "potentially relevant" atom subsets to the Planner; or
   - 2.2 Use a two-layer approach: first select "which skill packages / categories" to use, then select specific atoms from those categories for orchestration.

## 5. Running Instructions

The main business flow has been connected with Python: **User Intent → Planner → Structured Plan → Validator → Return plan + validation result**.

### Prerequisites
- Python 3.10+
- Node.js and npm (for frontend)
- uv package manager

### Setup
1. Install dependencies with `uv`:
   ```bash
   pip install uv  # if you don't have it already
   uv sync
   ```
2. Copy `.env.example` to `.env` and set required environment variables:
   ```
   OPENAI_API_KEY=your_openai_api_key
   OPENAI_MODEL=gpt-4
   OPENAI_BASE_URL=https://api.openai.com/v1
   ```
3. Start the server:
   ```bash
   uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

   Or alternatively:
   ```bash
   uv run python main.py
   ```

### API Usage
- **Health Check**: `GET /health` - Check if the service is running
- **Plan Generation**: `POST /plan` with request body `{ "intent": "user intent text" }`, returns `{ "plan": {...}, "validation": { "valid", "errors" | "execution_order", "warnings" } }`

When validation passes, `validation.execution_order` contains a step list sorted by dependencies, for subsequent Executor to execute in order.

### Programmatic Usage
You can also call the flow directly from Python:
```python
from main import run_main_flow
result = run_main_flow("user intent")
# Returns: { "plan": plan_doc, "validation": { "valid", "errors"|"execution_order", "warnings" } }
```

### For More Details
- Core architecture: See `AGENTS.md`
- Module-specific documentation:
  - `core/AGENTS.md` - Planner, provider, validator details
  - `api/AGENTS.md` - API endpoints and models
  - `atoms/AGENTS.md` - Atom definitions and implementations
  - `web/AGENTS.md` - Frontend architecture
- Validation rules and implementation: See `core/plan_validator.py`
- Plan DSL: See `core/plan.dsl.yaml`
