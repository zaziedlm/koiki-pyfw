import { createCSRFTokenResponse } from '@/lib/csrf-utils';

export async function GET() {
  // CSRF トークンを生成してレスポンス
  return createCSRFTokenResponse();
}