/**
 * @rag/core - Core Business Logic
 * Shared services, utilities, and types for RAG Enterprise
 */

// Services
export { apiService, ApiService } from './services/api.service'
export { authService, AuthService } from './auth/authService'
export { searchService, SearchService } from './services/search.service'
export { adminService, AdminService } from './services/admin.service'

// Hooks
export { useRealtime } from './hooks/useRealtime'
export { useOptimistic, useOptimisticList } from './hooks/useOptimistic'
export { useOffline, useOfflineQueue } from './hooks/useOffline'

export type {
  RealtimeMessage,
  UseRealtimeOptions,
  UseRealtimeReturn,
} from './hooks/useRealtime'

export type {
  OptimisticUpdate,
  UseOptimisticOptions,
  UseOptimisticReturn,
} from './hooks/useOptimistic'

export type { UseOfflineOptions, UseOfflineReturn } from './hooks/useOffline'

// Utilities
export {
  isOnline,
  getQueuedOperations,
  queueOperation,
  removeQueuedOperation,
  clearQueue,
  processQueue,
  setupOfflineListeners,
  cacheData,
  getCachedData,
  clearCache,
} from './utils/offline'

export type { QueuedOperation } from './utils/offline'

// Auth Types
export type {
  LoginCredentials,
  RegisterData,
  ForgotPasswordData,
  ResetPasswordData,
} from './auth/authService'

// Configuration
export { API_CONFIG, API_ENDPOINTS, HTTP_STATUS, ERROR_MESSAGES } from './config/api.config'

// Types - Enums must be exported as values, not types
export {
  UserRole,
  TenantStatus,
  SubscriptionPlan,
  JobStatus,
} from './types/api.types'

export type {
  User,
  LoginResponse,
  RegisterResponse,
  Tenant,
  ApiKey,
  UsageMetrics,
  UsageLimits,
  SearchRequest,
  SearchResult,
  SearchResponse,
  Product,
  AnalyticsOverview,
  PopularQuery,
  CrawlingJob,
  CrawlingScheduler,
  Webhook,
  ApiResponse,
  ApiError,
  PaginationParams,
  PaginatedResponse,
} from './types/api.types'
