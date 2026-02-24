import React, { useState, useRef, useEffect } from "react";
import { useChatStore } from "../../store/chatStore";
import { usePlanStore } from "../../store/planStore";
import type { Message } from "../../types/chat";
import { postPlan } from "../../api/planClient";
import "./ChatInterface.css";

function formatTime(ts: number): string {
  return new Date(ts).toLocaleTimeString("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

export const ChatInterface: React.FC = () => {
  const [input, setInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const {
    activeSessionId,
    getMessages,
    addMessage,
  } = useChatStore();

  const messages: Message[] = activeSessionId
    ? getMessages(activeSessionId)
    : [];

  const {
    setPlan,
    setError,
  } = usePlanStore();

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length]);

  // Auto-resize textarea based on content
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [input]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || !activeSessionId) return;

    addMessage(activeSessionId, "user", text);
    setInput("");

    try {
      const resp = await postPlan(text);
      setPlan(resp.plan, resp.validation);
      // 可选：在对话区追加一条系统消息提醒用户填写参数
      addMessage(
        activeSessionId,
        "assistant",
        `已生成计划，共 ${resp.plan.plan.steps.length} 个步骤，请在下方为每个步骤填写参数后执行。`,
      );
    } catch (err) {
      const msg =
        err instanceof Error ? err.message : "生成计划时发生未知错误";
      setError(msg);
      addMessage(activeSessionId, "assistant", `生成计划失败：${msg}`);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as unknown as React.FormEvent);
    }
  };

  if (!activeSessionId) {
    return (
      <div className="chat-panel">
        <header className="chat-panel-header">
          <h3 className="chat-panel-title">对话</h3>
        </header>
        <div className="chat-panel-empty-state">
          <p>请选择或新建一个对话</p>
        </div>
      </div>
    );
  }

  return (
    <div className="chat-panel">
      <header className="chat-panel-header">
        <h3 className="chat-panel-title">对话</h3>
      </header>

      <div className="chat-panel-messages">
        {messages.length === 0 ? (
          <p className="chat-panel-placeholder">在此输入你的需求，发送后消息会显示在这里（当前仅前端演示，未连接后端）</p>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`chat-panel-msg chat-panel-msg--${msg.role}`}
            >
              <span className="chat-panel-msg-content">{msg.content}</span>
              <span className="chat-panel-msg-time">{formatTime(msg.timestamp)}</span>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      <form className="chat-panel-form" onSubmit={handleSubmit}>
        <textarea
          ref={textareaRef}
          className="chat-panel-input"
          placeholder="输入需求，按 Enter 发送，Shift+Enter 换行..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
          aria-label="输入消息"
        />
        <button type="submit" className="chat-panel-send" disabled={!input.trim()}>
          发送
        </button>
      </form>
    </div>
  );
};
