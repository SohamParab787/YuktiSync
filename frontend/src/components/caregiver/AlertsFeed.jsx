import React, { useState, useEffect } from "react";
import { getAlerts } from "../../api/caregiver";

export default function AlertsFeed({ patientId, refreshTrigger }) {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchAlerts = async () => {
    if (!patientId) return;
    try {
      setLoading(true);
      setError(null);
      const data = await getAlerts(patientId);
      setAlerts(data || []);
    } catch (err) {
      console.error("Failed to load alerts feed:", err);
      setError(err.message || "Failed to load missed-dose alerts");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, [patientId, refreshTrigger]);

  const getSeverityBadgeClass = (severity) => {
    switch (severity?.toLowerCase()) {
      case "critical":
        return "badge-critical";
      case "high":
        return "badge-high";
      case "medium":
        return "badge-medium";
      default:
        return "badge-low";
    }
  };

  return (
    <div className="alerts-feed-card">
      <div className="card-header-row">
        <div className="header-title-group">
          <span className="icon-badge alert-icon">🔔</span>
          <h3 className="section-title">Missed Dose Alerts & Escalations</h3>
        </div>
        <button 
          onClick={fetchAlerts} 
          className="btn-text-sm"
          title="Refresh alerts"
        >
          ↻ Refresh
        </button>
      </div>

      {loading && (
        <div className="loading-state">
          <div className="spinner"></div>
          <span>Checking escalation feed...</span>
        </div>
      )}

      {error && (
        <div className="error-banner">
          <span>⚠️ {error}</span>
          <button onClick={fetchAlerts} className="btn-retry">Retry</button>
        </div>
      )}

      {!loading && !error && alerts.length === 0 && (
        <div className="empty-state">
          <span className="empty-icon">✅</span>
          <p>No active alerts. All scheduled medications are adhering to schedule.</p>
        </div>
      )}

      {!loading && !error && alerts.length > 0 && (
        <div className="alerts-list">
          {alerts.map((alert) => (
            <div 
              key={alert.id} 
              className={`alert-item-box ${alert.severity === "high" || alert.severity === "critical" ? "alert-item-urgent" : ""}`}
            >
              <div className="alert-top-row">
                <div className="alert-meta">
                  <span className={`severity-badge ${getSeverityBadgeClass(alert.severity)}`}>
                    {alert.severity?.toUpperCase()}
                  </span>
                  <span className="alert-med-name">{alert.medication_name}</span>
                </div>
                <span className="alert-time">
                  {alert.created_at ? new Date(alert.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "Recently"}
                </span>
              </div>
              <p className="alert-message">{alert.message}</p>
              <div className="alert-footer">
                <span className="alert-type-tag">Type: {alert.alert_type?.replace("_", " ")}</span>
                <span className="alert-status-badge">
                  {alert.is_resolved ? "Resolved" : "Active Escalation"}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
