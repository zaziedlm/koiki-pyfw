import { describe, expect, it } from 'vitest';
import { act, waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';

import { cookieApiClient } from '@/shared/api';
import { API_BASE_URL, server } from '@/test/server';
import { renderHookWithProviders } from '@/test/render';
import { cookieAuthKeys, useCookieLogin, useCookieLogout, useCookieMe, useCookieRegister } from './queries';

const testUser = {
  id: 10,
  username: 'security',
  email: 'security@example.com',
  full_name: 'Security User',
  is_active: true,
  is_superuser: false,
  roles: [{ id: 1, name: 'user', description: 'User' }],
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
};

describe('auth queries', () => {
  it('logs in, sends the CSRF header, and updates the cached session user', async () => {
    let receivedCsrfHeader: string | null = null;

    server.use(
      http.post(`${API_BASE_URL}/auth/session/login`, async ({ request }) => {
        receivedCsrfHeader = request.headers.get('x-csrf-token');
        return HttpResponse.json({ message: 'ok', user: testUser, location: '/dashboard' });
      }),
      http.get(`${API_BASE_URL}/auth/session/me`, () => HttpResponse.json(testUser))
    );

    cookieApiClient.csrfToken = 'test-csrf-token';

    // Keep useCookieMe() mounted as an active observer so the cache entry
    // survives gcTime: 0 in the test QueryClient (see createTestQueryClient).
    const { result } = renderHookWithProviders(() => ({
      me: useCookieMe(),
      login: useCookieLogin(),
    }));

    await act(async () => {
      await result.current.login.mutateAsync({ email: testUser.email, password: 'secret123' });
    });

    expect(receivedCsrfHeader).toBe('test-csrf-token');
    await waitFor(() => {
      expect(result.current.me.data).toEqual(testUser);
    });
  });

  it('rejects with the normalized ApiError when login fails', async () => {
    server.use(
      http.post(`${API_BASE_URL}/auth/session/login`, () => {
        return HttpResponse.json({ detail: 'Invalid credentials' }, { status: 401 });
      })
    );

    cookieApiClient.csrfToken = 'test-csrf-token';

    const { result } = renderHookWithProviders(() => useCookieLogin());

    await expect(
      act(async () => {
        await result.current.mutateAsync({ email: testUser.email, password: 'wrong' });
      })
    ).rejects.toMatchObject({ status: 401 });
  });

  it('registers a new user and updates the cached session user', async () => {
    let receivedBody: unknown;

    server.use(
      http.post(`${API_BASE_URL}/auth/session/register`, async ({ request }) => {
        receivedBody = await request.json();
        return HttpResponse.json({ message: 'ok', user: testUser });
      }),
      http.get(`${API_BASE_URL}/auth/session/me`, () => HttpResponse.json(testUser))
    );

    cookieApiClient.csrfToken = 'test-csrf-token';

    const { result } = renderHookWithProviders(() => ({
      me: useCookieMe(),
      register: useCookieRegister(),
    }));

    await act(async () => {
      await result.current.register.mutateAsync({
        username: testUser.username,
        email: testUser.email,
        password: 'Secret123',
      });
    });

    expect(receivedBody).toEqual({
      username: testUser.username,
      email: testUser.email,
      password: 'Secret123',
    });
    await waitFor(() => {
      expect(result.current.me.data).toEqual(testUser);
    });
  });

  it('clears cached auth state on logout', async () => {
    server.use(
      http.post(`${API_BASE_URL}/auth/session/logout`, () => {
        return HttpResponse.json({ message: 'ok' });
      })
    );

    const { result, queryClient } = renderHookWithProviders(() => useCookieLogout());

    queryClient.setQueryData(cookieAuthKeys.me(), testUser);
    expect(queryClient.getQueryData(cookieAuthKeys.me())).toEqual(testUser);

    await act(async () => {
      await result.current.mutateAsync();
    });

    await waitFor(() => {
      expect(queryClient.getQueryData(cookieAuthKeys.me())).toBeUndefined();
    });
  });
});
