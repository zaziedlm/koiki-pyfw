'use client';

import { Suspense, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { cookieApiClient } from '@/lib/cookie-api-client';
import { clearSsoContext, loadSsoContext } from '@/lib/sso-storage';
import { Button } from '@/components/ui/button';

type Status = 'pending' | 'error';

function SsoCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [status, setStatus] = useState<Status>('pending');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    const code = searchParams.get('code');
    const state = searchParams.get('state');

    const finalize = async () => {
      if (!code) {
        throw new Error('Missing authorization code in callback');
      }
      if (!state) {
        throw new Error('Missing state value in callback');
      }

      const stored = loadSsoContext();
      if (!stored) {
        throw new Error('SSO login session has expired. Please retry.');
      }

      try {
        if (stored.state !== state) {
          throw new Error('State verification failed. Please retry.');
        }

        if (stored.expiresAt) {
          const expiresAt = new Date(stored.expiresAt).getTime();
          if (!Number.isNaN(expiresAt) && Date.now() > expiresAt) {
            throw new Error('Authorization state has expired. Please retry.');
          }
        }

        const response = await cookieApiClient.sso.login({
          authorization_code: code,
          code_verifier: stored.codeVerifier,
          state: stored.state,
          nonce: stored.nonce,
          redirect_uri: stored.redirectUri,
        });

        if (!response.ok) {
          const payload = await response.json().catch(() => null);
          const message = payload?.detail || payload?.message || 'Failed to complete SSO login';
          throw new Error(message);
        }

        const data = await response.json().catch(() => ({}));

        clearSsoContext();

        const target = data?.location || '/dashboard';
        window.location.href = target;
      } finally {
        clearSsoContext();
      }
    };

    finalize().catch((error: unknown) => {
      console.error('[SSO][callback] failed', error);
      const message = error instanceof Error ? error.message : 'SSO login failed. Please try again.';
      setErrorMessage(message);
      setStatus('error');
    });
  }, [router, searchParams]);

  if (status === 'pending') {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center space-y-4">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary" />
        <p className="text-sm text-muted-foreground">Completing SSO login...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center space-y-4 px-4 text-center">
      <h1 className="text-xl font-semibold">SSO Login Failed</h1>
      {errorMessage && <p className="text-sm text-muted-foreground max-w-md">{errorMessage}</p>}
      <div className="flex gap-2">
        <Button onClick={() => router.replace('/auth/login')}>Go to Login</Button>
        <Button variant="outline" onClick={() => router.replace('/')}>Return Home</Button>
      </div>
    </div>
  );
}

export default function SsoCallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex flex-col items-center justify-center space-y-4">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary" />
          <p className="text-sm text-muted-foreground">Preparing SSO callback...</p>
        </div>
      }
    >
      <SsoCallbackContent />
    </Suspense>
  );
}
