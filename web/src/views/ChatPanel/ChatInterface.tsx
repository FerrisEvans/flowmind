/** Chat interface component */
import React, { useState } from "react";
import "./ChatInterface.css";

export const ChatInterface: React.FC = () => {
  const [input, setInput] = useState("");
  return (
    <div className="chat-interface">
      <div className="chat-header">
        <h3>AI Assistant</h3>
      </div>
      <div className="chat-messages">
      </div>
      <form className="chat-input-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="输入您的需求..."
          className="chat-input"
        />
        <button
          type="submit"
          className="chat-send-btn"
        >
          发送
        </button>
      </form>
    </div>
  );
};
