/** Three-column layout component */
import React from "react";
import { Navigation } from "../Navigation/SessionList";
import { DynamicCanvas } from "../Canvas/DynamicCanvas";
import { ChatInterface } from "../ChatPanel/ChatInterface";
import "./ThreeColumnLayout.css";

export const ThreeColumnLayout: React.FC = () => {
  return (
    <div className="three-column-layout">
      <aside className="navigation-column">
        <Navigation />
      </aside>
      <main className="canvas-column">
        <DynamicCanvas />
      </main>
      <aside className="chat-column">
        <ChatInterface />
      </aside>
    </div>
  );
};
