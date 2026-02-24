# API Module Documentation

## Overview

The API module provides REST endpoints for the Flowmind platform using FastAPI. It serves as the interface between clients and the core business logic, handling user requests and returning structured responses.

## Endpoints

### POST `/plan`

Generates a structured business flow plan from user intent.

**Request Body:**
```json
{
  "intent": "string (user's intent or desired outcome)"
}
```

**Response:**
```json
{
  "plan": {
    "target": "string (summary of user intent)",
    "plan": {
      "steps": [
        {
          "step_id": "string (optional unique identifier)",
          "id": "string (atom service identifier)",
          "target": "string (purpose of this step)",
          "inputs": "object (input parameters)",
          "depends_on": "string[] (optional dependencies)",
          "input_schema": [
            {
              "name": "string",
              "type": "string",
              "required": "boolean (optional)",
              "description": "string (optional)"
            }
          ]
        }
      ],
      "outputs": "object (optional final outputs)"
    }
  },
  "validation": {
    "valid": "boolean (whether the plan is valid)",
    "errors": [
      {
        "code": "string (error code)",
        "message": "string (human-readable error description)",
        "path": "string (location of error in plan structure)"
      }
    ],
    "warnings": [
      {
        "code": "string (warning code)",
        "message": "string (human-readable warning description)",
        "path": "string (location of warning in plan structure)"
      }
    ],
    "execution_order": "string[] (topologically sorted step identifiers for execution)"
  }
}
```

**Success Response:**
- Status: `200 OK`
- Body: Validated plan with execution order

**Error Response:**
- Status: `200 OK` when request schema is valid but plan validation fails
- Body: `validation.valid = false` with detailed validation errors

**Request Schema Error Response (FastAPI/Pydantic):**
- Status: `422 Unprocessable Entity`
- Trigger: Invalid request body shape/type (e.g. missing or non-string `intent`)

**Enriched response for frontend forms:** Each step in `plan.plan.steps` is augmented with `input_schema`, taken from the atoms registry for that step’s `id` (atom id). The frontend uses `input_schema` to render per-step input fields (e.g. string → text input) without a separate atoms request. See `api/routes.py` (enrichment loop before `validate_plan`).

### POST `/execute`

Executes a plan with per-step user-provided inputs. The client sends the plan document and a mapping from effective step id to input values; the server merges these into each step’s `inputs`, re-validates, and runs the executor.

**Request Body:**
```json
{
  "plan": { "target": "...", "plan": { "steps": [...], "outputs": {...} } },
  "validation": { "valid": true, "execution_order": ["step_id_1", ...] } (optional),
  "user_inputs": {
    "step_id_1": { "input_name": "value", ... },
    "step_id_2": { "input_name": "value", ... }
  }
}
```

- `plan`: Full plan document (same shape as `POST /plan` response).
- `validation`: Optional; if omitted, the server validates after merging user inputs.
- `user_inputs`: Map from effective step identifier (explicit `step_id` or index as string) to object of input name → value. These override or fill placeholders in each step’s `inputs`.

**Response:**
```json
{
  "plan": { ... },
  "validation": { "valid": true, "execution_order": [...], ... },
  "execution": {
    "success": true | false,
    "step_results": [
      {
        "step_id": "string",
        "atom_id": "string",
        "status": "completed" | "failed",
        "outputs": { ... },
        "error": null | "string"
      }
    ],
    "error": null | "string (top-level error if execution aborted)"
  }
}
```

- Status: `200 OK`; body always includes `plan`, `validation`, and `execution`. If validation fails after applying user inputs, `execution.success` is false and `execution.error` describes the failure.

### GET `/health`

Provides health check for the service.

**Response:**
```json
{
  "status": "ok"
}
```

**Success Response:**
- Status: `200 OK`
- Body: Health status information

## Request/Response Models

Defined in `api/models.py` using Pydantic:

- `PlanRequest`: Contains user intent
- `PlanResponse`: `plan`, `validation`, `execution` (optional)
- `ExecuteRequest`: `plan`, `validation` (optional), `user_inputs` (map step_id → input name → value)
- `ExecuteResponse`: `plan`, `validation`, `execution` (required)

`GET /health` returns a plain dict from route code and does not use a dedicated Pydantic response model.

## Architecture

- **FastAPI Framework:** Provides automatic API documentation (Swagger UI) and request validation
- **Pydantic Models:** Ensures type safety and automatic request/response validation
- **Direct Module Integration:** Imports and calls core components (planner, validator, atoms loader) directly; atoms registry is lazily loaded and cached via a module-level global
- **Error Handling:** Structured error responses with appropriate HTTP status codes

## Integration Points

- **Core Module:** Interfaces with planner and validator
- **Atoms Registry:** Utilizes loaded atom definitions for plan validation
- **Environment:** Uses configured LLM provider settings

## Runtime Notes

- Atoms registry is loaded lazily and cached in-process (`_atoms_registry`) to avoid repeated disk scanning for each `/plan` request.
