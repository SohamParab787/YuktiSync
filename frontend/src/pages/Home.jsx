import React from "react";

export default function Home({ onNavigate }) {
  return (
    <div className="card-box" style={{ maxWidth: "700px", margin: "2rem auto", textAlign: "center" }}>
      <h1 style={{ fontSize: "1.75rem", fontWeight: "800", marginBottom: "0.5rem" }}>
        Welcome to YuktiSync
      </h1>
      <p style={{ color: "#475569", marginBottom: "1.5rem" }}>
        AI-Powered Personalized Medication Management & Adherence Platform
      </p>
      <div style={{ display: "flex", gap: "1rem", justifyContent: "center" }}>
        <button
          className="btn-primary"
          onClick={() => onNavigate && onNavigate("/caregiver/dashboard")}
        >
          Open Caregiver Dashboard →
        </button>
        <button
          className="btn-secondary"
          onClick={() => onNavigate && onNavigate("/caregiver/chat")}
        >
          Ask Conversational Assistant 💬
        </button>
      </div>
    </div>
  );
}
