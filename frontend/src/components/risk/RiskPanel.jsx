// frontend/src/components/risk/RiskPanel.jsx
//
// Drop this into any page: <RiskPanel />
// Combines both Person 3 features behind a simple tab switch:
//   - Interaction & Allergy Checker (Feature 4)
//   - Missed-Dose Decision / Anti-Stacking (Feature 7)

import { useState } from "react";
import "./RiskPanel.css";
import InteractionChecker from "./InteractionChecker";
import MissedDoseChecker from "./MissedDoseChecker";

export default function RiskPanel() {
  const [tab, setTab] = useState("interactions");

  return (
    <div className="risk-panel">
      <header className="risk-header">
        <h2 className="risk-title">Medication Risk Check</h2>
        <p className="risk-subtitle">
          Check for dangerous combinations, or find out what to do about a
          dose you took late.
        </p>
      </header>

      <div className="risk-tabs">
        <button
          className={`risk-tab ${tab === "interactions" ? "risk-tab-active" : ""}`}
          onClick={() => setTab("interactions")}
        >
          Interaction Checker
        </button>
        <button
          className={`risk-tab ${tab === "missed-dose" ? "risk-tab-active" : ""}`}
          onClick={() => setTab("missed-dose")}
        >
          Missed a Dose?
        </button>
      </div>

      <div className="risk-panel-body">
        {tab === "interactions" ? <InteractionChecker /> : <MissedDoseChecker />}
      </div>
    </div>
  );
}
