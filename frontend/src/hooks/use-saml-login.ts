'use client';

import { useState } from 'react';
import { config } from '@/lib/config';
import { saveSamlContext } from '@/lib/saml-storage';

interface SamlAuthorizationResponse {
  sso_url: string;
  saml_request: string;
  relay_state: string;
  redirect_url: string;
  sso_binding: string;
  expires_at?: string;
}

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

      // Call backend SAML authorization endpoint via Next.js API route
      const response = await fetch(`/api/saml/authorization?redirect_uri=${encodeURIComponent(redirectUri)}`, {
        method: 'GET',
        credentials: 'include',
      });

      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        const message = payload?.detail || payload?.message || 'SAML authorization request failed';
        throw new Error(message);
      }

      const context = (await response.json()) as SamlAuthorizationResponse;

      // Save SAML context to sessionStorage
      saveSamlContext({
        relayState: context.relay_state,
        redirectUri,
        expiresAt: context.expires_at,
        createdAt: new Date().toISOString(),
      });

      // RelayState付きのURL（後方互換で sso_url もフォールバック）
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
