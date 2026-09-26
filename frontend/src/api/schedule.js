// frontend/src/api/schedule.js
import axios from 'axios';

const getBaseUrl = () => {
  try {
    if (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_BASE_URL) {
      return import.meta.env.VITE_API_BASE_URL;
    }
  } catch (e) {}
  try {
    if (typeof process !== 'undefined' && process.env?.REACT_APP_API_BASE_URL) {
      return process.env.REACT_APP_API_BASE_URL;
    }
  } catch (e) {}
  return '';
};

const BASE_URL = getBaseUrl();

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Helper to extract detailed error message from FastAPI responses
const getErrorMessage = (error) => {
  if (error.response && error.response.data) {
    if (typeof error.response.data.detail === 'string') {
      return error.response.data.detail;
    }
    if (Array.isArray(error.response.data.detail)) {
      return error.response.data.detail.map(d => d.msg || JSON.stringify(d)).join(', ');
    }
    if (error.response.data.message) {
      return error.response.data.message;
    }
  }
  return error.message || 'An unexpected error occurred.';
};

export const fetchDashboard = async (userId = 'user-1') => {
  try {
    const response = await api.get(`/api/schedule/dashboard`, {
      params: { user_id: userId, base_url: BASE_URL }
    });
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error));
  }
};

export const fetchTodayDoses = async (userId = 'user-1') => {
  try {
    const response = await api.get(`/api/schedule/today`, {
      params: { user_id: userId }
    });
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error));
  }
};

export const fetchScheduleTimeline = async (userId = 'user-1', viewType = 'daily', startDate = null) => {
  try {
    const params = { user_id: userId, view_type: viewType };
    if (startDate) params.start_date = startDate;
    const response = await api.get(`/api/schedule/timeline`, { params });
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error));
  }
};

export const fetchAdherenceSummary = async (userId = 'user-1', period = 'today', targetDate = null) => {
  try {
    const params = { user_id: userId, period };
    if (targetDate) params.target_date = targetDate;
    const response = await api.get(`/api/schedule/adherence`, { params });
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error));
  }
};

export const markDoseStatus = async (doseId, status, notes = null, takenAt = null) => {
  try {
    const response = await api.post(`/api/schedule/dose/${doseId}/mark`, {
      status,
      notes,
      taken_at: takenAt
    });
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error));
  }
};

export const generateSchedule = async (userId = 'user-1', prescriptionId = null, prescriptionData = null) => {
  try {
    const response = await api.post(`/api/schedule/generate`, {
      user_id: userId,
      prescription_id: prescriptionId,
      prescription_data: prescriptionData
    });
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error));
  }
};

export const checkEscalations = async (userId = 'user-1') => {
  try {
    const response = await api.post(`/api/schedule/check-escalations`, {
      user_id: userId
    });
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error));
  }
};

export const checkAntiStacking = async (userId = 'user-1', medicationName = '', doseId = null) => {
  try {
    const response = await api.post(`/api/schedule/anti-stacking/check`, {
      user_id: userId,
      medication_name: medicationName,
      dose_id: doseId
    });
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error));
  }
};

export const fetchEscalationHistory = async (userId = 'user-1') => {
  try {
    const response = await api.get(`/api/schedule/escalations`, {
      params: { user_id: userId }
    });
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error));
  }
};

export const fetchActivityHistory = async (userId = 'user-1', limit = 10) => {
  try {
    const response = await api.get(`/api/schedule/activities`, {
      params: { user_id: userId, limit }
    });
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error));
  }
};

export const fetchReminders = async (userId = 'user-1', lookaheadMinutes = 30) => {
  try {
    const response = await api.get(`/api/schedule/reminders`, {
      params: { user_id: userId, lookahead_minutes: lookaheadMinutes }
    });
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error));
  }
};
