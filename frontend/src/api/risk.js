// frontend/src/api/risk.js
//
// Thin wrapper around the Risk module's two endpoints.
// Change API_BASE if your backend runs somewhere other than localhost:8000.

const API_BASE = "http://127.0.0.1:8000";

export async function checkInteractions({ medications, allergies, foodItems }) {
  const res = await fetch(`${API_BASE}/api/risk/check-interactions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      medications,
      allergies,
      food_items: foodItems,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

export async function checkMissedDose({
  drugName,
  scheduledTime,
  currentTime,
  nextScheduledTime,
}) {
  const res = await fetch(`${API_BASE}/api/risk/missed-dose-decision`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      drug_name: drugName,
      scheduled_time: scheduledTime,
      current_time: currentTime,
      next_scheduled_time: nextScheduledTime,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Request failed (${res.status})`);
  }
  return res.json();
}
