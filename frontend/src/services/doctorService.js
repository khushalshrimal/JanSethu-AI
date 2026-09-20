import { apiClient } from './api';

export const doctorService = {
  getDoctors: async (paramsOrFacilityId, department_id = null) => {
    let facId = paramsOrFacilityId;
    let deptId = department_id;

    if (typeof paramsOrFacilityId === 'object' && paramsOrFacilityId !== null) {
      facId = paramsOrFacilityId.facility_id;
      deptId = paramsOrFacilityId.department_id;
    }

    let url = `/doctors?facility_id=${facId}`;
    if (deptId) {
      url += `&department_id=${deptId}`;
    }
    const response = await apiClient.get(url);
    return response.data;
  },

  getDoctorDetails: async (doctor_id) => {
    const response = await apiClient.get(`/doctors/${doctor_id}`);
    return response.data;
  },

  getDoctorAvailability: async (doctor_id, target_date) => {
    const response = await apiClient.get(`/doctors/${doctor_id}/availability?date=${target_date}`);
    return response.data; // { doctor_id, doctor_name, facility_name, department_name, slots: [...] }
  }
};

export const getDoctors = doctorService.getDoctors;
export const getDoctorDetails = doctorService.getDoctorDetails;
export const getDoctorAvailability = doctorService.getDoctorAvailability;
