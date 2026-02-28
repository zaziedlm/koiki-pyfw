'use client';

import { useState } from 'react';
import { config } from '@/lib/config';
import { saveSamlContext } from '@/lib/saml-storage';

/**
 * IdP リダイレクト前に RelayState の残り有効時間をチェックする最小閾値（秒）。
 * この秒数未満しか残っていない場合、IdP でのログイン中に期限切れになる可能性が
 * 高いため、リダイレクトを中止してエラーを返す。
 */
const MIN_REMAINING_SECONDS = 30;

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

      // ── 4-C: IdP リダイレクト前に RelayState 有効期限を事前チェック ──
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
