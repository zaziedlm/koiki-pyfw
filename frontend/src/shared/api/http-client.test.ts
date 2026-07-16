import { describe, expect, it } from 'vitest';
import { http, HttpResponse } from 'msw';

import { ApiError, CookieApiClient } from './http-client';
import { API_BASE_URL, server } from '@/test/server';

describe('CookieApiClient', () => {
  it('normalizes API error payloads', async () => {
    server.use(
      http.get(`${API_BASE_URL}/fails`, () => {
        return HttpResponse.json(
          { detail: { code: 'TASK_NOT_FOUND', message: 'Task was not found' } },
          { status: 404 }
        );
      })
    );

    const client = new CookieApiClient();

    await expect(client.requestJson('/fails')).rejects.toMatchObject({
      name: 'ApiError',
      status: 404,
      code: 'TASK_NOT_FOUND',
      message: 'Task was not found',
    });
  });

  it('refreshes CSRF token and retries once on CSRF invalid responses', async () => {
    const seenTokens: Array<string | null> = [];

    server.use(
      http.get(`${API_BASE_URL}/auth/session/csrf`, () => {
        return HttpResponse.json({ csrf_token: 'fresh-token' });
      }),
      http.post(`${API_BASE_URL}/todos`, ({ request }) => {
        seenTokens.push(request.headers.get('x-csrf-token'));

        if (seenTokens.length === 1) {
          return HttpResponse.json(
            { detail: { code: 'CSRF_TOKEN_INVALID', message: 'Invalid CSRF token' } },
            { status: 403 }
          );
        }

        return HttpResponse.json({ id: 1, title: 'Retried task' }, { status: 201 });
      })
    );

    const client = new CookieApiClient();
    await client.initializeCSRFToken();
    client.csrfToken = 'stale-token';

    const response = await client.fetchWithCredentials('/todos', {
      method: 'POST',
      body: JSON.stringify({ title: 'Retried task' }),
    });

    expect(response.status).toBe(201);
    expect(seenTokens).toEqual(['stale-token', 'fresh-token']);
  });

  it('coalesces concurrent CSRF initialization requests', async () => {
    let csrfRequests = 0;

    server.use(
      http.get(`${API_BASE_URL}/auth/session/csrf`, async () => {
        csrfRequests += 1;
        await new Promise((resolve) => setTimeout(resolve, 10));
        return HttpResponse.json({ csrf_token: 'coalesced-token' });
      })
    );

    const client = new CookieApiClient();

    await Promise.all([
      client.initializeCSRFToken(),
      client.initializeCSRFToken(),
    ]);

    expect(csrfRequests).toBe(1);
    expect(client.csrfToken).toBe('coalesced-token');
  });
});

describe('ApiError', () => {
  it('supports instanceof checks', () => {
    const error = new ApiError({ status: 500, message: 'Server error' });

    expect(error).toBeInstanceOf(Error);
    expect(error).toBeInstanceOf(ApiError);
  });
});
