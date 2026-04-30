import agentapiClient from '../api/agentapiClient';
import customerapiClient from '../api/customerapiClient';
import Cookies from 'js-cookie';

const COOKIE_OPTS = { expires: 1, secure: false, sameSite: 'Strict' };

export const agentLoginApi = async (username, password) => {
  try {
    const response = await agentapiClient.post(
      '/auth/token',
      new URLSearchParams({ username, password }),
      { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
    );
    const { access_token } = response.data;
    Cookies.set('agent_token', access_token, COOKIE_OPTS);
    return response.data;
  } catch (error) {
    const detail = error.response?.data?.detail || error.response?.data?.message || error.message;
    throw new Error('Login failed: ' + detail);
  }
};

export const agentLogoutApi = () => {
  Cookies.remove('agent_token');
};

export const customerLoginApi = async (username, password) => {
  try {
    // FIX: use customerapiClient (not agentapiClient) so the customer token is attached
    const response = await customerapiClient.post(
      '/auth/customer/login',
      new URLSearchParams({ username, password }),
      { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
    );
    const { access_token } = response.data;
    Cookies.set('customeruser_token', access_token, COOKIE_OPTS);
    return response.data;
  } catch (error) {
    const detail = error.response?.data?.detail || error.response?.data?.message || error.message;
    throw new Error('Login failed: ' + detail);
  }
};

export const customerLogoutApi = () => {
  Cookies.remove('customeruser_token');
};
