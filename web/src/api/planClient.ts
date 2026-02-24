import type {
  ExecuteApiResponse,
  PlanApiResponse,
  PlanDoc,
  ValidationResult,
} from "../types/plan";

// Mapping from effective step_id -> { inputName: value }
export interface UserStepInputs {
  [stepId: string]: {
    [inputName: string]: string;
  };
}

export async function postPlan(intent: string): Promise<PlanApiResponse> {
  const resp = await fetch("/api/plan", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ intent }),
  });

  if (!resp.ok) {
    throw new Error(`Failed to create plan: HTTP ${resp.status}`);
  }

  const data = (await resp.json()) as PlanApiResponse;
  return data;
}

export interface ExecutePayload {
  plan: PlanDoc;
  validation?: ValidationResult | null;
  user_inputs: UserStepInputs;
}

export async function postExecute(payload: ExecutePayload): Promise<ExecuteApiResponse> {
  const resp = await fetch("/api/execute", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!resp.ok) {
    throw new Error(`Failed to execute plan: HTTP ${resp.status}`);
  }

  const data = (await resp.json()) as ExecuteApiResponse;
  return data;
}

