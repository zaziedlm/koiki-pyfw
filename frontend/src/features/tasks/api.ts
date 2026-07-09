import { cookieApiClient } from '@/shared/api';
import type { TodoCreate, TodoResponse, TodoUpdate } from '@/types';

export const cookieTodoApi = {
  getAll: (params?: { skip?: number; limit?: number }) => {
    const queryString = params ? `?${new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)])).toString()}` : '';
    return cookieApiClient.requestJson<TodoResponse[]>(`/todos${queryString}`, {
      method: 'GET',
    });
  },

  getById: (id: number) => cookieApiClient.requestJson<TodoResponse>(`/todos/${id}`, {
    method: 'GET',
  }),

  create: async (data: TodoCreate) => {
    if (!cookieApiClient.csrfToken) {
      await cookieApiClient.initializeCSRFToken();
    }

    return cookieApiClient.requestJson<TodoResponse>('/todos', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  update: async (id: number, data: TodoUpdate) => {
    if (!cookieApiClient.csrfToken) {
      await cookieApiClient.initializeCSRFToken();
    }

    return cookieApiClient.requestJson<TodoResponse>(`/todos/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  delete: async (id: number) => {
    if (!cookieApiClient.csrfToken) {
      await cookieApiClient.initializeCSRFToken();
    }

    return cookieApiClient.requestJson<null>(`/todos/${id}`, {
      method: 'DELETE',
    });
  },
};
