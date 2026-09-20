import { apiClient } from './api';

export const adminService = {
  getDashboard: async () => {
    const response = await apiClient.get('/admin/dashboard');
    return response.data;
  },

  getFacilities: async () => {
    const response = await apiClient.get('/admin/facilities');
    return response.data;
  },

  createFacility: async (facilityData) => {
    const response = await apiClient.post('/admin/facilities', facilityData);
    return response.data;
  },

  toggleFacilityStatus: async (facilityId, isActive) => {
    const response = await apiClient.patch(`/admin/facilities/${facilityId}/status`, {
      is_active: isActive
    });
    return response.data;
  },

  createDepartment: async (facilityId, deptData) => {
    const response = await apiClient.post(`/admin/facilities/${facilityId}/departments`, deptData);
    return response.data;
  },

  toggleDepartmentStatus: async (deptId, isActive) => {
    const response = await apiClient.patch(`/admin/departments/${deptId}/status`, {
      is_active: isActive
    });
    return response.data;
  },

  getDoctors: async (facilityId = null) => {
    const params = facilityId ? { facility_id: facilityId } : {};
    const response = await apiClient.get('/admin/doctors', { params });
    return response.data;
  },

  createDoctor: async (doctorData) => {
    const response = await apiClient.post('/admin/doctors', doctorData);
    return response.data;
  },

  toggleDoctorStatus: async (doctorId, isActive) => {
    const response = await apiClient.patch(`/admin/doctors/${doctorId}/status`, {
      is_active: isActive
    });
    return response.data;
  },

  updateSchedule: async (scheduleData) => {
    const response = await apiClient.post('/admin/schedules', scheduleData);
    return response.data;
  },

  createScheduleException: async (exceptionData) => {
    const response = await apiClient.post('/admin/schedule-exceptions', exceptionData);
    return response.data;
  },

  getAppointments: async (params = {}) => {
    const response = await apiClient.get('/admin/appointments', { params });
    return response.data;
  },

  getAuditLogs: async (params = {}) => {
    const response = await apiClient.get('/admin/audit-logs', { params });
    return response.data;
  },

  getEmergencyContacts: async () => {
    const response = await apiClient.get('/admin/emergency-contacts');
    return response.data;
  },

  createEmergencyContact: async (contactData) => {
    const response = await apiClient.post('/admin/emergency-contacts', contactData);
    return response.data;
  },

  deleteEmergencyContact: async (contactId) => {
    const response = await apiClient.delete(`/admin/emergency-contacts/${contactId}`);
    return response.data;
  }
};
