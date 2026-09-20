import { apiClient } from './api';

export const providerService = {
  getDashboard: async () => {
    const response = await apiClient.get('/provider/dashboard');
    return response.data;
  },

  getAppointments: async (params = {}) => {
    const response = await apiClient.get('/provider/appointments', { params });
    return response.data;
  },

  updateAppointmentStatus: async (appointmentId, status, notes = '') => {
    const response = await apiClient.put(`/provider/appointments/${appointmentId}/status`, {
      status,
      notes
    });
    return response.data;
  },

  getSchedule: async () => {
    const response = await apiClient.get('/provider/schedule');
    return response.data;
  },

  createLeaveException: async (leaveData) => {
    const response = await apiClient.post('/provider/schedule-exceptions', leaveData);
    return response.data;
  }
};
