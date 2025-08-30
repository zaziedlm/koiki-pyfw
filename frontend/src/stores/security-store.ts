import { create } from 'zustand';
import { SecurityState } from '@/types';
import { securityApi } from '@/lib/api-client';

interface SecurityStore extends SecurityState {
  // Actions
  fetchMetrics: () => Promise<void>;
  fetchAuthMetrics: () => Promise<void>;
  fetchSummary: () => Promise<void>;
  fetchHealth: () => Promise<void>;
  resetMetrics: () => Promise<void>;
  clearError: () => void;
  refreshAll: () => Promise<void>;
}

export const useSecurityStore = create<SecurityStore>()((set, get) => ({
  // Initial state
  metrics: null,
  authMetrics: null,
  summary: null,
  health: null,
  isLoading: false,
  error: null,
  lastUpdated: null,

  // Actions
  fetchMetrics: async () => {
    set({ isLoading: true, error: null });
    
    try {
      const response = await securityApi.getMetrics();
      const metrics = response.data;
      
      set({
        metrics,
        isLoading: false,
        error: null,
        lastUpdated: new Date().toISOString(),
      });
    } catch (error: unknown) {
      const errorMessage = (error as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Failed to fetch security metrics';
      set({
        isLoading: false,
        error: errorMessage,
      });
      throw error;
    }
  },

  fetchAuthMetrics: async () => {
    set({ isLoading: true, error: null });
    
    try {
      const response = await securityApi.getAuthMetrics();
      const authMetrics = response.data;
      
      set({
        authMetrics,
        isLoading: false,
        error: null,
        lastUpdated: new Date().toISOString(),
      });
    } catch (error: unknown) {
      const errorMessage = (error as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Failed to fetch authentication metrics';
      set({
        isLoading: false,
        error: errorMessage,
      });
      throw error;
    }
  },

  fetchSummary: async () => {
    set({ isLoading: true, error: null });
    
    try {
      const response = await securityApi.getSummary();
      const summary = response.data;
      
      set({
        summary,
        isLoading: false,
        error: null,
        lastUpdated: new Date().toISOString(),
      });
    } catch (error: unknown) {
      const errorMessage = (error as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Failed to fetch security summary';
      set({
        isLoading: false,
        error: errorMessage,
      });
      throw error;
    }
  },

  fetchHealth: async () => {
    try {
      const response = await securityApi.getHealth();
      const health = response.data;
      
      set({
        health,
        lastUpdated: new Date().toISOString(),
      });
    } catch (error: unknown) {
      // Health check failures shouldn't set the main error state
      console.warn('Security health check failed:', error);
      set({
        health: {
          status: 'down',
          checks: {
            database: false,
            redis: false,
            authentication: false,
            rate_limiting: false,
          },
          timestamp: new Date().toISOString(),
        },
      });
    }
  },

  resetMetrics: async () => {
    set({ isLoading: true, error: null });
    
    try {
      await securityApi.resetMetrics();
      
      // Refresh all data after reset
      await get().refreshAll();
      
      set({
        isLoading: false,
        error: null,
        lastUpdated: new Date().toISOString(),
      });
    } catch (error: unknown) {
      const errorMessage = (error as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Failed to reset security metrics';
      set({
        isLoading: false,
        error: errorMessage,
      });
      throw error;
    }
  },

  refreshAll: async () => {
    set({ isLoading: true, error: null });
    
    try {
      // Fetch all security data in parallel
      await Promise.all([
        get().fetchMetrics(),
        get().fetchAuthMetrics(),
        get().fetchSummary(),
        get().fetchHealth(),
      ]);
      
      set({
        isLoading: false,
        error: null,
        lastUpdated: new Date().toISOString(),
      });
    } catch (error: unknown) {
      const errorMessage = 'Failed to refresh security data';
      set({
        isLoading: false,
        error: errorMessage,
      });
      throw error;
    }
  },

  clearError: () => set({ error: null }),
}));