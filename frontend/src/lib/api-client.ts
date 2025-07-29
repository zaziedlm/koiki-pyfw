import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { config } from './config';

// Token storage utilities
export const tokenStorage = {
  get: (key: string): string | null => {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(key);
  },
  set: (key: string, value: string): void => {
    if (typeof window === 'undefined') return;
    localStorage.setItem(key, value);
  },
  remove: (key: string): void => {
    if (typeof window === 'undefined') return;
    localStorage.removeItem(key);
  },
  clear: (): void => {
    if (typeof window === 'undefined') return;
    localStorage.removeItem(config.auth.tokenKey);
    localStorage.removeItem(config.auth.refreshTokenKey);
  },
};

// Create axios instance
const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: config.api.baseUrl,
    timeout: 10000,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Request interceptor to add auth token
  client.interceptors.request.use(
    (config) => {
      const token = tokenStorage.get('koiki_access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // Response interceptor to handle token refresh
  client.interceptors.response.use(
    (response) => response,
    async (error) => {
      const originalRequest = error.config;

      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true;

        try {
          const refreshToken = tokenStorage.get('koiki_refresh_token');
          if (refreshToken) {
            const response = await axios.post(
              `${config.api.baseUrl}/auth/refresh`,
              { refresh_token: refreshToken }
            );

            const { access_token, refresh_token: newRefreshToken } = response.data;
            tokenStorage.set('koiki_access_token', access_token);
            tokenStorage.set('koiki_refresh_token', newRefreshToken);

            // Retry original request with new token
            originalRequest.headers.Authorization = `Bearer ${access_token}`;
            return client(originalRequest);
          }
        } catch (refreshError) {
          // Refresh failed, clear tokens and redirect to login
          tokenStorage.clear();
          if (typeof window !== 'undefined') {
            window.location.href = '/auth/login';
          }
          return Promise.reject(refreshError);
        }
      }

      return Promise.reject(error);
    }
  );

  return client;
};

// Create singleton instance
export const apiClient = createApiClient();

// API response types
export interface ApiResponse<T = any> {
  data: T;
  message?: string;
}

export interface ApiError {
  message: string;
  detail?: string;
  statusCode?: number;
}

// Generic API methods
export const api = {
  get: <T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> =>
    apiClient.get<T>(url, config),

  post: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> =>
    apiClient.post<T>(url, data, config),

  put: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> =>
    apiClient.put<T>(url, data, config),

  patch: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> =>
    apiClient.patch<T>(url, data, config),

  delete: <T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> =>
    apiClient.delete<T>(url, config),
};

// Auth API methods
export const authApi = {
  login: (credentials: { username: string; password: string }) => {
    const formData = `username=${encodeURIComponent(credentials.username)}&password=${encodeURIComponent(credentials.password)}`;
    
    return apiClient.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
  },

  register: (userData: {
    username: string;
    email: string;
    password: string;
    full_name?: string;
  }) => apiClient.post('/auth/register', userData),

  logout: () => apiClient.post('/auth/logout'),

  getMe: () => apiClient.get('/auth/me'),

  refreshToken: (refreshToken: string) => 
    apiClient.post('/auth/refresh', { refresh_token: refreshToken }),

  changePassword: (data: { current_password: string; new_password: string }) =>
    apiClient.post('/auth/password-change', data),

  requestPasswordReset: (email: string) =>
    apiClient.post('/auth/password-reset/request', { email }),

  confirmPasswordReset: (data: { token: string; new_password: string }) =>
    apiClient.post('/auth/password-reset/confirm', data),

  revokeAllTokens: () => apiClient.post('/auth/revoke-all-tokens'),
};

// Todo API methods
export const todoApi = {
  getAll: (params?: { skip?: number; limit?: number }) =>
    apiClient.get('/todos/', { params }),

  getById: (id: number) => apiClient.get(`/todos/${id}`),

  create: (data: { title: string; description?: string }) =>
    apiClient.post('/todos/', data),

  update: (id: number, data: { title?: string; description?: string; is_completed?: boolean }) =>
    apiClient.put(`/todos/${id}`, data),

  delete: (id: number) => apiClient.delete(`/todos/${id}`),
};

// User API methods
export const userApi = {
  getMe: () => apiClient.get('/users/me'),

  updateMe: (data: {
    username?: string;
    email?: string;
    full_name?: string;
    is_active?: boolean;
  }) => apiClient.put('/users/me', data),

  getAll: (params?: { skip?: number; limit?: number }) =>
    apiClient.get('/users/', { params }),

  getById: (id: number) => apiClient.get(`/users/${id}`),

  create: (data: {
    username: string;
    email: string;
    password: string;
    full_name?: string;
    is_active?: boolean;
  }) => apiClient.post('/users/', data),

  update: (id: number, data: {
    username?: string;
    email?: string;
    full_name?: string;
    is_active?: boolean;
    password?: string;
  }) => apiClient.put(`/users/${id}`, data),

  delete: (id: number) => apiClient.delete(`/users/${id}`),
};

// Security API methods
export const securityApi = {
  getMetrics: () => apiClient.get('/security/metrics'),
  getAuthMetrics: () => apiClient.get('/security/metrics/authentication'),
  getSummary: () => apiClient.get('/security/metrics/summary'),
  resetMetrics: () => apiClient.post('/security/metrics/reset'),
  getHealth: () => apiClient.get('/security/health'),
};

// Health check API (direct access, not through API v1)
const directClient = axios.create({
  baseURL: config.api.url, // http://localhost:8000 (without /api/v1)
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const healthApi = {
  check: () => directClient.get('/health'),
  root: () => directClient.get('/'),
};