import { describe, expect, it } from 'vitest';

import { ApiError } from '@/shared/api';
import { makeQueryClient } from './react-query-client';

describe('makeQueryClient', () => {
  const retry = makeQueryClient().getDefaultOptions().queries?.retry;

  if (typeof retry !== 'function') {
    throw new Error('Expected query retry option to be a function');
  }

  it('does not retry most 4xx API errors', () => {
    const error = new ApiError({ status: 404, message: 'Not found' });

    expect(retry(0, error)).toBe(false);
  });

  it('allows retry for rate limit and transient errors', () => {
    const rateLimit = new ApiError({ status: 429, message: 'Rate limited' });
    const serverError = new ApiError({ status: 500, message: 'Server error' });

    expect(retry(0, rateLimit)).toBe(true);
    expect(retry(0, serverError)).toBe(true);
    expect(retry(3, serverError)).toBe(false);
  });
});
