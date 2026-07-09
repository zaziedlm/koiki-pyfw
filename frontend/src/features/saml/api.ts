import { cookieApiClient } from '@/shared/api';

export interface SamlAuthorizationResponse {
  sso_url: string;
  saml_request: string;
  relay_state: string;
  redirect_url: string;
  sso_binding: string;
  expires_at?: string;
}

export interface SamlLoginResponse {
  location?: string;
  [key: string]: unknown;
}

export const cookieSamlApi = {
  authorization: (params?: { redirect_uri?: string }) => {
    const queryString =
      params && params.redirect_uri
        ? `?${new URLSearchParams({ redirect_uri: params.redirect_uri }).toString()}`
        : '';

    return cookieApiClient.requestJson<SamlAuthorizationResponse>(`/auth/saml/authorization${queryString}`);
  },

  login: async (payload: { login_ticket: string; relay_state: string }) => {
    if (!cookieApiClient.csrfToken) {
      await cookieApiClient.initializeCSRFToken();
    }

    return cookieApiClient.requestJson<SamlLoginResponse>('/auth/session/saml/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
};
