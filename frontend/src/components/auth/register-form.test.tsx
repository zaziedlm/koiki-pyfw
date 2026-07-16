import { beforeEach, describe, expect, it } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { Route, Routes } from 'react-router';

import { RegisterForm } from './register-form';
import { cookieApiClient } from '@/shared/api';
import { useUIStore } from '@/stores';
import { API_BASE_URL, server } from '@/test/server';
import { renderWithProviders } from '@/test/render';

function renderRegisterForm() {
  return renderWithProviders(
    <Routes>
      <Route path="/auth/register" element={<RegisterForm />} />
      <Route path="/dashboard" element={<div>Dashboard Home</div>} />
    </Routes>,
    { router: { initialEntries: ['/auth/register'] } }
  );
}

async function fillValidForm(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByLabelText('Username'), 'newuser');
  await user.type(screen.getByLabelText('Email'), 'newuser@example.com');
  await user.type(screen.getByLabelText('Password'), 'Secret123');
  await user.type(screen.getByLabelText('Confirm Password'), 'Secret123');
}

describe('RegisterForm', () => {
  beforeEach(() => {
    useUIStore.getState().clearNotifications();
    cookieApiClient.csrfToken = 'test-csrf-token';
  });

  it('shows a validation error and does not submit when the passwords do not match', async () => {
    const user = userEvent.setup();
    renderRegisterForm();

    await user.type(screen.getByLabelText('Username'), 'newuser');
    await user.type(screen.getByLabelText('Email'), 'newuser@example.com');
    await user.type(screen.getByLabelText('Password'), 'Secret123');
    await user.type(screen.getByLabelText('Confirm Password'), 'Different123');
    await user.click(screen.getByRole('button', { name: 'Create Account' }));

    expect(await screen.findByText("Passwords don't match")).toBeInTheDocument();
    expect(useUIStore.getState().notifications).toHaveLength(0);
  });

  it('navigates to the dashboard and records a success notification on registration', async () => {
    let receivedBody: unknown;

    server.use(
      http.post(`${API_BASE_URL}/auth/session/register`, async ({ request }) => {
        receivedBody = await request.json();
        return HttpResponse.json({ message: 'ok' });
      })
    );

    const user = userEvent.setup();
    renderRegisterForm();

    await fillValidForm(user);
    await user.click(screen.getByRole('button', { name: 'Create Account' }));

    expect(await screen.findByText('Dashboard Home')).toBeInTheDocument();
    expect(useUIStore.getState().notifications[0]).toMatchObject({ type: 'success' });
    expect(receivedBody).toMatchObject({
      username: 'newuser',
      email: 'newuser@example.com',
      password: 'Secret123',
    });
  });

  it('stays on the form and records an error notification when registration fails', async () => {
    server.use(
      http.post(`${API_BASE_URL}/auth/session/register`, () => {
        return HttpResponse.json({ detail: 'Email already registered' }, { status: 409 });
      })
    );

    const user = userEvent.setup();
    renderRegisterForm();

    await fillValidForm(user);
    await user.click(screen.getByRole('button', { name: 'Create Account' }));

    await waitFor(() => {
      expect(useUIStore.getState().notifications[0]).toMatchObject({ type: 'error' });
    });
    expect(screen.getByRole('button', { name: 'Create Account' })).toBeInTheDocument();
  });
});
