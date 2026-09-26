// frontend/src/components/risk/MissedDoseChecker.jsx

import { useState } from "react";
import { checkMissedDose } from "../../api/risk";
import SeverityBadge from "./SeverityBadge";

const ACTION_LABEL = {
  TAKE_NOW: "Take it now",
  TAKE_NOW_DELAY_NEXT: "Take now, next dose delayed",
  SKIP_DOSE: "Skip this dose",
  CONSULT_DOCTOR: "Consult your doctor",
};

// Sensible defaults so the form is fillable instantly for a demo.
function defaultDateTime(hoursFromNow) {
  const d = new Date();
  d.setHours(d.getHours() + hoursFromNow);
  return d.toISOString().slice(0, 16); // matches datetime-local input format
}

export default function MissedDoseChecker() {
  const [drugName, setDrugName] = useState("Metformin");
  const [scheduledTime, setScheduledTime] = useState(defaultDateTime(-7));
  const [currentTime, setCurrentTime] = useState(defaultDateTime(0));
  const [nextScheduledTime, setNextScheduledTime] = useState(defaultDateTime(1));
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await checkMissedDose({
        drugName,
        scheduledTime: new Date(scheduledTime).toISOString(),
        currentTime: new Date(currentTime).toISOString(),
        nextScheduledTime: new Date(nextScheduledTime).toISOString(),
      });
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <form onSubmit={handleSubmit} className="risk-form">
        <label className="risk-label">
          Medication
          <input
            className="risk-input"
            value={drugName}
            onChange={(e) => setDrugName(e.target.value)}
            placeholder="Metformin"
          />
        </label>

        <label className="risk-label">
          Originally scheduled for
          <input
            className="risk-input"
            type="datetime-local"
            value={scheduledTime}
            onChange={(e) => setScheduledTime(e.target.value)}
          />
        </label>

        <label className="risk-label">
          It is now
          <input
            className="risk-input"
            type="datetime-local"
            value={currentTime}
            onChange={(e) => setCurrentTime(e.target.value)}
          />
        </label>

        <label className="risk-label">
          Next dose was scheduled for
          <input
            className="risk-input"
            type="datetime-local"
            value={nextScheduledTime}
            onChange={(e) => setNextScheduledTime(e.target.value)}
          />
        </label>

        <button className="risk-button" type="submit" disabled={loading}>
          {loading ? "Calculating..." : "What should I do?"}
        </button>
      </form>

      {error && <div className="risk-error">{error}</div>}

      {result && (
        <div className="risk-result">
          <div className="risk-card">
            <div className="risk-card-head">
              <span className="risk-card-title">
                {ACTION_LABEL[result.action] || result.action}
              </span>
              <SeverityBadge severity={result.severity} />
            </div>
            <p className="risk-hazard">{result.message}</p>
            <p className="risk-explanation">{result.reasoning}</p>
            {result.adjusted_next_dose_time && (
              <p className="risk-meta">
                Next dose:{" "}
                {new Date(result.adjusted_next_dose_time).toLocaleString()}
              </p>
            )}
            <p className="risk-meta">{result.hours_late}h late</p>
          </div>
        </div>
      )}
    </div>
  );
}
