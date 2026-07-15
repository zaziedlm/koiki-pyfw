import { cookieApiClient } from '@/shared/api';
import type { UserCreate, UserListParams, UserResponse, UserUpdate } from '@/types';

export const cookieUserApi = {
  getMe: () => cookieApiClient.requestJson<UserResponse>('/users/me'),

  updateMe: async (data: UserUpdate) => {
    if (!cookieApiClient.csrfToken) {
      await cookieApiClient.initializeCSRFToken();
    }

    return cookieApiClient.requestJson<UserResponse>('/users/me', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  getAll: (params?: UserListParams) => {
    const queryString = params ? `?${new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)])).toString()}` : '';
    return cookieApiClient.requestJson<UserResponse[]>(`/users${queryString}`);
  },

  getById: (id: number) => cookieApiClient.requestJson<UserResponse>(`/users/${id}`),

  create: async (data: UserCreate) => {
    if (!cookieApiClient.csrfToken) {
      await cookieApiClient.initializeCSRFToken();
    }

    return cookieApiClient.requestJson<UserResponse>('/users', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  update: async (id: number, data: UserUpdate) => {
    if (!cookieApiClient.csrfToken) {
      await cookieApiClient.initializeCSRFToken();
    }

    return cookieApiClient.requestJson<UserResponse>(`/users/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  delete: async (id: number) => {
    if (!cookieApiClient.csrfToken) {
      await cookieApiClient.initializeCSRFToken();
    }

    return cookieApiClient.requestJson<UserResponse>(`/users/${id}`, {
      method: 'DELETE',
    });
  },
};
