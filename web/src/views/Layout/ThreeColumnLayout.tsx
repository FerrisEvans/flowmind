import React from "react";
import { Navigation } from "../Navigation/SessionList";
import { DynamicCanvas } from "../Canvas/DynamicCanvas";
import { ChatInterface } from "../ChatPanel/ChatInterface";
import "./ThreeColumnLayout.css";

export const ThreeColumnLayout: React.FC = () => {
  return (
    <div className="three-column-layout">
      <aside className="layout-nav">
        <Navigation />
      </aside>
      <main className="layout-canvas">
        <DynamicCanvas />
      </main>
      <aside className="layout-chat">
        <ChatInterface />
      </aside>
    </div>
  );
};
