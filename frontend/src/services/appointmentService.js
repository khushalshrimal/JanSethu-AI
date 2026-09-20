import { apiClient } from './api';

export const appointmentService = {
  createAppointment: async (payload) => {
    const response = await apiClient.post('/appointments/', {
      doctor_id: payload.doctor_id,
      facility_id: payload.facility_id || null,
      department_id: payload.department_id || null,
      patient_id: payload.patient_id || null,
      appointment_date: payload.date || payload.appointment_date,
      start_time: payload.start_time,
      end_time: payload.end_time || null,
      booking_channel: payload.booking_channel || 'PWA',
      reason_for_visit: payload.reason || payload.reason_for_visit || null,
      patient_name: payload.patient_name || null,
      patient_phone: payload.patient_phone || null,
      patient_age: payload.patient_age || null,
      patient_gender: payload.patient_gender || null,
    });
    return response.data;
  },

  bookAppointment: async (appointmentData) => {
    return appointmentService.createAppointment(appointmentData);
  },

  getAppointmentDetails: async (appointment_id) => {
    const response = await apiClient.get(`/appointments/${appointment_id}`);
    return response.data;
  },

  getMyAppointments: async (filters = {}) => {
    const params = new URLSearchParams();
    if (filters.status) params.append('status', filters.status);
    if (filters.date) params.append('date', filters.date);
    if (filters.upcoming) params.append('upcoming', 'true');
    const response = await apiClient.get(`/appointments/me?${params.toString()}`);
    return response.data;
  },

  cancelAppointment: async (appointment_id, reason = 'Patient request') => {
    const response = await apiClient.put(`/appointments/${appointment_id}/cancel`, {
      cancellation_reason: reason
    });
    return response.data;
  },

  rescheduleAppointment: async (appointment_id, new_date, new_start_time, new_end_time = null, reason = 'Rescheduled by patient') => {
    const response = await apiClient.put(`/appointments/${appointment_id}/reschedule`, {
      new_appointment_date: new_date,
      new_start_time: new_start_time,
      new_end_time: new_end_time,
      reschedule_reason: reason
    });
    return response.data;
  },

  getByConfirmationCode: async (code) => {
    const response = await apiClient.get(`/appointments/confirmation/${code}`);
    return response.data;
  },

  checkInAppointment: async (appointment_id) => {
    const response = await apiClient.post(`/appointments/${appointment_id}/check-in`);
    return response.data;
  },

  getVisitStatus: async (appointment_id) => {
    const response = await apiClient.get(`/appointments/${appointment_id}/visit-status`);
    return response.data;
  },

  startConsultation: async (appointment_id) => {
    const response = await apiClient.post(`/provider/appointments/${appointment_id}/start-consultation`);
    return response.data;
  },

  completeConsultation: async (appointment_id) => {
    const response = await apiClient.post(`/provider/appointments/${appointment_id}/complete-consultation`);
    return response.data;
  },

  markNoShow: async (appointment_id) => {
    const response = await apiClient.post(`/provider/appointments/${appointment_id}/no-show`);
    return response.data;
  }
};

export const createAppointment = appointmentService.createAppointment;
export const bookAppointment = appointmentService.bookAppointment;
export const getAppointmentDetails = appointmentService.getAppointmentDetails;
export const getMyAppointments = appointmentService.getMyAppointments;
export const cancelAppointment = appointmentService.cancelAppointment;
export const rescheduleAppointment = appointmentService.rescheduleAppointment;
export const getByConfirmationCode = appointmentService.getByConfirmationCode;
export const lookupAppointmentByConfirmationCode = appointmentService.getByConfirmationCode;
export const checkInAppointment = appointmentService.checkInAppointment;
export const getVisitStatus = appointmentService.getVisitStatus;
export const startConsultation = appointmentService.startConsultation;
export const completeConsultation = appointmentService.completeConsultation;
export const markNoShow = appointmentService.markNoShow;
