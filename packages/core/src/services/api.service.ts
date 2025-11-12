/**
 * Base API Service
 * Core HTTP client with retry logic, error handling, and token management
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosError } from 'axios'
import { API_CONFIG, API_ENDPOINTS, HTTP_STATUS, ERROR_MESSAGES } from '../config/api.config'
import type { ApiResponse, ApiError } from '../types/api.types'

export class ApiService {
  private client: AxiosInstance
  private isRefreshing = false
  private failedQueue: Array<{
    resolve: (value?: any) => void
    reject: (reason?: any) => void
  }> = []

  constructor(baseURL: string = API_CONFIG.BASE_URL) {
    this.client = axios.create({
      baseURL: `${baseURL}${API_CONFIG.API_PREFIX}`,
      timeout: API_CONFIG.TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    this.setupInterceptors()
  }

  /**
   * Setup request/response interceptors
   */
  private setupInterceptors() {
    // Request interceptor - Add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = this.getToken()
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )

    // Response interceptor - Handle errors and token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean }

        // Handle 401 Unauthorized - Token expired
        if (error.response?.status === HTTP_STATUS.UNAUTHORIZED && !originalRequest._retry) {
          if (this.isRefreshing) {
            // Queue the request while refreshing
            return new Promise((resolve, reject) => {
              this.failedQueue.push({ resolve, reject })
            })
              .then((token) => {
                if (originalRequest.headers) {
                  originalRequest.headers.Authorization = `Bearer ${token}`
                }
                return this.client(originalRequest)
              })
              .catch((err) => Promise.reject(err))
          }

          originalRequest._retry = true
          this.isRefreshing = true

          try {
            const refreshToken = this.getRefreshToken()
            if (!refreshToken) {
              throw new Error('No refresh token available')
            }

            const response = await this.client.post(API_ENDPOINTS.AUTH.REFRESH, {
              refresh_token: refreshToken,
            })

            const { access_token } = response.data
            this.setToken(access_token)

            // Retry all queued requests
            this.failedQueue.forEach(({ resolve }) => resolve(access_token))
            this.failedQueue = []

            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${access_token}`
            }
            return this.client(originalRequest)
          } catch (refreshError) {
            // Refresh failed - logout user
            this.failedQueue.forEach(({ reject }) => reject(refreshError))
            this.failedQueue = []
            this.clearTokens()
            window.location.href = '/login'
            return Promise.reject(refreshError)
          } finally {
            this.isRefreshing = false
          }
        }

        return Promise.reject(this.handleError(error))
      }
    )
  }

  /**
   * Handle API errors
   */
  private handleError(error: AxiosError): ApiError {
    if (error.response) {
      // Server responded with error
      const status = error.response.status
      const data = error.response.data as any

      return {
        code: data?.code || `HTTP_${status}`,
        message: data?.message || this.getErrorMessage(status),
        details: data?.details,
      }
    } else if (error.request) {
      // Request made but no response
      return {
        code: 'NETWORK_ERROR',
        message: ERROR_MESSAGES.NETWORK_ERROR,
      }
    } else {
      // Error in request setup
      return {
        code: 'UNKNOWN_ERROR',
        message: ERROR_MESSAGES.UNKNOWN,
      }
    }
  }

  /**
   * Get error message for HTTP status code
   */
  private getErrorMessage(status: number): string {
    switch (status) {
      case HTTP_STATUS.UNAUTHORIZED:
        return ERROR_MESSAGES.UNAUTHORIZED
      case HTTP_STATUS.FORBIDDEN:
        return ERROR_MESSAGES.FORBIDDEN
      case HTTP_STATUS.NOT_FOUND:
        return ERROR_MESSAGES.NOT_FOUND
      case HTTP_STATUS.TOO_MANY_REQUESTS:
        return ERROR_MESSAGES.RATE_LIMIT
      default:
        return ERROR_MESSAGES.UNKNOWN
    }
  }

  /**
   * Token management
   */
  private getToken(): string | null {
    if (typeof window === 'undefined') return null
    return localStorage.getItem(API_CONFIG.AUTH.TOKEN_KEY)
  }

  private getRefreshToken(): string | null {
    if (typeof window === 'undefined') return null
    return localStorage.getItem(API_CONFIG.AUTH.REFRESH_TOKEN_KEY)
  }

  setToken(token: string) {
    if (typeof window === 'undefined') return
    localStorage.setItem(API_CONFIG.AUTH.TOKEN_KEY, token)
  }

  setRefreshToken(token: string) {
    if (typeof window === 'undefined') return
    localStorage.setItem(API_CONFIG.AUTH.REFRESH_TOKEN_KEY, token)
  }

  clearTokens() {
    if (typeof window === 'undefined') return
    localStorage.removeItem(API_CONFIG.AUTH.TOKEN_KEY)
    localStorage.removeItem(API_CONFIG.AUTH.REFRESH_TOKEN_KEY)
    localStorage.removeItem(API_CONFIG.AUTH.USER_KEY)
  }

  /**
   * HTTP Methods
   */
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    const response = await this.client.get(url, config)
    return response.data
  }

  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    const response = await this.client.post(url, data, config)
    return response.data
  }

  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    const response = await this.client.put(url, data, config)
    return response.data
  }

  async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    const response = await this.client.patch(url, data, config)
    return response.data
  }

  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    const response = await this.client.delete(url, config)
    return response.data
  }
}

// Singleton instance
export const apiService = new ApiService()
