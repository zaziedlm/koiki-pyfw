import { describe, expect, it } from 'vitest';
import { act, waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';

import { cookieApiClient } from '@/shared/api';
import { API_BASE_URL, server } from '@/test/server';
import { renderHookWithProviders } from '@/test/render';
import { useCookieCreateTodo, useCookieUpdateTodo } from './queries';

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
            version: 1,
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

  it('sends the current version when updating a todo (optimistic lock)', async () => {
    let receivedBody: unknown;

    server.use(
      http.put(`${API_BASE_URL}/todos/42`, async ({ request }) => {
        receivedBody = await request.json();

        return HttpResponse.json({
          id: 42,
          title: 'Updated title',
          description: null,
          is_completed: true,
          owner_id: 10,
          version: 2,
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:01:00Z',
        });
      })
    );

    cookieApiClient.csrfToken = 'test-csrf-token';

    const { result } = renderHookWithProviders(() => useCookieUpdateTodo());

    let updatedVersion: number | undefined;
    await act(async () => {
      const updated = await result.current.mutateAsync({
        id: 42,
        data: { title: 'Updated title', is_completed: true, version: 1 },
      });
      updatedVersion = updated.version;
    });

    expect(receivedBody).toEqual({ title: 'Updated title', is_completed: true, version: 1 });
    expect(updatedVersion).toBe(2);
  });

  it('rejects with a 409 conflict when the version is stale', async () => {
    server.use(
      http.put(`${API_BASE_URL}/todos/42`, () => {
        return HttpResponse.json(
          { detail: 'ToDo was updated by another request. Please reload and try again.' },
          { status: 409 }
        );
      })
    );

    cookieApiClient.csrfToken = 'test-csrf-token';

    const { result } = renderHookWithProviders(() => useCookieUpdateTodo());

    await expect(
      act(async () => {
        await result.current.mutateAsync({
          id: 42,
          data: { title: 'Stale update', version: 1 },
        });
      })
    ).rejects.toMatchObject({ status: 409 });
  });
});
