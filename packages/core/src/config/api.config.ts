/**
 * API Configuration
 * Central configuration for all API endpoints and settings
 */

export const API_CONFIG = {
  // Base URL - can be overridden by environment variables
  BASE_URL: process.env.NEXT_PUBLIC_API_URL || process.env.API_URL || 'http://localhost:8001',

  // API prefix
  API_PREFIX: '/api/v1',

  // Timeout settings (ms)
  TIMEOUT: 30000,

  // Retry settings
  RETRY: {
    enabled: true,
    maxRetries: 3,
    retryDelay: 1000,
  },

  // Auth settings
  AUTH: {
    TOKEN_KEY: 'rag_auth_token',
    REFRESH_TOKEN_KEY: 'rag_refresh_token',
    USER_KEY: 'rag_user',
    TOKEN_EXPIRY_BUFFER: 60, // seconds before expiry to refresh
  },
} as const

/**
 * API Endpoints
 */
export const API_ENDPOINTS = {
  // Authentication
  AUTH: {
    LOGIN: '/auth/login',
    REGISTER: '/auth/register',
    LOGOUT: '/auth/logout',
    REFRESH: '/auth/refresh',
    ME: '/auth/me',
    FORGOT_PASSWORD: '/auth/forgot-password',
    RESET_PASSWORD: '/auth/reset-password',
  },

  // SaaS Management
  SAAS: {
    TENANTS: {
      LIST: '/saas/tenants',
      CREATE: '/saas/tenants',
      GET: (id: string) => `/saas/tenants/${id}`,
      UPDATE: (id: string) => `/saas/tenants/${id}`,
      DELETE: (id: string) => `/saas/tenants/${id}`,
    },
    SUBSCRIPTIONS: {
      LIST: '/saas/subscriptions',
      CREATE: '/saas/subscriptions',
      GET: (id: string) => `/saas/subscriptions/${id}`,
      UPDATE: (id: string) => `/saas/subscriptions/${id}`,
      CANCEL: (id: string) => `/saas/subscriptions/${id}/cancel`,
    },
    API_KEYS: {
      LIST: '/saas/api-keys',
      CREATE: '/saas/api-keys',
      DELETE: (id: string) => `/saas/api-keys/${id}`,
      ROTATE: (id: string) => `/saas/api-keys/${id}/rotate`,
    },
    USAGE: {
      CURRENT: '/saas/usage/current',
      HISTORY: '/saas/usage/history',
      LIMITS: '/saas/usage/limits',
    },
  },

  // Search & RAG
  SEARCH: {
    BASIC: '/search',
    ADVANCED: '/search/advanced',
    HYBRID: '/search/hybrid',
    MULTIMODAL: '/search/multimodal',
    SEMANTIC: '/search/semantic',
  },

  // Products
  PRODUCTS: {
    LIST: '/products',
    GET: (id: string) => `/products/${id}`,
    SEARCH: '/products/search',
  },

  // Analytics
  ANALYTICS: {
    OVERVIEW: '/analytics/overview',
    SEARCH_METRICS: '/analytics/search-metrics',
    USER_BEHAVIOR: '/analytics/user-behavior',
    POPULAR_QUERIES: '/analytics/popular-queries',
  },

  // Admin
  ADMIN: {
    USERS: {
      LIST: '/admin/users',
      GET: (id: string) => `/admin/users/${id}`,
      UPDATE: (id: string) => `/admin/users/${id}`,
      DELETE: (id: string) => `/admin/users/${id}`,
    },
    SETTINGS: '/admin/settings',
    HEALTH: '/health',
  },

  // Crawling
  CRAWLING: {
    JOBS: {
      LIST: '/crawling/jobs',
      CREATE: '/crawling/jobs',
      GET: (id: string) => `/crawling/jobs/${id}`,
      CANCEL: (id: string) => `/crawling/jobs/${id}/cancel`,
    },
    SCHEDULERS: {
      LIST: '/crawling/schedulers',
      CREATE: '/crawling/schedulers',
      UPDATE: (id: string) => `/crawling/schedulers/${id}`,
      DELETE: (id: string) => `/crawling/schedulers/${id}`,
    },
  },

  // Webhooks
  WEBHOOKS: {
    LIST: '/webhooks',
    CREATE: '/webhooks',
    UPDATE: (id: string) => `/webhooks/${id}`,
    DELETE: (id: string) => `/webhooks/${id}`,
    TEST: (id: string) => `/webhooks/${id}/test`,
  },
} as const

/**
 * HTTP Status Codes
 */
export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  NO_CONTENT: 204,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  CONFLICT: 409,
  UNPROCESSABLE_ENTITY: 422,
  TOO_MANY_REQUESTS: 429,
  INTERNAL_SERVER_ERROR: 500,
  SERVICE_UNAVAILABLE: 503,
} as const

/**
 * Error Messages
 */
export const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Network error. Please check your connection.',
  UNAUTHORIZED: 'You are not authorized. Please log in.',
  FORBIDDEN: 'You do not have permission to perform this action.',
  NOT_FOUND: 'The requested resource was not found.',
  TIMEOUT: 'Request timed out. Please try again.',
  UNKNOWN: 'An unknown error occurred. Please try again.',
  RATE_LIMIT: 'Too many requests. Please try again later.',
} as const
