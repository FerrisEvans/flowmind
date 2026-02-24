import React, { useState } from "react";
import { usePlanStore } from "../../store/planStore";
import type { AtomInputSchema, PlanStep } from "../../types/plan";
import { postExecute } from "../../api/planClient";
import "./DynamicCanvas.css";

export const DynamicCanvas: React.FC = () => {
  const [activeTool, setActiveTool] = useState('select');
  const {
    plan,
    validation,
    stepInputsById,
    execution,
    isExecuting,
    error,
    updateStepInput,
    setExecution,
    setError,
    setIsExecuting,
  } = usePlanStore();

  const handleExecute = async () => {
    if (!plan) return;
    setIsExecuting(true);
    setError(null);

    try {
      const resp = await postExecute({
        plan,
        validation: validation ?? undefined,
        user_inputs: stepInputsById,
      });
      setExecution(resp.execution);
    } catch (err) {
      const msg =
        err instanceof Error ? err.message : "执行计划时发生未知错误";
      setError(msg);
    }
  };

  const renderStepInputs = (step: PlanStep, index: number) => {
    const schema: AtomInputSchema[] = step.input_schema ?? [];
    if (!schema.length) return null;

    const effectiveStepId =
      typeof step.step_id === "string" && step.step_id.trim()
        ? step.step_id.trim()
        : String(index);

    const currentValues = stepInputsById[effectiveStepId] ?? {};

    return (
      <div className="chat-plan-step" key={effectiveStepId}>
        <div className="chat-plan-step-header">
          <div className="chat-plan-step-title">
            <span className="chat-plan-step-id">
              步骤 {index + 1}（{effectiveStepId}）
            </span>
            <span className="chat-plan-step-atom">{step.id}</span>
          </div>
          <p className="chat-plan-step-target">{step.target}</p>
        </div>

        <div className="chat-plan-step-inputs">
          {schema.map((field) => (
            <label
              key={field.name}
              className="chat-plan-input-group"
            >
              <span className="chat-plan-input-label">
                {field.name}
                {field.required && <span className="chat-plan-input-required">*</span>}
              </span>
              <input
                type="text"
                className="chat-plan-input-control"
                value={currentValues[field.name] ?? ""}
                placeholder={field.description ?? ""}
                onChange={(ev) =>
                  updateStepInput(
                    effectiveStepId,
                    field.name,
                    ev.target.value,
                  )
                }
              />
            </label>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="dynamic-canvas">
      <div className="canvas-toolbar">
        <div className="toolbar-group">
          <button
            className={`toolbar-btn ${activeTool === 'select' ? 'active' : ''}`}
            onClick={() => setActiveTool('select')}
            title="选择工具"
          >
            ✋
          </button>
          <button
            className={`toolbar-btn ${activeTool === 'move' ? 'active' : ''}`}
            onClick={() => setActiveTool('move')}
            title="移动画布"
          >
            🖱️
          </button>
          <button
            className={`toolbar-btn ${activeTool === 'zoom' ? 'active' : ''}`}
            onClick={() => setActiveTool('zoom')}
            title="缩放"
          >
            🔍
          </button>
        </div>

        <div className="toolbar-group">
          <button
            className="toolbar-btn-secondary"
            title="适应视图"
          >
            🏠
          </button>
          <button
            className="toolbar-btn-secondary"
            title="重置缩放"
          >
            🔄
          </button>
        </div>
      </div>

      <div className="canvas-content">
        {!plan ? (
          <div className="canvas-placeholder">
            <p className="canvas-placeholder-text">工作流将在此展示</p>
            <p className="canvas-placeholder-hint">在右侧对话中输入需求并生成计划后，这里会显示各步骤及其参数。</p>

            <div className="canvas-workflow-preview">
              <div className="workflow-node initial">
                <div className="node-icon">📋</div>
                <div className="node-info">
                  <h4>初始任务</h4>
                  <p>定义目标和需求</p>
                </div>
              </div>

              <div className="workflow-arrow">⬇️</div>

              <div className="workflow-node process">
                <div className="node-icon">⚙️</div>
                <div className="node-info">
                  <h4>处理阶段</h4>
                  <p>执行核心逻辑</p>
                </div>
              </div>

              <div className="workflow-arrow">⬇️</div>

              <div className="workflow-node final">
                <div className="node-icon">✅</div>
                <div className="node-info">
                  <h4>完成状态</h4>
                  <p>输出结果</p>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="canvas-plan-panel">
            <div className="chat-panel-plan-header">
              <h4 className="chat-panel-plan-title">计划步骤参数</h4>
              <p className="chat-panel-plan-subtitle">
                根据每个原子服务的定义填写所需参数，然后点击执行。
              </p>
              {error && (
                <p className="chat-panel-plan-error">
                  {error}
                </p>
              )}
            </div>

            <div className="chat-panel-plan-steps">
              {plan.plan.steps.map((step, idx) => renderStepInputs(step, idx))}
            </div>

            <div className="chat-panel-plan-actions">
              <button
                type="button"
                className="chat-panel-execute"
                onClick={handleExecute}
                disabled={isExecuting}
              >
                {isExecuting ? "执行中..." : "执行计划"}
              </button>
            </div>

            {execution && (
              <div className="chat-panel-execution-summary">
                <p>执行结果：{execution.success ? "成功" : "失败"}</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
