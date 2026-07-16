import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';

const API_BASE_URL = 'http://localhost:8000/api/v1';

export const server = setupServer(
  http.get(`${API_BASE_URL}/auth/session/csrf`, () => {
    return HttpResponse.json({ csrf_token: 'test-csrf-token' });
  })
);

export { API_BASE_URL };
