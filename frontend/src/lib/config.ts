export const config = {
  api: {
    baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1',
    url: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
  app: {
    name: process.env.NEXT_PUBLIC_APP_NAME || 'KOIKI Task Manager',
    version: process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0',
  },
  auth: {
    tokenKey: 'koiki_access_token',
    refreshTokenKey: 'koiki_refresh_token',
    tokenExpiration: 30 * 60 * 1000, // 30 minutes in milliseconds
  },
} as const;