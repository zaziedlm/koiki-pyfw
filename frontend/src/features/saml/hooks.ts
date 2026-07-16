import { useState } from 'react';
import { config } from '@/lib/config';
import { saveSamlContext } from '@/lib/saml-storage';
import { cookieSamlApi } from './api';

const MIN_REMAINING_SECONDS = 30;

function buildRedirectUri(explicitRedirect?: string): string {
  if (typeof window === 'undefined') {
    return explicitRedirect || config.saml?.redirectUri || '/auth/saml/callback';
  }

  const base = explicitRedirect || config.saml?.redirectUri || '/auth/saml/callback';
  try {
    return new URL(base, window.location.origin).toString();
  } catch {
    return `${window.location.origin}/auth/saml/callback`;
  }
}

export function useSamlLogin() {
  const [isLoading, setIsLoading] = useState(false);

  const startSamlLogin = async (options?: { redirectUri?: string }) => {
    if (isLoading) return;
    setIsLoading(true);

    try {
      const redirectUri = buildRedirectUri(options?.redirectUri);

      const context = await cookieSamlApi.authorization({ redirect_uri: redirectUri });

      if (context.expires_at) {
        const expiresMs = new Date(context.expires_at).getTime();
        if (!Number.isNaN(expiresMs)) {
          const remainingSec = (expiresMs - Date.now()) / 1000;
          if (remainingSec < MIN_REMAINING_SECONDS) {
            throw new Error(
              `SAML authorization state will expire too soon (${Math.round(remainingSec)}s remaining). Please retry.`,
            );
          }
        }
      }

      saveSamlContext({
        relayState: context.relay_state,
        redirectUri,
        expiresAt: context.expires_at,
        createdAt: new Date().toISOString(),
      });

      const redirectTarget = context.redirect_url || context.sso_url;
      window.location.href = redirectTarget;
    } catch (error) {
      setIsLoading(false);
      throw error;
    }
  };

  return {
    startSamlLogin,
    isLoading,
  };
}
