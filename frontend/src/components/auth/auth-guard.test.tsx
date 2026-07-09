import { describe, expect, it } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';

import { AuthGuard } from './auth-guard';
import { API_BASE_URL, server } from '@/test/server';
import { renderWithProviders } from '@/test/render';

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

describe('AuthGuard', () => {
  it('renders children when cookie auth resolves to a user', async () => {
    server.use(
      http.get(`${API_BASE_URL}/auth/session/me`, () => {
        return HttpResponse.json(testUser);
      })
    );

    renderWithProviders(
      <AuthGuard>
        <div>Protected content</div>
      </AuthGuard>,
      { router: { initialEntries: ['/dashboard'] } }
    );

    expect(await screen.findByText('Protected content')).toBeInTheDocument();
  });

  it('shows the redirecting state when authentication is required but absent', async () => {
    server.use(
      http.get(`${API_BASE_URL}/auth/session/me`, () => {
        return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 });
      })
    );

    renderWithProviders(
      <AuthGuard>
        <div>Protected content</div>
      </AuthGuard>,
      { router: { initialEntries: ['/dashboard'] } }
    );

    await waitFor(() => {
      expect(screen.getByText('Redirecting to login...')).toBeInTheDocument();
    });
    expect(screen.queryByText('Protected content')).not.toBeInTheDocument();
  });
});
