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

export const sendVoiceIntent = async (voicePayload) => {
  try {
    const response = await api.post('/voice/intent', voicePayload);
    return response.data;
  } catch {
    // Fallback intent parser for offline frontend execution
    const text = (voicePayload.transcript || '').toLowerCase();
    const isHi = voicePayload.lang === 'hi';
    
    if (text.includes('emergency') || text.includes('ambulance') || text.includes('108') || text.includes('आपात') || text.includes('एम्बुलेंस')) {
      return {
        intent: 'emergency_help',
        response_text: 'For medical emergencies, please dial Ambulance 108 immediately.',
        response_text_hi: 'गंभीर चिकित्सा आपात स्थिति के लिए कृपया तुरंत एम्बुलेंस 108 पर कॉल करें।',
        action: 'navigate_emergency'
      };
    }
    
    if (text.includes('doctor') || text.includes('appointment') || text.includes('book') || text.includes('दिखाना') || text.includes('डॉक्टर')) {
      if (!text.includes('sanganer') && !text.includes('jaipur') && !text.includes('delhi') && !text.includes('सांगानेर')) {
        return {
          intent: 'appointment_request',
          response_text: 'Sure! Which city or area are you looking for?',
          response_text_hi: 'जी! आप किस शहर या क्षेत्र में अस्पताल ढूंढ रहे हैं?',
          missing_field: 'location',
          action: 'prompt_missing'
        };
      }
      return {
        intent: 'appointment_request',
        response_text: 'Found District Civil Hospital in Sanganer. Slots available tomorrow starting 9:00 AM.',
        response_text_hi: 'सांगानेर में जिला नागरिक अस्पताल उपलब्ध है। कल सुबह 9:00 बजे से स्लॉट उपलब्ध हैं।',
        matched_facility_id: 1,
        facilities: MOCK_FACILITIES,
        slots: MOCK_SLOTS,
        action: 'navigate_slots'
      };
    }

    return {
      intent: 'fallback',
      response_text: 'I could not quite understand. Try saying "I need to see a doctor tomorrow".',
      response_text_hi: 'मैं समझ नहीं पाया। कृपया "मुझे कल डॉक्टर को दिखाना है" बोलें।',
      action: 'prompt_retry'
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

export const getEmergencyFacilities = async () => {
  try {
    const response = await api.get('/emergency/facilities');
    return response.data;
  } catch {
    return MOCK_FACILITIES.filter(f => f.services.includes('Emergency') || f.facility_type.includes('Hospital'));
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

export const addSlot = async (facilityId, slotData) => {
  try {
    const response = await api.post(`/facilities/${facilityId}/slots`, slotData);
    return response.data;
  } catch {
    return { id: Date.now(), facility_id: facilityId, ...slotData };
  }
};

export const toggleSlot = async (slotId) => {
  try {
    const response = await api.patch(`/slots/${slotId}/toggle`);
    return response.data;
  } catch {
    return { id: slotId, available: false };
  }
};

export const deleteSlot = async (slotId) => {
  try {
    const response = await api.delete(`/slots/${slotId}`);
    return response.data;
  } catch {
    return { message: "Slot deleted in mock state", id: slotId };
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

export const rescheduleAppointment = async (id, newDate, newTime) => {
  try {
    const response = await api.patch(`/appointments/${id}/reschedule`, { new_date: newDate, new_time: newTime });
    return response.data;
  } catch {
    return { id, status: 'rescheduled', date: newDate, time: newTime };
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

export const getProviderEmergencyCases = async () => {
  try {
    const response = await api.get('/provider/emergency_cases');
    return response.data;
  } catch {
    return [
      {
        id: 101,
        patient_name: "Ramesh Pawar",
        phone: "+91-9876543210",
        location: "Baramati Rural (Ward 4)",
        detected_issue: "Acute Chest Tightness & Breathlessness (Voice Triage)",
        urgency: "CRITICAL 🚨",
        status: "Dispatch Requested",
        timestamp: "10 mins ago"
      },
      {
        id: 102,
        patient_name: "Sunita Kamble",
        phone: "+91-9822114455",
        location: "Sanganer Sub-centre",
        detected_issue: "Severe Pediatric Dehydration & Fever",
        urgency: "HIGH ⚠️",
        status: "Under Evaluation",
        timestamp: "25 mins ago"
      },
      {
        id: 103,
        patient_name: "Anil Deshmukh",
        phone: "+91-9765432109",
        location: "Indapur PHC Road",
        detected_issue: "Trauma / Accidental Leg Injury",
        urgency: "MEDIUM",
        status: "108 Notified",
        timestamp: "42 mins ago"
      }
    ];
  }
};

export default api;

