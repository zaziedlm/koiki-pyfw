import { cookieApiClient } from '@/shared/api';

export const cookieUserApi = {
  getMe: () => cookieApiClient.get('/users/me'),

  updateMe: (data: {
    username?: string;
    email?: string;
    full_name?: string;
    is_active?: boolean;
  }) => cookieApiClient.put('/users/me', data),

  getAll: (params?: { skip?: number; limit?: number }) => {
    const queryString = params ? `?${new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)])).toString()}` : '';
    return cookieApiClient.get(`/users${queryString}`);
  },

  getById: (id: number) => cookieApiClient.get(`/users/${id}`),

  create: (data: {
    username: string;
    email: string;
    password: string;
    full_name?: string;
    is_active?: boolean;
  }) => cookieApiClient.post('/users', data),

  update: (id: number, data: {
    username?: string;
    email?: string;
    full_name?: string;
    is_active?: boolean;
    password?: string;
  }) => cookieApiClient.put(`/users/${id}`, data),

  delete: (id: number) => cookieApiClient.delete(`/users/${id}`),
};
