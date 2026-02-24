# Web Module Documentation

## Overview

The Web module provides the frontend interface for the Flowmind platform using React and TypeScript. It implements a three-column layout with **plan-driven forms**: the user sends intent, receives a plan with per-step input schemas, fills in parameters for each atomic service, then triggers execution.

## Architecture

### Technology Stack

- **React 18**: Component-based UI framework
- **TypeScript**: Type-safe JavaScript development
- **Vite**: Fast build tool and development server
- **Zustand**: State management for chat sessions (`chatStore`) and plan/execution state (`planStore`)
- **fetch**: Used for API calls (`api/planClient.ts`); Axios remains an optional dependency

### Layout Structure

The application implements a three-column layout (`views/Layout/ThreeColumnLayout.tsx`):

#### 1. Navigation Column (`views/Navigation/SessionList.tsx`)
- Renders a sidebar with "Sessions" header, "+ New" button, and "Settings" button
- **Planned:** Conversation history, session switching, saved workflows

#### 2. Chat Panel Column (`views/ChatPanel/ChatInterface.tsx`)
- Text input and send button; on submit, calls `POST /api/plan` with intent
- Displays conversation messages and informs the user when a plan has been generated
- **Implemented:** Intent entry, sending to backend, basic conversation log

#### 3. Canvas Column (`views/Canvas/DynamicCanvas.tsx`)
- Toolbar plus central canvas area
- When no plan is present, shows a placeholder \"workflow will appear here\"
- When a plan is present, renders **one parameter form per step** using each step’s `input_schema` (e.g. `globalx.transfer.file_transfer` → three string inputs)
- \"执行计划\" button submits plan + user-filled `step_inputs` to `POST /api/execute`, and shows execution summary

## Components

### Core Views

#### ThreeColumnLayout (`views/Layout/ThreeColumnLayout.tsx`)
- Composes Navigation, Canvas, and ChatPanel

#### ChatInterface (`views/ChatPanel/ChatInterface.tsx`)
- Controlled input; send → `postPlan(intent)`; stores plan/validation in `planStore`
- Shows user and assistant messages (including \"plan generated\" / error hints)

#### DynamicCanvas (`views/Canvas/DynamicCanvas.tsx`)
- Reads `plan`, `validation`, `execution`, `stepInputsById`, `error`, `isExecuting` from `planStore`
- For each step in `plan.plan.steps`, renders a form block using `step.input_schema` (name, type, required, description); inputs are keyed by effective `step_id` (explicit `step_id` or index)
- Execute button calls `postExecute({ plan, validation, user_inputs: stepInputsById })` and shows execution result
- **Note:** Cross-step duplicate field names are not deduplicated; each step has its own inputs (see Todolist)

#### SessionList (`views/Navigation/SessionList.tsx`)
- Static UI shell; session list and switching logic planned

## State Management

### chatStore (`store/chatStore.ts`)
- Sessions list, active session id, messages per session
- `addMessage`, `getMessages`, `addSession`, `setActiveSession`

### planStore (`store/planStore.ts`)
- `plan`, `validation`, `execution` (from API)
- `stepInputsById`: `Record<stepId, Record<inputName, string>>` for user-filled values
- `setPlan(plan, validation)`, `updateStepInput(stepId, name, value)`, `setExecution`, `setError`, `setIsExecuting`, `clear`
- Helper `getEffectiveStepIds(plan)` for step id resolution (mirrors backend)

### Data Flow (Current)

1. **Intent:** User types intent and sends → `POST /api/plan` → response includes `plan` with each step enriched by `input_schema` (from atoms registry).
2. **Plan display:** Frontend stores plan/validation in planStore; the **Canvas column** (`DynamicCanvas`) shows one form per step (inputs from `input_schema`; string → text input).
3. **User fills** each step’s fields in the middle canvas; state in `stepInputsById`.
4. **Execute:** User clicks \"执行计划\" in the canvas → `POST /api/execute` with `plan`, `validation`, `user_inputs: stepInputsById` → backend merges user inputs into step `inputs`, validates, runs executor → frontend shows success/failure and execution summary in the canvas.

## Integration Points

### API Client (`api/planClient.ts`)

- **`postPlan(intent)`** → `POST /api/plan` → returns `PlanApiResponse` (plan with `input_schema` per step, validation, optional execution from backend).
- **`postExecute({ plan, validation, user_inputs })`** → `POST /api/execute` → returns `ExecuteApiResponse` (plan, validation, execution).

### Types (`types/plan.ts`)

- `PlanDoc`, `PlanStep` (with optional `input_schema`), `AtomInputSchema`, `ValidationResult`, `ExecutionResult`, `PlanApiResponse`, `ExecuteApiResponse`.

### Proxy and Endpoints

- **POST `/api/plan`**: Send intent; receive plan (with per-step `input_schema`), validation, and optional execution.
- **POST `/api/execute`**: Send plan, optional validation, and `user_inputs` (per step_id); receive plan, validation, execution.
- **GET `/api/health`**: Health check (proxied to backend).
- Vite proxy: `/api` → `http://localhost:8000` (path prefix `/api` stripped).

### Running the Frontend

- **Install:** `npm install` (from `web/`)
- **Dev:** `npm run dev` — serves at `http://localhost:3000`
- **Build:** `npm run build` — output in `web/dist/`
- **Preview:** `npm run preview` — serve production build locally
- Ensure backend is running on port 8000 for API calls (e.g. `uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000` from repo root).

## Todolist

- **Cross-step duplicate field values:** Multiple steps may declare the same input name (e.g. `user_id`). Currently each step has its own input fields; no sharing or deduplication. Future: decide whether same-named fields share one value or stay per-step and implement accordingly.

## Development Guidelines

### Component Standards
- Use TypeScript interfaces for all props and state
- Implement proper error boundaries
- Follow React best practices for performance
- Maintain consistent styling approach

### State Management
- Use Zustand for global application state
- Component-specific state for UI controls
- Proper cleanup of subscriptions and listeners

### UI/UX Principles
- Intuitive visualization of complex workflow dependencies
- Clear indication of validation errors or plan issues
- Smooth animations for interactions
- Accessibility compliance
