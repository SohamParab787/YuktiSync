// frontend/src/api/schedule.js
import axios from 'axios';

const BASE_URL = import.meta.env?.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const fetchDashboard = async (userId = 'user-1') => {
  const response = await api.get(`/api/schedule/dashboard`, {
    params: { user_id: userId, base_url: BASE_URL }
  });
  return response.data;
};

export const fetchTodayDoses = async (userId = 'user-1') => {
  const response = await api.get(`/api/schedule/today`, {
    params: { user_id: userId }
  });
  return response.data;
};

export const fetchScheduleTimeline = async (userId = 'user-1', viewType = 'daily', startDate = null) => {
  const params = { user_id: userId, view_type: viewType };
  if (startDate) params.start_date = startDate;
  const response = await api.get(`/api/schedule/timeline`, { params });
  return response.data;
};

export const fetchAdherenceSummary = async (userId = 'user-1', period = 'today', targetDate = null) => {
  const params = { user_id: userId, period };
  if (targetDate) params.target_date = targetDate;
  const response = await api.get(`/api/schedule/adherence`, { params });
  return response.data;
};

export const markDoseStatus = async (doseId, status, notes = null, takenAt = null) => {
  const response = await api.post(`/api/schedule/dose/${doseId}/mark`, {
    status,
    notes,
    taken_at: takenAt
  });
  return response.data;
};

export const generateSchedule = async (userId = 'user-1', prescriptionId = null, prescriptionData = null) => {
  const response = await api.post(`/api/schedule/generate`, {
    user_id: userId,
    prescription_id: prescriptionId,
    prescription_data: prescriptionData
  });
  return response.data;
};

export const checkEscalations = async (userId = 'user-1') => {
  const response = await api.post(`/api/schedule/check-escalations`, {
    user_id: userId
  });
  return response.data;
};

export const fetchReminders = async (userId = 'user-1', lookaheadMinutes = 30) => {
  const response = await api.get(`/api/schedule/reminders`, {
    params: { user_id: userId, lookahead_minutes: lookaheadMinutes }
  });
  return response.data;
};
