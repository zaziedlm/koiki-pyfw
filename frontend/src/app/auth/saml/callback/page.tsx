'use client';

import { Suspense, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { clearSamlContext, loadSamlContext } from '@/lib/saml-storage';
import { Button } from '@/components/ui/button';

type Status = 'pending' | 'error';

function SamlCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [status, setStatus] = useState<Status>('pending');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    const samlTicket = searchParams.get('saml_ticket');

    const finalize = async () => {
      if (!samlTicket) {
        throw new Error('Missing SAML login ticket in callback');
      }

      const stored = loadSamlContext();
      if (!stored) {
        throw new Error('SAML login session has expired. Please retry.');
      }

      try {
        if (stored.expiresAt) {
          const expiresAt = new Date(stored.expiresAt).getTime();
          if (!Number.isNaN(expiresAt) && Date.now() > expiresAt) {
            throw new Error('SAML authorization state has expired. Please retry.');
          }
        }

        // Exchange login ticket for auth tokens via Next.js API route
        const response = await fetch('/api/saml/login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          body: JSON.stringify({
            login_ticket: samlTicket,
          }),
        });

        if (!response.ok) {
          const payload = await response.json().catch(() => null);
          const message = payload?.detail || payload?.message || 'Failed to complete SAML login';
          throw new Error(message);
        }

        const data = await response.json().catch(() => ({}));

        clearSamlContext();

        const target = data?.location || '/dashboard';
        window.location.href = target;
      } finally {
        clearSamlContext();
      }
    };

    finalize().catch((error: unknown) => {
      console.error('[SAML][callback] failed', error);
      const message = error instanceof Error ? error.message : 'SAML login failed. Please try again.';
      setErrorMessage(message);
      setStatus('error');
    });
  }, [router, searchParams]);

  if (status === 'pending') {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center space-y-4">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary" />
        <p className="text-sm text-muted-foreground">Completing SAML login...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center space-y-4 px-4 text-center">
      <h1 className="text-xl font-semibold">SAML Login Failed</h1>
      {errorMessage && <p className="text-sm text-muted-foreground max-w-md">{errorMessage}</p>}
      <div className="flex gap-2">
        <Button onClick={() => router.replace('/auth/login')}>Go to Login</Button>
        <Button variant="outline" onClick={() => router.replace('/')}>Return Home</Button>
      </div>
    </div>
  );
}

export default function SamlCallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex flex-col items-center justify-center space-y-4">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary" />
          <p className="text-sm text-muted-foreground">Preparing SAML callback...</p>
        </div>
      }
    >
      <SamlCallbackContent />
    </Suspense>
  );
}