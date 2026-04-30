import axios from 'axios';
import Cookies from 'js-cookie';

const customerapiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8001',
});

// Attach customer token to every request
customerapiClient.interceptors.request.use((config) => {
  const token = Cookies.get('customeruser_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auto-logout on 401
customerapiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      Cookies.remove('customeruser_token');
      window.location.href = '/customer/login';
    }
    return Promise.reject(error);
  }
);

export default customerapiClient;
