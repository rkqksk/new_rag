/**
 * API Service Layer
 * Handles all HTTP requests to the backend
 */

import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

// API Configuration
const API_BASE_URL = 'http://localhost:8001/api/v1';
const MOBILE_API_BASE_URL = 'http://localhost:8001/api/v1/mobile-api';

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Create mobile API instance
const mobileApi: AxiosInstance = axios.create({
  baseURL: MOBILE_API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - add auth token
api.interceptors.request.use(
  async (config) => {
    const token = await AsyncStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

mobileApi.interceptors.request.use(
  async (config) => {
    const token = await AsyncStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - handle errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired, logout user
      await AsyncStorage.removeItem('auth_token');
    }
    return Promise.reject(error);
  }
);

// ========================================================================
// Search APIs
// ========================================================================

export const searchProducts = async (query: string, topK: number = 10) => {
  const response = await mobileApi.post('/search', {
    query,
    top_k: topK,
    include_images: true,
  });
  return response.data;
};

export const imageSearch = async (imageUri: string, topK: number = 10) => {
  const formData = new FormData();
  formData.append('file', {
    uri: imageUri,
    type: 'image/jpeg',
    name: 'image.jpg',
  } as any);

  const response = await mobileApi.post('/image-search', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const voiceSearch = async (audioUri: string, language: string = 'ko-KR') => {
  const formData = new FormData();
  formData.append('audio', {
    uri: audioUri,
    type: 'audio/wav',
    name: 'audio.wav',
  } as any);

  const response = await mobileApi.post(`/voice-search?language=${language}`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

// ========================================================================
// QR Code APIs
// ========================================================================

export const scanQRCode = async (qrData: string) => {
  const response = await mobileApi.post('/qr/scan', {
    qr_data: qrData,
  });
  return response.data;
};

// ========================================================================
// Work Orders APIs
// ========================================================================

export interface WorkOrder {
  wo_id: string;
  wo_number: string;
  product_name: string;
  quantity_planned: number;
  quantity_completed: number;
  status: 'planned' | 'inprogress' | 'completed' | 'delayed';
  priority: number;
  start_date: string;
  due_date: string;
  progress_percent: number;
}

export const getWorkOrders = async (status?: string) => {
  const params = status ? { status } : {};
  const response = await mobileApi.get('/work-orders', { params });
  return response.data.work_orders as WorkOrder[];
};

export const getWorkOrderById = async (woId: string) => {
  const response = await mobileApi.get(`/work-orders/${woId}`);
  return response.data;
};

export const updateWorkOrderStatus = async (woId: string, status: string) => {
  const response = await mobileApi.patch(`/work-orders/${woId}`, { status });
  return response.data;
};

// ========================================================================
// Sync APIs
// ========================================================================

export const syncOfflineData = async (deviceId: string, lastSync: string, pendingData: any[]) => {
  const response = await mobileApi.post('/sync', {
    device_id: deviceId,
    last_sync: lastSync,
    pending_data: pendingData,
  });
  return response.data;
};

// ========================================================================
// Notification APIs
// ========================================================================

export const registerDevice = async (
  deviceId: string,
  platform: 'ios' | 'android',
  pushToken: string,
  userId: string
) => {
  const response = await mobileApi.post('/notifications/register', {
    device_id: deviceId,
    platform,
    push_token: pushToken,
    user_id: userId,
  });
  return response.data;
};

// ========================================================================
// Analytics APIs
// ========================================================================

export const trackEvent = async (eventName: string, eventData: any) => {
  const response = await mobileApi.post('/analytics/event', {
    event_name: eventName,
    event_data: eventData,
    timestamp: new Date().toISOString(),
  });
  return response.data;
};

// ========================================================================
// Vision Inspection APIs
// ========================================================================

export const performVisionInspection = async (imageUri: string) => {
  const formData = new FormData();
  formData.append('image', {
    uri: imageUri,
    type: 'image/jpeg',
    name: 'inspection.jpg',
  } as any);

  const response = await api.post('/vision/inspect', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

// ========================================================================
// Dashboard APIs
// ========================================================================

export const getDashboardStats = async () => {
  const response = await api.get('/dashboard/stats');
  return response.data;
};

export const getRecentActivity = async (limit: number = 10) => {
  const response = await api.get('/dashboard/recent-activity', {
    params: { limit },
  });
  return response.data;
};

// ========================================================================
// User Profile APIs
// ========================================================================

export const getUserProfile = async () => {
  const response = await api.get('/users/me');
  return response.data;
};

export const updateUserProfile = async (profileData: any) => {
  const response = await api.patch('/users/me', profileData);
  return response.data;
};

export const uploadProfileImage = async (imageUri: string) => {
  const formData = new FormData();
  formData.append('image', {
    uri: imageUri,
    type: 'image/jpeg',
    name: 'profile.jpg',
  } as any);

  const response = await api.post('/users/me/photo', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

// ========================================================================
// Chat APIs
// ========================================================================

export const sendChatMessage = async (message: string, conversationId?: string) => {
  const response = await api.post('/chat/messages', {
    message,
    conversation_id: conversationId,
  });
  return response.data;
};

export const getChatHistory = async (conversationId: string, limit: number = 50) => {
  const response = await api.get(`/chat/conversations/${conversationId}/messages`, {
    params: { limit },
  });
  return response.data;
};

export const getConversations = async () => {
  const response = await api.get('/chat/conversations');
  return response.data;
};

export default {
  searchProducts,
  imageSearch,
  voiceSearch,
  scanQRCode,
  getWorkOrders,
  getWorkOrderById,
  updateWorkOrderStatus,
  syncOfflineData,
  registerDevice,
  trackEvent,
  performVisionInspection,
  getDashboardStats,
  getRecentActivity,
  getUserProfile,
  updateUserProfile,
  uploadProfileImage,
  sendChatMessage,
  getChatHistory,
  getConversations,
};
