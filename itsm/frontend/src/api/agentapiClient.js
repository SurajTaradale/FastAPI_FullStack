import axios from 'axios';
import Cookies from 'js-cookie';

const agentapiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8001',
});

// Attach agent token to every request
agentapiClient.interceptors.request.use((config) => {
  const token = Cookies.get('agent_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auto-logout on 401
agentapiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      Cookies.remove('agent_token');
      window.location.href = '/agent/login';
    }
    return Promise.reject(error);
  }
);

export default agentapiClient;
