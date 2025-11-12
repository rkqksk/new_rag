/**
 * Zustand State Management Store
 * Global state for the React Native app
 */

import {create} from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';
import {WorkOrder} from '../services/api';

// ========================================================================
// Types
// ========================================================================

export interface SearchResult {
  id: string;
  name: string;
  category: string;
  price: number;
  image_url: string;
  score: number;
  in_stock: boolean;
}

export interface User {
  id: string;
  name: string;
  email: string;
  phone?: string;
  avatar_url?: string;
  role: string;
}

export interface Message {
  id: string;
  text: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
}

export interface DashboardStats {
  totalWorkOrders: number;
  completedWorkOrders: number;
  inProgressWorkOrders: number;
  delayedWorkOrders: number;
  totalProducts: number;
  recentSearches: number;
}

interface AppState {
  // User
  user: User | null;
  setUser: (user: User | null) => void;

  // Search
  searchResults: SearchResult[];
  setSearchResults: (results: SearchResult[]) => void;
  recentSearches: string[];
  addRecentSearch: (query: string) => void;

  // Work Orders
  workOrders: WorkOrder[];
  setWorkOrders: (orders: WorkOrder[]) => void;
  selectedWorkOrder: WorkOrder | null;
  selectWorkOrder: (order: WorkOrder | null) => void;

  // Chat
  messages: Message[];
  addMessage: (message: Message) => void;
  clearMessages: () => void;

  // Dashboard
  dashboardStats: DashboardStats | null;
  setDashboardStats: (stats: DashboardStats) => void;

  // Settings
  theme: 'light' | 'dark';
  setTheme: (theme: 'light' | 'dark') => void;
  language: 'ko' | 'en';
  setLanguage: (language: 'ko' | 'en') => void;

  // Network
  isOnline: boolean;
  setIsOnline: (online: boolean) => void;

  // Loading
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;

  // Sync
  pendingSync: any[];
  addPendingSync: (data: any) => void;
  clearPendingSync: () => void;

  // Initialize from storage
  initialize: () => Promise<void>;
}

// ========================================================================
// Store
// ========================================================================

export const useStore = create<AppState>((set, get) => ({
  // User
  user: null,
  setUser: (user) => {
    set({user});
    if (user) {
      AsyncStorage.setItem('user', JSON.stringify(user));
    } else {
      AsyncStorage.removeItem('user');
    }
  },

  // Search
  searchResults: [],
  setSearchResults: (results) => set({searchResults: results}),
  recentSearches: [],
  addRecentSearch: (query) => {
    const current = get().recentSearches;
    const updated = [query, ...current.filter(q => q !== query)].slice(0, 10);
    set({recentSearches: updated});
    AsyncStorage.setItem('recentSearches', JSON.stringify(updated));
  },

  // Work Orders
  workOrders: [],
  setWorkOrders: (orders) => set({workOrders: orders}),
  selectedWorkOrder: null,
  selectWorkOrder: (order) => set({selectedWorkOrder: order}),

  // Chat
  messages: [],
  addMessage: (message) => {
    const current = get().messages;
    set({messages: [...current, message]});
  },
  clearMessages: () => set({messages: []}),

  // Dashboard
  dashboardStats: null,
  setDashboardStats: (stats) => set({dashboardStats: stats}),

  // Settings
  theme: 'light',
  setTheme: (theme) => {
    set({theme});
    AsyncStorage.setItem('theme', theme);
  },
  language: 'ko',
  setLanguage: (language) => {
    set({language});
    AsyncStorage.setItem('language', language);
  },

  // Network
  isOnline: true,
  setIsOnline: (online) => set({isOnline: online}),

  // Loading
  isLoading: false,
  setIsLoading: (loading) => set({isLoading: loading}),

  // Sync
  pendingSync: [],
  addPendingSync: (data) => {
    const current = get().pendingSync;
    const updated = [...current, data];
    set({pendingSync: updated});
    AsyncStorage.setItem('pendingSync', JSON.stringify(updated));
  },
  clearPendingSync: () => {
    set({pendingSync: []});
    AsyncStorage.removeItem('pendingSync');
  },

  // Initialize from storage
  initialize: async () => {
    try {
      // Load user
      const userStr = await AsyncStorage.getItem('user');
      if (userStr) {
        set({user: JSON.parse(userStr)});
      }

      // Load recent searches
      const searchesStr = await AsyncStorage.getItem('recentSearches');
      if (searchesStr) {
        set({recentSearches: JSON.parse(searchesStr)});
      }

      // Load theme
      const theme = await AsyncStorage.getItem('theme');
      if (theme === 'light' || theme === 'dark') {
        set({theme});
      }

      // Load language
      const language = await AsyncStorage.getItem('language');
      if (language === 'ko' || language === 'en') {
        set({language});
      }

      // Load pending sync
      const pendingSyncStr = await AsyncStorage.getItem('pendingSync');
      if (pendingSyncStr) {
        set({pendingSync: JSON.parse(pendingSyncStr)});
      }
    } catch (error) {
      console.error('Failed to initialize store:', error);
    }
  },
}));

// ========================================================================
// Selectors (for better performance)
// ========================================================================

export const useUser = () => useStore(state => state.user);
export const useSearchResults = () => useStore(state => state.searchResults);
export const useWorkOrders = () => useStore(state => state.workOrders);
export const useMessages = () => useStore(state => state.messages);
export const useDashboardStats = () => useStore(state => state.dashboardStats);
export const useTheme = () => useStore(state => state.theme);
export const useIsOnline = () => useStore(state => state.isOnline);
export const useIsLoading = () => useStore(state => state.isLoading);
