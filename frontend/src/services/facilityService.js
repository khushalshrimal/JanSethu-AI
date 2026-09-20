import { apiClient } from './api';

export const facilityService = {
  getFacilities: async (filters = {}) => {
    return facilityService.searchFacilities(filters);
  },

  searchFacilities: async (params = {}) => {
    const queryParams = new URLSearchParams();
    if (params.q) queryParams.append('q', params.q);
    if (params.pincode) queryParams.append('pincode', params.pincode);
    if (params.district) queryParams.append('district', params.district);
    if (params.village) queryParams.append('village', params.village);
    if (params.facility_type) queryParams.append('facility_type', params.facility_type);
    if (params.emergency_capable !== undefined && params.emergency_capable !== null && params.emergency_capable !== '') {
      queryParams.append('emergency_capable', params.emergency_capable);
    }
    if (params.emergency_only !== undefined && params.emergency_only !== null && params.emergency_only !== '') {
      queryParams.append('emergency_capable', params.emergency_only);
    }
    if (params.department_id) queryParams.append('department_id', params.department_id);
    if (params.latitude !== undefined && params.latitude !== null) queryParams.append('latitude', params.latitude);
    if (params.longitude !== undefined && params.longitude !== null) queryParams.append('longitude', params.longitude);
    if (params.radius_km) queryParams.append('radius_km', params.radius_km);
    if (params.search) queryParams.append('q', params.search);

    const response = await apiClient.get(`/facilities/search?${queryParams.toString()}`);
    return response.data;
  },

  getNearbyFacilities: async (latitude, longitude, radius_km = 20) => {
    return facilityService.searchFacilities({ latitude, longitude, radius_km });
  },

  getFacilityDetails: async (facility_id) => {
    const response = await apiClient.get(`/facilities/${facility_id}`);
    return response.data;
  },

  getFacilityDepartments: async (facility_id) => {
    const response = await apiClient.get(`/facilities/${facility_id}/departments`);
    return response.data;
  }
};

export const getFacilities = facilityService.getFacilities;
export const searchFacilities = facilityService.searchFacilities;
export const getNearbyFacilities = facilityService.getNearbyFacilities;
export const searchNearbyFacilities = facilityService.getNearbyFacilities;
export const getFacilityDetails = facilityService.getFacilityDetails;
export const getFacilityDepartments = facilityService.getFacilityDepartments;

