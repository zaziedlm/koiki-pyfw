import { cookieApiClient } from '@/shared/api';
import type { RegisterData, UserResponse } from '@/types';

export interface AuthSessionResponse {
  message?: string;
  data?: Record<string, unknown>;
  user?: UserResponse;
  location?: string;
}

export const cookieAuthApi = {
  getMe: () => cookieApiClient.requestJson<UserResponse>('/auth/session/me'),

  login: async (credentials: { email: string; password: string }) => {
    if (!cookieApiClient.csrfToken) {
      await cookieApiClient.initializeCSRFToken();
    }

    return cookieApiClient.requestJson<AuthSessionResponse>('/auth/session/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  },

  logout: () => cookieApiClient.requestJson<unknown>('/auth/session/logout', {
    method: 'POST',
  }),

  register: async (userData: RegisterData) => {
    if (!cookieApiClient.csrfToken) {
      await cookieApiClient.initializeCSRFToken();
    }

    return cookieApiClient.requestJson<AuthSessionResponse>('/auth/session/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  },

  refreshToken: () => cookieApiClient.requestJson<unknown>('/auth/session/refresh', {
    method: 'POST',
  }),
};
