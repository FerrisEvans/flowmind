import React from "react";
import { useChatStore } from "../../store/chatStore";
import "./SessionList.css";

function formatSessionDate(ts: number): string {
  const d = new Date(ts);
  const today = new Date();
  if (d.toDateString() === today.toDateString()) {
    return d.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
  }
  return d.toLocaleDateString("zh-CN", { month: "short", day: "numeric" });
}

export const Navigation: React.FC = () => {
  const { sessions, activeSessionId, addSession, setActiveSession } = useChatStore();

  return (
    <div className="session-list-nav">
      <header className="session-list-header">
        <h2 className="session-list-title">对话</h2>
        <button type="button" className="session-list-new" onClick={addSession}>
          + 新建
        </button>
      </header>

      <div className="session-list-scroll">
        {sessions.length === 0 ? (
          <p className="session-list-empty">暂无对话，点击「+ 新建」开始</p>
        ) : (
          <ul className="session-list-items">
            {sessions.map((s) => (
              <li key={s.id}>
                <button
                  type="button"
                  className={`session-list-item ${activeSessionId === s.id ? "active" : ""}`}
                  onClick={() => setActiveSession(s.id)}
                >
                  <span className="session-list-item-title">{s.title}</span>
                  <span className="session-list-item-date">{formatSessionDate(s.createdAt)}</span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <footer className="session-list-footer">
        <button type="button" className="session-list-settings">
          设置
        </button>
      </footer>
    </div>
  );
};
