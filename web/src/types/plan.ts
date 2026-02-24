export interface AtomInputSchema {
  name: string;
  type: string;
  required?: boolean;
  description?: string;
  // properties is present in JSON but not needed for simple text inputs
  properties?: unknown;
}

export interface PlanStep {
  step_id?: string;
  id: string;
  target: string;
  inputs: Record<string, unknown>;
  depends_on?: string[];
  // Added by backend: schema derived from atom definition inputs
  input_schema?: AtomInputSchema[];
}

export interface PlanInner {
  steps: PlanStep[];
  outputs?: Record<string, unknown>;
}

export interface PlanDoc {
  target: string;
  plan: PlanInner;
}

export interface ValidationError {
  code: string;
  message: string;
  path: string;
}

export interface ValidationResult {
  valid: boolean;
  errors?: ValidationError[];
  warnings?: ValidationError[];
  execution_order?: string[];
}

export interface StepExecutionResult {
  step_id: string;
  atom_id: string;
  status: "completed" | "failed";
  outputs: Record<string, unknown>;
  error: string | null;
}

export interface ExecutionResult {
  success: boolean;
  step_results: StepExecutionResult[];
  error?: string | null;
}

export interface PlanApiResponse {
  plan: PlanDoc;
  validation: ValidationResult;
  execution: ExecutionResult | null;
}

export interface ExecuteApiResponse {
  plan: PlanDoc;
  validation: ValidationResult;
  execution: ExecutionResult;
}

