import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, renderHook, type RenderOptions } from '@testing-library/react';
import { MemoryRouter, type MemoryRouterProps } from 'react-router-dom';

export function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

interface ProviderOptions {
  queryClient?: QueryClient;
  router?: MemoryRouterProps;
}

function TestProviders({
  children,
  queryClient = createTestQueryClient(),
  router,
}: React.PropsWithChildren<ProviderOptions>) {
  return (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter {...router}>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

export function renderWithProviders(
  ui: React.ReactElement,
  {
    queryClient = createTestQueryClient(),
    router,
    ...renderOptions
  }: ProviderOptions & Omit<RenderOptions, 'wrapper'> = {}
) {
  return {
    queryClient,
    ...render(ui, {
      wrapper: ({ children }) => (
        <TestProviders queryClient={queryClient} router={router}>
          {children}
        </TestProviders>
      ),
      ...renderOptions,
    }),
  };
}

export function renderHookWithProviders<Result, Props>(
  callback: (props: Props) => Result,
  { queryClient = createTestQueryClient(), router }: ProviderOptions = {}
) {
  return {
    queryClient,
    ...renderHook(callback, {
      wrapper: ({ children }) => (
        <TestProviders queryClient={queryClient} router={router}>
          {children}
        </TestProviders>
      ),
    }),
  };
}
