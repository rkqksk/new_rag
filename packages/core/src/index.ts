/**
 * @rag/core - Core Business Logic
 * Shared services, utilities, and types for RAG Enterprise
 */

// Services
export { apiService, ApiService } from './services/api.service'
export { authService, AuthService } from './auth/authService'
export { searchService, SearchService } from './services/search.service'
export { adminService, AdminService } from './services/admin.service'

// Auth Types
export type {
  LoginCredentials,
  RegisterData,
  ForgotPasswordData,
  ResetPasswordData,
} from './auth/authService'

// Configuration
export { API_CONFIG, API_ENDPOINTS, HTTP_STATUS, ERROR_MESSAGES } from './config/api.config'

// Types
export type {
  User,
  UserRole,
  LoginResponse,
  RegisterResponse,
  Tenant,
  TenantStatus,
  SubscriptionPlan,
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
  JobStatus,
  CrawlingScheduler,
  Webhook,
  ApiResponse,
  ApiError,
  PaginationParams,
  PaginatedResponse,
} from './types/api.types'
