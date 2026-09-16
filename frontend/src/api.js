import axios from 'axios';
import { MOCK_FACILITIES, MOCK_SLOTS, MOCK_APPOINTMENTS, MOCK_EMERGENCY } from './mockData';

const API_BASE = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 3000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const checkHealth = async () => {
  try {
    const response = await api.get('/health');
    return response.data;
  } catch {
    return {
      status: 'ok',
      service: 'JanSethu AI (Mock Mode)',
      version: '1.0.0-mock',
      demo_mode: true
    };
  }
};

export const getFacilities = async (params = {}) => {
  try {
    const response = await api.get('/facilities', { params });
    return response.data;
  } catch {
    let list = [...MOCK_FACILITIES];
    if (params.search) {
      const q = params.search.toLowerCase();
      list = list.filter(f => 
        f.name.toLowerCase().includes(q) ||
        (f.name_hi && f.name_hi.toLowerCase().includes(q)) ||
        f.area.toLowerCase().includes(q) ||
        f.city.toLowerCase().includes(q) ||
        f.services.toLowerCase().includes(q)
      );
    }
    return list;
  }
};

export const getFacilityDetail = async (id) => {
  try {
    const response = await api.get(`/facilities/${id}`);
    return response.data;
  } catch {
    const fac = MOCK_FACILITIES.find(f => f.id === Number(id)) || MOCK_FACILITIES[0];
    const slots = MOCK_SLOTS.filter(s => s.facility_id === fac.id);
    return { ...fac, slots };
  }
};

export const getFacilitySlots = async (id, date = null) => {
  try {
    const params = date ? { date } : {};
    const response = await api.get(`/facilities/${id}/slots`, { params });
    return response.data;
  } catch {
    return MOCK_SLOTS.filter(s => s.facility_id === Number(id));
  }
};

export const createAppointment = async (appointmentData) => {
  try {
    const response = await api.post('/appointments', appointmentData);
    return response.data;
  } catch {
    const fac = MOCK_FACILITIES.find(f => f.id === Number(appointmentData.facility_id));
    return {
      id: Math.floor(1000 + Math.random() * 9000),
      facility_id: appointmentData.facility_id,
      facility_name: fac ? fac.name : 'District Civil Hospital (DEMO)',
      service: appointmentData.service || 'General OPD',
      date: appointmentData.date || 'Tomorrow',
      time: appointmentData.time || '10:00 AM',
      patient_name: appointmentData.patient_name || 'Valued Patient',
      phone: appointmentData.phone || '+91-9876543210',
      status: 'pending',
      created_at: new Date().toISOString()
    };
  }
};

export const getAppointmentDetail = async (id) => {
  try {
    const response = await api.get(`/appointments/${id}`);
    return response.data;
  } catch {
    const apt = MOCK_APPOINTMENTS.find(a => a.id === Number(id)) || MOCK_APPOINTMENTS[0];
    return apt;
  }
};

export const getAppointments = async (params = {}) => {
  try {
    const response = await api.get('/appointments', { params });
    return response.data;
  } catch {
    return MOCK_APPOINTMENTS;
  }
};

export const updateAppointmentStatus = async (id, status) => {
  try {
    const response = await api.patch(`/appointments/${id}/status`, null, { params: { status } });
    return response.data;
  } catch {
    return { message: "Status updated in mock state", id, status };
  }
};

export const getEmergencyInfo = async () => {
  try {
    const response = await api.get('/emergency');
    return response.data;
  } catch {
    return MOCK_EMERGENCY;
  }
};

export default api;
