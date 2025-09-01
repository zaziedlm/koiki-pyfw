import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosHeaders } from 'axios';
import { config as appConfig } from './config';
import { isTokenExpired } from './token-utils';

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
    localStorage.removeItem(appConfig.auth.tokenKey);
    localStorage.removeItem(appConfig.auth.refreshTokenKey);
  },
};

// =========================================================
// BFF client (same-origin /api/*). Sends cookies and CSRF.
// =========================================================
const CSRF_COOKIE_NAME = 'koiki_csrf_token';
const CSRF_HEADER_NAME = 'x-csrf-token';

function readCookie(name: string): string | null {
  if (typeof document === 'undefined') return null;
  const match = document.cookie.match(new RegExp('(?:^|; )' + name.replace(/([.$?*|{}()\[\]\\/+^])/g, '\\$1') + '=([^;]*)'));
  return match ? decodeURIComponent(match[1]) : null;
}

const bffClient = axios.create({
  baseURL: '/',
  timeout: 10000,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach CSRF token for state-changing requests
bffClient.interceptors.request.use((cfg) => {
  const method = (cfg.method || 'get').toUpperCase();
  if (method !== 'GET' && method !== 'HEAD' && method !== 'OPTIONS') {
    const token = readCookie(CSRF_COOKIE_NAME);
    if (token) {
      const headers = AxiosHeaders.from(cfg.headers ?? {});
      headers.set(CSRF_HEADER_NAME, token);
      cfg.headers = headers;
    }
  }
  return cfg;
});

// Create axios instance
const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: appConfig.api.baseUrl,
    timeout: 10000,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Request interceptor to add auth token and check expiration
  client.interceptors.request.use(
    async (config) => {
      const token = tokenStorage.get('koiki_access_token');

      if (token) {
        // トークンの有効期限をチェック（60秒の猶予時間）
        if (isTokenExpired(token, 60)) {
          // トークンが期限切れの場合、リフレッシュを試みる
          const refreshToken = tokenStorage.get('koiki_refresh_token');
          if (refreshToken) {
            try {
              const response = await axios.post(
                `${appConfig.api.baseUrl}/auth/refresh`,
                { refresh_token: refreshToken }
              );

              const { access_token, refresh_token: newRefreshToken } = response.data;
              tokenStorage.set('koiki_access_token', access_token);
              tokenStorage.set('koiki_refresh_token', newRefreshToken);

              // 新しいトークンを使用
              config.headers.Authorization = `Bearer ${access_token}`;
            } catch {
              // リフレッシュに失敗した場合、トークンをクリア
              tokenStorage.clear();
              if (typeof window !== 'undefined') {
                window.location.href = '/auth/login';
              }
              return Promise.reject(new Error('Token refresh failed'));
            }
          } else {
            // リフレッシュトークンがない場合、ログインページにリダイレクト
            tokenStorage.clear();
            if (typeof window !== 'undefined') {
              window.location.href = '/auth/login';
            }
            return Promise.reject(new Error('No refresh token available'));
          }
        } else {
          // トークンが有効な場合、そのまま使用
          config.headers.Authorization = `Bearer ${token}`;
        }
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
              `${appConfig.api.baseUrl}/auth/refresh`,
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
export interface ApiResponse<T = unknown> {
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
  get: <T = unknown>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> =>
    apiClient.get<T>(url, config),

  post: <T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> =>
    apiClient.post<T>(url, data, config),

  put: <T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> =>
    apiClient.put<T>(url, data, config),

  patch: <T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> =>
    apiClient.patch<T>(url, data, config),

  delete: <T = unknown>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> =>
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
    bffClient.get('/api/todos', { params }),

  getById: (id: number) => bffClient.get(`/api/todos/${id}`),

  create: (data: { title: string; description?: string }) =>
    bffClient.post('/api/todos', data),

  update: (id: number, data: { title?: string; description?: string; is_completed?: boolean }) =>
    bffClient.put(`/api/todos/${id}`, data),

  delete: (id: number) => bffClient.delete(`/api/todos/${id}`),
};

// User API methods (BFF経由)
export const userApi = {
  getMe: () => bffClient.get('/api/users/me'),

  updateMe: (data: {
    username?: string;
    email?: string;
    full_name?: string;
    is_active?: boolean;
  }) => bffClient.put('/api/users/me', data),

  getAll: (params?: { skip?: number; limit?: number }) =>
    bffClient.get('/api/users', { params }),

  getById: (id: number) => bffClient.get(`/api/users/${id}`),

  create: (data: {
    username: string;
    email: string;
    password: string;
    full_name?: string;
    is_active?: boolean;
  }) => bffClient.post('/api/users', data),

  update: (id: number, data: {
    username?: string;
    email?: string;
    full_name?: string;
    is_active?: boolean;
    password?: string;
  }) => bffClient.put(`/api/users/${id}`, data),

  delete: (id: number) => bffClient.delete(`/api/users/${id}`),
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
  baseURL: appConfig.api.url, // http://localhost:8000 (without /api/v1)
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const healthApi = {
  check: () => directClient.get('/health'),
  root: () => directClient.get('/'),
};