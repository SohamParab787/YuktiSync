/**
 * Caregiver API Client
 * YuktiSync - Person 4 Module
 * Interacts with backend /api/caregiver/* endpoints
 */

const API_BASE_URL = (typeof window !== "undefined" && window.__API_URL__) 
  || import.meta.env?.VITE_API_BASE_URL 
  || "/api";

/**
 * Generic fetch wrapper with automatic JSON parsing and auth header attachment
 */
async function request(endpoint, options = {}) {
  const token = typeof localStorage !== "undefined" ? localStorage.getItem("yukti_token") : null;
  const currentUserId = typeof localStorage !== "undefined" ? localStorage.getItem("yukti_user_id") || "caregiver-201" : "caregiver-201";
  const currentUserRole = typeof localStorage !== "undefined" ? localStorage.getItem("yukti_user_role") || "caregiver" : "caregiver";

  const headers = {
    "Content-Type": "application/json",
    "X-User-Id": currentUserId,
    "X-User-Role": currentUserRole,
    ...(options.headers || {}),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const config = {
    ...options,
    headers,
  };

  const response = await fetch(`${API_BASE_URL}${endpoint}`, config);

  if (!response.ok) {
    let errorDetail = `Request failed with status ${response.status}`;
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || errorDetail;
    } catch (_) {
      // fallback to status text
      errorDetail = response.statusText || errorDetail;
    }
    const err = new Error(errorDetail);
    err.status = response.status;
    throw err;
  }

  return response.json();
}

/**
 * Generate a new caregiver invitation
 */
export async function createInvite({ patient_id, caregiver_email, caregiver_name, permissions, expires_in_days = 7 }) {
  return request("/caregiver/invite", {
    method: "POST",
    body: JSON.stringify({
      patient_id,
      caregiver_email,
      caregiver_name,
      permissions: permissions || "read_respond",
      expires_in_days: Number(expires_in_days) || 7,
    }),
  });
}

/**
 * Accept an invitation token
 */
export async function acceptInvite({ invite_token, caregiver_id, caregiver_name }) {
  return request("/caregiver/invite/accept", {
    method: "POST",
    body: JSON.stringify({
      invite_token,
      caregiver_id,
      caregiver_name,
    }),
  });
}

/**
 * Revoke caregiver access
 */
export async function revokeAccess(linkId) {
  return request(`/caregiver/invite/${linkId}`, {
    method: "DELETE",
  });
}

/**
 * List all caregivers linked or invited for a patient
 */
export async function listLinkedCaregivers(patientId) {
  return request(`/caregiver/invite/list/${patientId}`);
}

/**
 * List all patients linked to current caregiver
 */
export async function listLinkedPatients() {
  return request("/caregiver/patients");
}

/**
 * Fetch consolidated dashboard data for patient
 */
export async function getDashboard(patientId) {
  return request(`/caregiver/dashboard/${patientId}`);
}

/**
 * Add a shared note on patient record
 */
export async function createNote({ patient_id, content }) {
  return request("/caregiver/notes", {
    method: "POST",
    body: JSON.stringify({
      patient_id,
      content,
    }),
  });
}

/**
 * Retrieve notes for patient
 */
export async function getNotes(patientId) {
  return request(`/caregiver/notes/${patientId}`);
}

/**
 * Retrieve missed-dose alerts feed for patient
 */
export async function getAlerts(patientId) {
  return request(`/caregiver/alerts/${patientId}`);
}

/**
 * Send natural language medication query to RAG-grounded chat assistant
 */
export async function sendChatQuery({ patient_id, query }) {
  return request("/caregiver/chat", {
    method: "POST",
    body: JSON.stringify({
      patient_id,
      query,
    }),
  });
}

/**
 * Upload/Apply a clinical prescription
 */
export async function uploadPrescription(prescriptionData) {
  return request("/caregiver/prescription", {
    method: "POST",
    body: JSON.stringify(prescriptionData),
  });
}

/**
 * Retrieve patient's prescriptions
 */
export async function getPrescriptions(patientId) {
  return request(`/caregiver/prescription/${patientId}`);
}

export default {
  createInvite,
  acceptInvite,
  revokeAccess,
  listLinkedCaregivers,
  listLinkedPatients,
  getDashboard,
  createNote,
  getNotes,
  getAlerts,
  sendChatQuery,
  uploadPrescription,
  getPrescriptions,
};
