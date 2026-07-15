import { cookieApiClient } from '@/shared/api';

export interface SsoAuthorizationResponse {
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

export interface SsoLoginResponse {
  location?: string;
  [key: string]: unknown;
}

export const cookieSsoApi = {
  authorization: (params?: { redirect_uri?: string }) => {
    const queryString =
      params && params.redirect_uri
        ? `?${new URLSearchParams({ redirect_uri: params.redirect_uri }).toString()}`
        : '';

    return cookieApiClient.requestJson<SsoAuthorizationResponse>(`/auth/sso/authorization${queryString}`);
  },

  login: (payload: {
    authorization_code: string;
    code_verifier: string;
    state: string;
    nonce: string;
    redirect_uri: string;
  }) =>
    cookieApiClient.requestJson<SsoLoginResponse>('/auth/session/sso/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};
