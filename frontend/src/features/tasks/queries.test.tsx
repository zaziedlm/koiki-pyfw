import { describe, expect, it } from 'vitest';
import { act, waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';

import { cookieApiClient } from '@/shared/api';
import { API_BASE_URL, server } from '@/test/server';
import { renderHookWithProviders } from '@/test/render';
import { useCookieCreateTodo } from './queries';

describe('task queries', () => {
  it('creates a todo through the cookie task API and invalidates list queries', async () => {
    let receivedBody: unknown;

    server.use(
      http.post(`${API_BASE_URL}/todos`, async ({ request }) => {
        receivedBody = await request.json();

        return HttpResponse.json(
          {
            id: 42,
            title: 'Write tests',
            description: null,
            is_completed: false,
            owner_id: 10,
            created_at: '2026-01-01T00:00:00Z',
            updated_at: '2026-01-01T00:00:00Z',
          },
          { status: 201 }
        );
      })
    );

    cookieApiClient.csrfToken = 'test-csrf-token';

    const { result, queryClient } = renderHookWithProviders(() => useCookieCreateTodo());

    let createdId: number | undefined;
    await act(async () => {
      const created = await result.current.mutateAsync({ title: 'Write tests' });
      createdId = created.id;
    });

    expect(createdId).toBe(42);
    expect(receivedBody).toEqual({ title: 'Write tests' });

    await waitFor(() => {
      expect(queryClient.isFetching()).toBe(0);
    });
  });
});
