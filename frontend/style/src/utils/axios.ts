/**
 * Centralized Axios instance with auth header injection and refresh flow.
 * Works with axios v0.27+ and v1.x without importing type-only members.
 */
import axios from 'axios';
import { useAuthStore } from '@/stores/auth';

const baseURL = (import.meta.env.VITE_API_URL as string).replace(/\/$/, '');

const axiosServices = axios.create({
  baseURL,
  withCredentials: false, // set true only if you switch to cookie-only mode
});

// Inject Authorization header from Pinia store
axiosServices.interceptors.request.use((config: any) => {
  const auth = useAuthStore();
  const access = auth.user?.access || auth.user?.token || null;
  if (access) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${access}`;
  }
  return config;
});

// 401-refresh queue (avoid multiple parallel refreshes)
let isRefreshing = false;
let requestQueue: Array<(token: string | null) => void> = [];

function enqueue(cb: (token: string | null) => void) {
  requestQueue.push(cb);
}
function flushQueue(token: string | null) {
  requestQueue.forEach((cb) => cb(token));
  requestQueue = [];
}

axiosServices.interceptors.response.use(
  (response) => response,
  async (error: any) => {
    const auth = useAuthStore();
    const originalRequest: any = error.config || {};
    const status = error?.response?.status;

    if (status !== 401 || originalRequest._retry) {
      return Promise.reject((error.response && error.response.data) || error);
    }

    originalRequest._retry = true;

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        enqueue((newToken) => {
          if (!newToken) return reject(error);
          originalRequest.headers = originalRequest.headers || {};
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          resolve(axiosServices(originalRequest));
        });
      });
    }

    isRefreshing = true;
    try {
      const newToken = await auth.tryRefresh();
      isRefreshing = false;
      flushQueue(newToken);

      if (!newToken) {
        await auth.logout();
        return Promise.reject((error.response && error.response.data) || error);
      }

      originalRequest.headers = originalRequest.headers || {};
      originalRequest.headers.Authorization = `Bearer ${newToken}`;
      return axiosServices(originalRequest);
    } catch (e) {
      isRefreshing = false;
      flushQueue(null);
      await auth.logout();
      return Promise.reject(e);
    }
  }
);

export default axiosServices;
