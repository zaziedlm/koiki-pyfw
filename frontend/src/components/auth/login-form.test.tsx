import { beforeEach, describe, expect, it } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { Route, Routes } from 'react-router';

import { LoginForm } from './login-form';
import { cookieApiClient } from '@/shared/api';
import { useUIStore } from '@/stores';
import { API_BASE_URL, server } from '@/test/server';
import { renderWithProviders } from '@/test/render';

function renderLoginForm() {
  return renderWithProviders(
    <Routes>
      <Route path="/auth/login" element={<LoginForm />} />
      <Route path="/dashboard" element={<div>Dashboard Home</div>} />
    </Routes>,
    { router: { initialEntries: ['/auth/login'] } }
  );
}

describe('LoginForm', () => {
  beforeEach(() => {
    useUIStore.getState().clearNotifications();
    cookieApiClient.csrfToken = 'test-csrf-token';
  });

  it('shows a validation error and does not submit when the email is invalid', async () => {
    const user = userEvent.setup();
    renderLoginForm();

    // "user@localhost" satisfies the browser's native type="email" constraint
    // (which would otherwise block the submit event before React ever sees it)
    // but still fails the app's stricter Zod email format, so this exercises
    // the app's own validation message rather than a native browser tooltip.
    await user.type(screen.getByLabelText('Email'), 'user@localhost');
    await user.type(screen.getByLabelText('Password'), 'secret123');
    await user.click(screen.getByRole('button', { name: 'Sign In' }));

    expect(await screen.findByText('Please enter a valid email address')).toBeInTheDocument();
    expect(useUIStore.getState().notifications).toHaveLength(0);
  });

  it('navigates to the returned location and records a success notification on login', async () => {
    server.use(
      http.post(`${API_BASE_URL}/auth/session/login`, () => {
        return HttpResponse.json({ message: 'ok', location: '/dashboard' });
      })
    );

    const user = userEvent.setup();
    renderLoginForm();

    await user.type(screen.getByLabelText('Email'), 'user@example.com');
    await user.type(screen.getByLabelText('Password'), 'secret123');
    await user.click(screen.getByRole('button', { name: 'Sign In' }));

    expect(await screen.findByText('Dashboard Home')).toBeInTheDocument();
    expect(useUIStore.getState().notifications[0]).toMatchObject({ type: 'success' });
  });

  it('stays on the form and records an error notification when login fails', async () => {
    server.use(
      http.post(`${API_BASE_URL}/auth/session/login`, () => {
        return HttpResponse.json({ detail: 'Invalid credentials' }, { status: 401 });
      })
    );

    const user = userEvent.setup();
    renderLoginForm();

    await user.type(screen.getByLabelText('Email'), 'user@example.com');
    await user.type(screen.getByLabelText('Password'), 'wrong-password');
    await user.click(screen.getByRole('button', { name: 'Sign In' }));

    await waitFor(() => {
      expect(useUIStore.getState().notifications[0]).toMatchObject({ type: 'error' });
    });
    expect(screen.getByRole('button', { name: 'Sign In' })).toBeInTheDocument();
  });
});
