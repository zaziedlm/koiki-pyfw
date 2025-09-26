'use client';

import { useState } from 'react';
import { cookieApiClient } from '@/lib/cookie-api-client';
import { config } from '@/lib/config';
import { generateCodeChallenge, generateCodeVerifier } from '@/lib/pkce';
import { saveSsoContext } from '@/lib/sso-storage';

interface SsoAuthorizationResponse {
  authorization_endpoint: string;
  authorization_base_url: string;
  response_type: string;
  client_id: string;
  redirect_uri: string;
  scope: string;
  state: string;
  nonce: string;
  expires_at?: string;
  code_challenge_method?: string;
}

const DEFAULT_CODE_CHALLENGE_METHOD = 'S256';

function buildRedirectUri(explicitRedirect?: string): string {
  if (typeof window === 'undefined') {
    return explicitRedirect || config.sso.redirectUri;
  }

  const base = explicitRedirect || config.sso.redirectUri;
  try {
    return new URL(base, window.location.origin).toString();
  } catch {
    return `${window.location.origin}/sso/callback`;
  }
}

export function useSsoLogin() {
  const [isLoading, setIsLoading] = useState(false);

  const startSsoLogin = async (options?: { redirectUri?: string }) => {
    if (isLoading) return;
    setIsLoading(true);

    try {
      const redirectUri = buildRedirectUri(options?.redirectUri);

      const response = await cookieApiClient.sso.authorization({ redirect_uri: redirectUri });

      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        const message = payload?.detail || payload?.message || 'SSO authorization request failed';
        throw new Error(message);
      }

      const context = (await response.json()) as SsoAuthorizationResponse;

      const codeVerifier = generateCodeVerifier();
      const codeChallenge = await generateCodeChallenge(codeVerifier);
      const challengeMethod = context.code_challenge_method || DEFAULT_CODE_CHALLENGE_METHOD;

      saveSsoContext({
        codeVerifier,
        state: context.state,
        nonce: context.nonce,
        redirectUri: context.redirect_uri || redirectUri,
        expiresAt: context.expires_at,
        createdAt: new Date().toISOString(),
      });

      const separator = context.authorization_base_url.includes('?') ? '&' : '?';
      const url = `${context.authorization_base_url}${separator}code_challenge=${encodeURIComponent(
        codeChallenge,
      )}&code_challenge_method=${encodeURIComponent(challengeMethod)}`;

      window.location.href = url;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    startSsoLogin,
    isLoading,
  };
}
