import { create } from "zustand";
import type {
  ExecutionResult,
  PlanDoc,
  PlanInner,
  PlanStep,
  ValidationResult,
} from "../types/plan";

export interface StepInputs {
  [inputName: string]: string;
}

interface PlanState {
  plan: PlanDoc | null;
  validation: ValidationResult | null;
  execution: ExecutionResult | null;
  // Effective step_id -> inputs entered by the user
  stepInputsById: Record<string, StepInputs>;
  isExecuting: boolean;
  error: string | null;

  setPlan: (plan: PlanDoc, validation: ValidationResult) => void;
  updateStepInput: (stepId: string, name: string, value: string) => void;
  clear: () => void;
  setExecution: (execution: ExecutionResult) => void;
  setError: (msg: string | null) => void;
  setIsExecuting: (executing: boolean) => void;
}

function effectiveStepId(step: PlanStep, index: number): string {
  if (typeof step.step_id === "string" && step.step_id.trim()) {
    return step.step_id.trim();
  }
  return String(index);
}

export const usePlanStore = create<PlanState>((set) => ({
  plan: null,
  validation: null,
  execution: null,
  stepInputsById: {},
  isExecuting: false,
  error: null,

  setPlan: (plan, validation) =>
    set(() => ({
      plan,
      validation,
      execution: null,
      // reset inputs when a new plan arrives
      stepInputsById: {},
      error: null,
    })),

  updateStepInput: (stepId, name, value) =>
    set((state) => {
      const prevForStep = state.stepInputsById[stepId] ?? {};
      return {
        stepInputsById: {
          ...state.stepInputsById,
          [stepId]: {
            ...prevForStep,
            [name]: value,
          },
        },
      };
    }),

  clear: () =>
    set(() => ({
      plan: null,
      validation: null,
      execution: null,
      stepInputsById: {},
      isExecuting: false,
      error: null,
    })),

  setExecution: (execution) =>
    set(() => ({
      execution,
      isExecuting: false,
      error: null,
    })),

  setError: (msg) =>
    set(() => ({
      error: msg,
      isExecuting: false,
    })),

  setIsExecuting: (executing) =>
    set(() => ({
      isExecuting: executing,
    })),
}));

// Helper exported for components that need to mirror executor's step id logic
export function getEffectiveStepIds(plan: PlanDoc | null): string[] {
  if (!plan) return [];
  const inner: PlanInner | undefined = plan.plan;
  const steps = inner?.steps ?? [];
  return steps.map((step, idx) => effectiveStepId(step, idx));
}

