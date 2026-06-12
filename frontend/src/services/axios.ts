import axios from "axios"
import type { AxiosError} from "axios"

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000"

axios.defaults.xsrfCookieName = 'csrftoken';
axios.defaults.xsrfHeaderName = 'X-CSRFToken';

// Public client
export const publicApi = axios.create({
  baseURL: BASE_URL,
   withCredentials: true, 
})

// Private client
export const privateApi = axios.create({
  baseURL: BASE_URL,
  withCredentials: true,
})

privateApi.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as any;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        await axios.post(`${BASE_URL}/auth/refresh/`, {}, { withCredentials: true });
        
        return privateApi(originalRequest);
      } catch (refreshError) {
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  }
);
