import { create } from 'zustand';
import { UserState, UserResponse, UserCreate, UserUpdate } from '@/types';
import { userApi } from '@/lib/api-client';

interface UserStore extends UserState {
  // Actions
  fetchUsers: (params?: { skip?: number; limit?: number }) => Promise<void>;
  fetchUser: (id: number) => Promise<UserResponse>;
  createUser: (data: UserCreate) => Promise<UserResponse>;
  updateUser: (id: number, data: UserUpdate) => Promise<UserResponse>;
  deleteUser: (id: number) => Promise<void>;
  updateCurrentUser: (data: UserUpdate) => Promise<UserResponse>;
  clearError: () => void;
}

export const useUserStore = create<UserStore>()((set, get) => ({
  // Initial state
  users: [],
  currentUser: null,
  isLoading: false,
  error: null,
  totalCount: 0,

  // Actions
  fetchUsers: async (params = {}) => {
    set({ isLoading: true, error: null });
    
    try {
      const response = await userApi.getAll(params);
      const users = response.data;
      
      set({
        users,
        totalCount: users.length,
        isLoading: false,
        error: null,
      });
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to fetch users';
      set({
        isLoading: false,
        error: errorMessage,
      });
      throw error;
    }
  },

  fetchUser: async (id: number) => {
    set({ isLoading: true, error: null });
    
    try {
      const response = await userApi.getById(id);
      const user = response.data;
      
      set({
        isLoading: false,
        error: null,
      });
      
      return user;
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to fetch user';
      set({
        isLoading: false,
        error: errorMessage,
      });
      throw error;
    }
  },

  createUser: async (data: UserCreate) => {
    set({ isLoading: true, error: null });
    
    try {
      const response = await userApi.create(data);
      const newUser = response.data;
      
      set((state) => ({
        users: [newUser, ...state.users],
        totalCount: state.totalCount + 1,
        isLoading: false,
        error: null,
      }));
      
      return newUser;
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to create user';
      set({
        isLoading: false,
        error: errorMessage,
      });
      throw error;
    }
  },

  updateUser: async (id: number, data: UserUpdate) => {
    set({ isLoading: true, error: null });
    
    try {
      const response = await userApi.update(id, data);
      const updatedUser = response.data;
      
      set((state) => ({
        users: state.users.map((user) =>
          user.id === id ? updatedUser : user
        ),
        isLoading: false,
        error: null,
      }));
      
      return updatedUser;
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to update user';
      set({
        isLoading: false,
        error: errorMessage,
      });
      throw error;
    }
  },

  deleteUser: async (id: number) => {
    set({ isLoading: true, error: null });
    
    try {
      await userApi.delete(id);
      
      set((state) => ({
        users: state.users.filter((user) => user.id !== id),
        totalCount: state.totalCount - 1,
        isLoading: false,
        error: null,
      }));
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to delete user';
      set({
        isLoading: false,
        error: errorMessage,
      });
      throw error;
    }
  },

  updateCurrentUser: async (data: UserUpdate) => {
    set({ isLoading: true, error: null });
    
    try {
      const response = await userApi.updateMe(data);
      const updatedUser = response.data;
      
      set({
        currentUser: updatedUser,
        isLoading: false,
        error: null,
      });
      
      return updatedUser;
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to update profile';
      set({
        isLoading: false,
        error: errorMessage,
      });
      throw error;
    }
  },

  clearError: () => set({ error: null }),
}));