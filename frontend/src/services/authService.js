import { apiClient } from './api';

export const authService = {
  login: async (phone_number, password) => {
    const response = await apiClient.post('/auth/login', {
      phone_number,
      password
    });
    return response.data; // { access_token, token_type, user }
  },

  register: async (customerData) => {
    const response = await apiClient.post('/auth/register', {
      name: customerData.name,
      phone_number: customerData.phone_number,
      password: customerData.password,
      email: customerData.email || null,
      preferred_language: customerData.preferred_language || 'HI',
      pincode: customerData.pincode,
      district: customerData.district,
      village: customerData.village
    });
    return response.data;
  },

  getMe: async () => {
    const response = await apiClient.get('/auth/me');
    return response.data;
  }
};
