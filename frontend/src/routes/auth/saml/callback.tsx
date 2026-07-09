import { Suspense, useEffect, useRef, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { cookieSamlApi } from '@/features/saml/api';
import { clearSamlContext, loadSamlContext } from '@/lib/saml-storage';
import { Button } from '@/components/ui/button';

type Status = 'pending' | 'error';

function SamlCallbackContent() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const hasFinalizedRef = useRef(false);

  const [status, setStatus] = useState<Status>('pending');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (hasFinalizedRef.current) {
      return;
    }
    hasFinalizedRef.current = true;

    const samlTicket = searchParams.get('saml_ticket');
    const relayStateFromQuery =
      searchParams.get('relay_state') || searchParams.get('RelayState');

    const finalize = async () => {
      if (!samlTicket) {
        throw new Error('Missing SAML login ticket in callback');
      }

      const stored = loadSamlContext();
      const relayState = stored?.relayState || relayStateFromQuery;
      if (!relayState) {
        throw new Error('Missing RelayState. Please retry the SAML login.');
      }
      if (
        stored?.relayState &&
        relayStateFromQuery &&
        stored.relayState !== relayStateFromQuery
      ) {
        throw new Error('RelayState mismatch detected. Please retry the SAML login.');
      }

      try {
        if (stored?.expiresAt) {
          const expiresAt = new Date(stored.expiresAt).getTime();
          if (!Number.isNaN(expiresAt) && Date.now() > expiresAt) {
            throw new Error('SAML authorization state has expired. Please retry.');
          }
        }

        const data = await cookieSamlApi.login({
          login_ticket: samlTicket,
          relay_state: relayState,
        });

        clearSamlContext();

        navigate(data?.location || '/dashboard', { replace: true });
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
  }, [navigate, searchParams]);

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
        <Button onClick={() => navigate('/auth/login', { replace: true })}>Go to Login</Button>
        <Button variant="outline" onClick={() => navigate('/', { replace: true })}>Return Home</Button>
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
