import React, { useState, useEffect } from "react";
import { getDashboard, createNote, uploadPrescription } from "../../api/caregiver";
import AlertsFeed from "./AlertsFeed";

export default function Dashboard({
  patientId = "patient-101",
  onOpenChat,
  onOpenInvite,
}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Shared Notes Form State
  const [newNoteText, setNewNoteText] = useState("");
  const [submittingNote, setSubmittingNote] = useState(false);
  const [noteError, setNoteError] = useState(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // Prescription Modal State
  const [showRxModal, setShowRxModal] = useState(false);
  const [rxDoctor, setRxDoctor] = useState("Dr. Anita Sengupta, MD");
  const [rxClinic, setRxClinic] = useState("Max Healthcare Multispeciality Clinic");
  const [rxDiagnosis, setRxDiagnosis] = useState("Type 2 Diabetes Mellitus & Essential Hypertension");
  const [rxMedsInput, setRxMedsInput] = useState(
    "Metformin XR | 500mg | Twice daily after meals | 08:00 AM, 08:00 PM | Take with meals\nLisinopril | 10mg | Once daily morning | 09:00 AM | Take with water in morning\nAtorvastatin | 20mg | Once daily bedtime | 10:00 PM | Take at night before sleep"
  );
  const [rxSubmitting, setRxSubmitting] = useState(false);
  const [rxError, setRxError] = useState(null);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await getDashboard(patientId);
      setData(res);
    } catch (err) {
      console.error("Dashboard error:", err);
      setError(err.message || "Failed to load caregiver dashboard");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, [patientId, refreshTrigger]);

  const handleAddNote = async (e) => {
    e.preventDefault();
    if (!newNoteText.trim()) return;

    try {
      setSubmittingNote(true);
      setNoteError(null);
      await createNote({
        patient_id: patientId,
        content: newNoteText.trim(),
      });
      setNewNoteText("");
      setRefreshTrigger((prev) => prev + 1);
    } catch (err) {
      setNoteError(err.message || "Failed to add note");
    } finally {
      setSubmittingNote(false);
    }
  };

  // Prescription Parser & Uploader
  const handleUploadPrescription = async (e) => {
    e?.preventDefault();
    try {
      setRxSubmitting(true);
      setRxError(null);

      // Parse line-by-line: Name | Dosage | Frequency | Timing Slots | Instructions
      const lines = rxMedsInput.split("\n").filter((l) => l.trim().length > 0);
      const parsedMeds = lines.map((line, idx) => {
        const parts = line.split("|").map((p) => p.trim());
        const name = parts[0] || `Medication ${idx + 1}`;
        const dosage = parts[1] || "1 dose";
        const frequency = parts[2] || "Once daily";
        const rawSlots = parts[3] ? parts[3].split(",").map((s) => s.trim()) : ["09:00 AM"];
        const instructions = parts[4] || "Take as prescribed by doctor";

        return {
          id: `med-${idx + 1}`,
          patient_id: patientId,
          name,
          dosage,
          frequency,
          timing_slots: rawSlots,
          instructions,
          prescribed_by: rxDoctor,
          duration: "90 Days",
          warnings: name.toLowerCase().includes("metformin")
            ? ["Take with food to prevent GI upset"]
            : name.toLowerCase().includes("atorvastatin")
            ? ["Avoid grapefruit juice"]
            : name.toLowerCase().includes("lisinopril")
            ? ["Monitor blood pressure regularly"]
            : [],
        };
      });

      const prescriptionPayload = {
        patient_id: patientId,
        rx_number: `RX-${Math.floor(10000 + Math.random() * 90000)}-DOC`,
        doctor_name: rxDoctor,
        clinic_name: rxClinic,
        diagnosis: rxDiagnosis,
        issued_date: new Date().toISOString().split("T")[0],
        medications: parsedMeds,
      };

      await uploadPrescription(prescriptionPayload);
      setShowRxModal(false);
      setRefreshTrigger((prev) => prev + 1);
    } catch (err) {
      console.error("Prescription upload error:", err);
      setRxError(err.message || "Failed to apply prescription");
    } finally {
      setRxSubmitting(false);
    }
  };

  // Preset Prescription Loaders
  const loadPresetRx = (presetType) => {
    if (presetType === "cardio") {
      setRxDoctor("Dr. Anita Sengupta, MD (Cardiology & Diabetology)");
      setRxClinic("Max Healthcare Multispeciality Clinic");
      setRxDiagnosis("Type 2 Diabetes Mellitus & Essential Hypertension");
      setRxMedsInput(
        "Metformin XR | 500mg | Twice daily after meals | 08:00 AM, 08:00 PM | Take with breakfast and dinner\nLisinopril | 10mg | Once daily morning | 09:00 AM | Take in morning with water\nAtorvastatin | 20mg | Once daily bedtime | 10:00 PM | Take at night before sleep"
      );
    } else if (presetType === "ortho") {
      setRxDoctor("Dr. Rajiv Mehta, MS (Orthopedic Surgery)");
      setRxClinic("Fortis Bone & Joint Institute");
      setRxDiagnosis("Post-Operative Knee Arthroplasty & Acute Inflammation");
      setRxMedsInput(
        "Amoxicillin | 500mg | Three times daily with food | 08:00 AM, 02:00 PM, 08:00 PM | Complete full 10-day antibiotic course\nParacetamol | 650mg | As needed for pain (Max 4g/day) | 09:00 AM, 09:00 PM | Do not take with other acetaminophen\nPantoprazole | 40mg | Once daily before breakfast | 07:30 AM | Take 30 mins before morning food"
      );
    } else if (presetType === "neuro") {
      setRxDoctor("Dr. Sunita Rao, DM (Neurology)");
      setRxClinic("Apollo Institute of Neurosciences");
      setRxDiagnosis("Migraine Prophylaxis & Tension Headache");
      setRxMedsInput(
        "Propranolol | 40mg | Once daily morning | 08:30 AM | Monitor resting pulse rate\nNaproxen | 250mg | Twice daily after meals | 09:00 AM, 09:00 PM | Take with plenty of water\nVitamin B2 (Riboflavin) | 400mg | Once daily morning | 08:30 AM | Dietary migraine supplement"
      );
    }
  };

  const isReadOnly = data?.caregiver_permission === "read_only";
  const adherenceRate = data?.adherence_summary?.adherence_rate ?? 0;
  const activePrescription = data?.prescriptions && data.prescriptions.length > 0 ? data.prescriptions[data.prescriptions.length - 1] : null;

  // Compute color & tier for Adherence Gauge
  const getAdherenceColor = (rate) => {
    if (rate >= 80) return "var(--success)";
    if (rate >= 50) return "var(--severity-medium-text)";
    return "#ef4444";
  };

  const getAdherenceTier = (rate) => {
    if (rate >= 80) return { label: "High Adherence", class: "tier-high" };
    if (rate >= 50) return { label: "Moderate Risk", class: "tier-med" };
    return { label: "Action Required", class: "tier-low" };
  };

  // SVG circle calculations for progress ring
  const circleRadius = 30;
  const circumference = 2 * Math.PI * circleRadius;
  const strokeDashoffset = circumference - (Math.min(adherenceRate, 100) / 100) * circumference;

  return (
    <div className="dashboard-container">
      {/* Top Banner / Patient Header */}
      <div className="dashboard-header-card">
        <div className="patient-title-group">
          <div className="patient-avatar-box">👤</div>
          <div>
            <div className="badge-row">
              <span className="patient-type-pill">Monitored Patient</span>
              <span
                className={`permission-pill ${
                  isReadOnly ? "perm-read-pill" : "perm-respond-pill"
                }`}
              >
                {isReadOnly ? "👁️ Read-Only" : "✓ Read & Respond"}
              </span>
            </div>
            <h1 className="patient-name-title">
              {data?.patient_name || `Patient ${patientId}`}
            </h1>
            <span className="patient-meta-id">ID: {patientId}</span>
          </div>
        </div>

        <div className="header-actions-group">
          <button
            onClick={() => setShowRxModal(true)}
            className="btn-primary"
            title="Import or view official doctor's prescription"
          >
            <span>📜</span>
            <span>Import / Switch Rx</span>
          </button>
          <button
            onClick={() => setRefreshTrigger((prev) => prev + 1)}
            className="btn-refresh"
            title="Refresh dashboard data"
          >
            ↻ Refresh
          </button>
          <button onClick={onOpenInvite} className="btn-secondary">
            <span>👥</span>
            <span>Manage Invites</span>
          </button>
          <button onClick={onOpenChat} className="btn-action-primary">
            <span>💬</span>
            <span>Clinical Assistant</span>
          </button>
        </div>
      </div>

      {/* Prescription Modal Dialog */}
      {showRxModal && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0,0,0,0.6)",
            backdropFilter: "blur(4px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 100,
            padding: "1rem",
          }}
        >
          <div
            className="card-box"
            style={{
              maxWidth: "680px",
              width: "100%",
              maxHeight: "90vh",
              overflowY: "auto",
              boxShadow: "var(--shadow-lg)",
            }}
          >
            <div className="card-header-row">
              <div className="header-title-group">
                <span className="icon-badge">📜</span>
                <div>
                  <h3 className="section-title">Clinical Prescription (Rx) Import</h3>
                  <p style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                    Derives medications, dosage timings, and adherence telemetry directly from doctor Rx
                  </p>
                </div>
              </div>
              <button
                onClick={() => setShowRxModal(false)}
                className="btn-text-sm"
                style={{ fontSize: "1.25rem", cursor: "pointer" }}
              >
                ✕
              </button>
            </div>

            {/* Quick Presets */}
            <div style={{ marginBottom: "1rem" }}>
              <span style={{ fontSize: "0.75rem", fontWeight: "700", color: "var(--text-secondary)", display: "block", marginBottom: "0.4rem" }}>
                Select Doctor Prescription Template:
              </span>
              <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                <button
                  type="button"
                  onClick={() => loadPresetRx("cardio")}
                  className="chip-btn"
                  style={{ fontWeight: "600" }}
                >
                  🫀 Cardiology & Diabetes (Dr. Sengupta)
                </button>
                <button
                  type="button"
                  onClick={() => loadPresetRx("ortho")}
                  className="chip-btn"
                  style={{ fontWeight: "600" }}
                >
                  🦴 Orthopedic & Antibiotics (Dr. Mehta)
                </button>
                <button
                  type="button"
                  onClick={() => loadPresetRx("neuro")}
                  className="chip-btn"
                  style={{ fontWeight: "600" }}
                >
                  🧠 Neurology & Pain (Dr. Rao)
                </button>
              </div>
            </div>

            <form onSubmit={handleUploadPrescription}>
              <div className="form-group-grid">
                <div className="form-field">
                  <label>Prescribing Physician</label>
                  <input
                    type="text"
                    value={rxDoctor}
                    onChange={(e) => setRxDoctor(e.target.value)}
                    required
                    className="form-input"
                  />
                </div>
                <div className="form-field">
                  <label>Hospital / Clinic Name</label>
                  <input
                    type="text"
                    value={rxClinic}
                    onChange={(e) => setRxClinic(e.target.value)}
                    required
                    className="form-input"
                  />
                </div>
              </div>

              <div className="form-field">
                <label>Clinical Diagnosis / Indication</label>
                <input
                  type="text"
                  value={rxDiagnosis}
                  onChange={(e) => setRxDiagnosis(e.target.value)}
                  required
                  className="form-input"
                />
              </div>

              <div className="form-field">
                <label>
                  Prescribed Medicines (Format: <code>Name | Dosage | Frequency | Daily Slots | Instructions</code>)
                </label>
                <textarea
                  rows="4"
                  value={rxMedsInput}
                  onChange={(e) => setRxMedsInput(e.target.value)}
                  required
                  className="form-textarea"
                  style={{ fontSize: "0.8rem", fontFamily: "monospace" }}
                />
              </div>

              {rxError && (
                <div className="error-banner mb-4">
                  <span>⚠️ {rxError}</span>
                </div>
              )}

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.75rem", marginTop: "1rem" }}>
                <button
                  type="button"
                  onClick={() => setShowRxModal(false)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={rxSubmitting}
                  className="btn-primary"
                >
                  {rxSubmitting ? "Generating Schedule from Rx..." : "Apply Prescription & Generate Schedule →"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {loading && !data && (
        <div className="loading-state" style={{ minHeight: "300px", flexDirection: "column" }}>
          <div className="spinner-lg"></div>
          <p>Syncing adherence telemetry & timetable...</p>
        </div>
      )}

      {error && (
        <div className="error-banner mb-6">
          <span>⚠️ {error}</span>
          <button onClick={fetchDashboardData} className="btn-primary-sm">
            Retry
          </button>
        </div>
      )}

      {data && (
        <>
          {/* Active Prescription Badge Header */}
          {activePrescription && (
            <div
              className="card-box mb-6"
              style={{
                background: "linear-gradient(135deg, var(--bg-surface) 0%, var(--bg-surface-elevated) 100%)",
                borderLeft: "4px solid var(--primary)",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "0.5rem" }}>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.25rem" }}>
                    <span style={{ fontSize: "0.7rem", fontWeight: "800", textTransform: "uppercase", background: "var(--primary-light)", color: "var(--primary)", padding: "0.15rem 0.5rem", borderRadius: "4px" }}>
                      Active Clinical Prescription
                    </span>
                    <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontWeight: "600" }}>
                      Rx ID: {activePrescription.rx_number || activePrescription.id}
                    </span>
                  </div>
                  <h3 style={{ fontSize: "1.1rem", fontWeight: "800", color: "var(--text-primary)" }}>
                    {activePrescription.doctor_name}
                  </h3>
                  <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                    {activePrescription.clinic_name} • <strong>Diagnosis:</strong> {activePrescription.diagnosis}
                  </p>
                </div>
                <button
                  onClick={() => setShowRxModal(true)}
                  className="btn-text-sm"
                  style={{ alignSelf: "center" }}
                >
                  ✎ Edit / Switch Rx
                </button>
              </div>
            </div>
          )}

          {/* Adherence & Key Metrics Row */}
          <div className="metrics-summary-grid">
            {/* Prominent SVG Adherence Gauge Card */}
            <div className="metric-card adherence-hero-card">
              <div className="metric-header-row">
                <span className="metric-label">Adherence Rate</span>
                <span className="sub-counter">From Prescription</span>
              </div>
              <div className="adherence-flex-content">
                <div className="progress-ring-container">
                  <svg width="76" height="76">
                    <circle
                      className="progress-ring-circle-bg"
                      strokeWidth="6"
                      r={circleRadius}
                      cx="38"
                      cy="38"
                    />
                    <circle
                      className="progress-ring-circle-fill"
                      strokeWidth="6"
                      stroke={getAdherenceColor(adherenceRate)}
                      strokeDasharray={`${circumference} ${circumference}`}
                      style={{ strokeDashoffset }}
                      r={circleRadius}
                      cx="38"
                      cy="38"
                    />
                  </svg>
                  <span className="progress-ring-text">{adherenceRate}%</span>
                </div>
                <div className="adherence-status-col">
                  <span className={`adherence-tier-badge ${getAdherenceTier(adherenceRate).class}`}>
                    {getAdherenceTier(adherenceRate).label}
                  </span>
                  <span className="adherence-subtext">
                    {data.adherence_summary.taken_count} of {data.adherence_summary.total_scheduled} doses logged
                  </span>
                </div>
              </div>
            </div>

            <div className="metric-card">
              <div className="metric-header-row">
                <span className="metric-label">Doses Taken</span>
                <div className="metric-icon-box box-emerald">✓</div>
              </div>
              <span className="metric-val">{data.adherence_summary.taken_count}</span>
              <span className="metric-desc">Successfully taken today</span>
            </div>

            <div className="metric-card">
              <div className="metric-header-row">
                <span className="metric-label">Missed Doses</span>
                <div className="metric-icon-box box-rose">✕</div>
              </div>
              <span className="metric-val">{data.adherence_summary.missed_count}</span>
              <span className="metric-desc">Triggered threshold alert</span>
            </div>

            <div className="metric-card">
              <div className="metric-header-row">
                <span className="metric-label">Upcoming</span>
                <div className="metric-icon-box box-blue">⏳</div>
              </div>
              <span className="metric-val">{data.adherence_summary.upcoming_count}</span>
              <span className="metric-desc">Scheduled for today</span>
            </div>
          </div>

          {/* Active Medications & Schedule Grid */}
          <div className="two-column-layout">
            <div className="column-left">
              {/* Upcoming & Recent Doses */}
              <div className="card-box mb-6">
                <div className="card-header-row">
                  <div className="header-title-group">
                    <span className="icon-badge">📅</span>
                    <div>
                      <h3 className="section-title">Medication Schedule & History</h3>
                      <p style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                        Generated from active prescription timing slots
                      </p>
                    </div>
                  </div>
                  <span className="sub-counter">
                    {data.recent_doses.length} scheduled slots
                  </span>
                </div>

                <div className="dose-timeline-list">
                  {data.recent_doses.map((dose) => (
                    <div key={dose.id} className="timeline-item">
                      <div className={`status-indicator status-${dose.status}`}></div>
                      <div className="dose-content-block">
                        <div className="dose-title-row">
                          <strong className="dose-med-name">
                            {dose.medication_name}
                          </strong>
                          <span className={`dose-status-pill pill-${dose.status}`}>
                            {dose.status.toUpperCase()}
                          </span>
                        </div>
                        <div className="dose-meta-row">
                          <span>Dosage: <strong>{dose.dosage}</strong></span>
                          <span>•</span>
                          <span>Time: {dose.scheduled_time}</span>
                          {dose.taken_time && (
                            <>
                              <span>•</span>
                              <span className="text-taken">Taken: {dose.taken_time}</span>
                            </>
                          )}
                        </div>
                        {dose.notes && (
                          <div className="dose-notes-snippet">
                            <em>Instructions:</em> {dose.notes}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Shared Caregiver & Patient Notes */}
              <div className="card-box">
                <div className="card-header-row">
                  <div className="header-title-group">
                    <span className="icon-badge">📝</span>
                    <h3 className="section-title">Shared Care Notes</h3>
                  </div>
                  <span className="sub-counter">{data.notes.length} notes</span>
                </div>

                {isReadOnly && (
                  <div className="info-banner mb-4">
                    <span>
                      ℹ️ You are in <strong>Read-Only</strong> mode. To leave notes for the patient or family, request <strong>Read & Respond</strong> access.
                    </span>
                  </div>
                )}

                {/* Add Note Form */}
                {!isReadOnly && (
                  <form onSubmit={handleAddNote} className="add-note-form mb-4">
                    <textarea
                      rows="2"
                      placeholder="Leave a vitals observation, symptom update, or reminder..."
                      value={newNoteText}
                      onChange={(e) => setNewNoteText(e.target.value)}
                      className="note-textarea"
                    />
                    {noteError && (
                      <span className="text-danger-sm" style={{ color: "#ef4444", fontSize: "0.75rem", display: "block", marginTop: "4px" }}>
                        ⚠️ {noteError}
                      </span>
                    )}
                    <div className="form-action-right">
                      <button
                        type="submit"
                        disabled={submittingNote || !newNoteText.trim()}
                        className="btn-primary-sm"
                      >
                        {submittingNote ? "Posting Note..." : "Post Care Note →"}
                      </button>
                    </div>
                  </form>
                )}

                {/* Notes Stream */}
                <div className="notes-stream sleek-scroll">
                  {data.notes.length === 0 ? (
                    <div className="empty-state">
                      <p>No notes posted yet for this patient.</p>
                    </div>
                  ) : (
                    data.notes.map((note) => (
                      <div key={note.id} className="note-card">
                        <div className="note-top-row">
                          <div className="note-author-info">
                            <strong>{note.author_name}</strong>
                            <span
                              className={`author-role-badge ${
                                note.author_role === "caregiver"
                                  ? "badge-cg"
                                  : "badge-pt"
                              }`}
                            >
                              {note.author_role}
                            </span>
                          </div>
                          <span className="note-time">
                            {new Date(note.created_at).toLocaleString([], {
                              month: "short",
                              day: "numeric",
                              hour: "2-digit",
                              minute: "2-digit",
                            })}
                          </span>
                        </div>
                        <p className="note-text">{note.content}</p>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>

            <div className="column-right">
              {/* Standalone Alerts Feed Component */}
              <AlertsFeed
                patientId={patientId}
                refreshTrigger={refreshTrigger}
              />

              {/* Active Prescriptions Overview */}
              <div className="card-box mt-6">
                <div className="card-header-row">
                  <div className="header-title-group">
                    <span className="icon-badge">💊</span>
                    <div>
                      <h3 className="section-title">Prescribed Regimen</h3>
                      <p style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                        Rx: {activePrescription?.doctor_name?.split(",")[0] || "Doctor"}
                      </p>
                    </div>
                  </div>
                  <span className="sub-counter">
                    {data.active_medications?.length || 0} items
                  </span>
                </div>

                <div className="active-meds-list">
                  {data.active_medications?.map((med) => (
                    <div key={med.id} className="active-med-item">
                      <div className="med-row">
                        <strong style={{ color: "var(--text-primary)" }}>{med.name}</strong>
                        <span className="med-dosage-tag">{med.dosage}</span>
                      </div>
                      <p className="med-freq"><strong>Frequency:</strong> {med.frequency}</p>
                      {med.instructions && (
                        <p className="med-inst">💡 {med.instructions}</p>
                      )}
                      {med.warnings && med.warnings.length > 0 && (
                        <div className="med-warning-tag">
                          ⚠️ {med.warnings.join(", ")}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
