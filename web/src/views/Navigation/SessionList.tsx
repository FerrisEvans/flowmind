/** Navigation/Session list component */
import React from "react";
import "./SessionList.css";

export const Navigation: React.FC = () => {
  return (
    <div className="navigation">
      <div className="navigation-header">
        <h2>Sessions</h2>
        <button className="new-session-btn">
          + New
        </button>
      </div>
      <div className="session-list"></div>
      <div className="navigation-footer">
        <div className="user-info">User</div>
        <button className="settings-btn">Settings</button>
      </div>
    </div>
  );
};
