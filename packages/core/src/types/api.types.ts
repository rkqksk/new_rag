/**
 * API Types
 * Common types for API requests and responses
 */

/**
 * User Types
 */
export interface User {
  id: string
  email: string
  name: string
  role: UserRole
  tenantId: string
  createdAt: string
  updatedAt: string
}

export enum UserRole {
  SUPER_ADMIN = 'super_admin',
  ADMIN = 'admin',
  STAFF = 'staff',
  CUSTOMER = 'customer',
}

/**
 * Auth Types
 */
export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: User
}

export interface RegisterResponse {
  message: string
  user: User
}

/**
 * Tenant Types
 */
export interface Tenant {
  id: string
  name: string
  slug: string
  plan: SubscriptionPlan
  status: TenantStatus
  createdAt: string
  updatedAt: string
}

export enum TenantStatus {
  ACTIVE = 'active',
  SUSPENDED = 'suspended',
  CANCELLED = 'cancelled',
}

export enum SubscriptionPlan {
  FREE = 'free',
  STARTER = 'starter',
  PROFESSIONAL = 'professional',
  ENTERPRISE = 'enterprise',
}

/**
 * API Key Types
 */
export interface ApiKey {
  id: string
  name: string
  key: string // Only returned on creation
  keyPreview: string // Masked key for display
  permissions: string[]
  expiresAt: string | null
  lastUsedAt: string | null
  createdAt: string
}

/**
 * Usage Types
 */
export interface UsageMetrics {
  period: string
  searches: number
  apiCalls: number
  storage: number
  limits: UsageLimits
}

export interface UsageLimits {
  searches: number
  apiCalls: number
  storage: number
}

/**
 * Search Types
 */
export interface SearchRequest {
  query: string
  filters?: Record<string, any>
  limit?: number
  offset?: number
}

export interface SearchResult {
  id: string
  title: string
  description: string
  score: number
  metadata: Record<string, any>
}

export interface SearchResponse {
  results: SearchResult[]
  total: number
  took: number
}

/**
 * Product Types
 */
export interface Product {
  id: string
  name: string
  description: string
  category: string
  price: number
  imageUrl: string
  metadata: Record<string, any>
  createdAt: string
  updatedAt: string
}

/**
 * Analytics Types
 */
export interface AnalyticsOverview {
  totalSearches: number
  totalUsers: number
  avgResponseTime: number
  popularQueries: PopularQuery[]
}

export interface PopularQuery {
  query: string
  count: number
  avgScore: number
}

/**
 * Crawling Types
 */
export interface CrawlingJob {
  id: string
  url: string
  status: JobStatus
  progress: number
  itemsProcessed: number
  errors: string[]
  startedAt: string
  completedAt: string | null
}

export enum JobStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
}

export interface CrawlingScheduler {
  id: string
  name: string
  url: string
  schedule: string // cron expression
  enabled: boolean
  lastRun: string | null
  nextRun: string | null
  createdAt: string
}

/**
 * Webhook Types
 */
export interface Webhook {
  id: string
  url: string
  events: string[]
  secret: string
  enabled: boolean
  lastTriggeredAt: string | null
  createdAt: string
}

/**
 * Common Response Types
 */
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: ApiError
  meta?: {
    page?: number
    limit?: number
    total?: number
  }
}

export interface ApiError {
  code: string
  message: string
  details?: Record<string, any>
}

/**
 * Pagination Types
 */
export interface PaginationParams {
  page?: number
  limit?: number
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  limit: number
  totalPages: number
}
