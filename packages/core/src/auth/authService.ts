/**
 * Authentication Service
 * Handles user authentication, registration, and session management
 */

import { apiService } from '../services/api.service'
import { API_ENDPOINTS, API_CONFIG } from '../config/api.config'
import type { User, LoginResponse, RegisterResponse } from '../types/api.types'

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterData {
  email: string
  password: string
  name: string
  company: string
  role?: string
}

export interface ForgotPasswordData {
  email: string
}

export interface ResetPasswordData {
  token: string
  password: string
  confirmPassword: string
}

export class AuthService {
  /**
   * Login user
   */
  async login(credentials: LoginCredentials): Promise<LoginResponse> {
    const response = await apiService.post<LoginResponse>(
      API_ENDPOINTS.AUTH.LOGIN,
      credentials
    )

    if (response.data) {
      const { access_token, refresh_token, user } = response.data

      // Store tokens
      apiService.setToken(access_token)
      apiService.setRefreshToken(refresh_token)

      // Store user data
      this.setUser(user)

      return response.data
    }

    throw new Error('Login failed')
  }

  /**
   * Register new user
   */
  async register(data: RegisterData): Promise<RegisterResponse> {
    const response = await apiService.post<RegisterResponse>(
      API_ENDPOINTS.AUTH.REGISTER,
      data
    )

    if (response.data) {
      return response.data
    }

    throw new Error('Registration failed')
  }

  /**
   * Logout user
   */
  async logout(): Promise<void> {
    try {
      await apiService.post(API_ENDPOINTS.AUTH.LOGOUT)
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      // Always clear local data
      apiService.clearTokens()
      this.clearUser()
    }
  }

  /**
   * Get current user
   */
  async getCurrentUser(): Promise<User> {
    const response = await apiService.get<User>(API_ENDPOINTS.AUTH.ME)

    if (response.data) {
      this.setUser(response.data)
      return response.data
    }

    throw new Error('Failed to get current user')
  }

  /**
   * Forgot password
   */
  async forgotPassword(data: ForgotPasswordData): Promise<void> {
    await apiService.post(API_ENDPOINTS.AUTH.FORGOT_PASSWORD, data)
  }

  /**
   * Reset password
   */
  async resetPassword(data: ResetPasswordData): Promise<void> {
    await apiService.post(API_ENDPOINTS.AUTH.RESET_PASSWORD, data)
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    if (typeof window === 'undefined') return false
    const token = localStorage.getItem(API_CONFIG.AUTH.TOKEN_KEY)
    return !!token
  }

  /**
   * Get stored user data
   */
  getUser(): User | null {
    if (typeof window === 'undefined') return null

    const userStr = localStorage.getItem(API_CONFIG.AUTH.USER_KEY)
    if (!userStr) return null

    try {
      return JSON.parse(userStr)
    } catch {
      return null
    }
  }

  /**
   * Store user data
   */
  private setUser(user: User): void {
    if (typeof window === 'undefined') return
    localStorage.setItem(API_CONFIG.AUTH.USER_KEY, JSON.stringify(user))
  }

  /**
   * Clear user data
   */
  private clearUser(): void {
    if (typeof window === 'undefined') return
    localStorage.removeItem(API_CONFIG.AUTH.USER_KEY)
  }

  /**
   * Refresh access token
   */
  async refreshToken(): Promise<string> {
    const refreshToken = localStorage.getItem(API_CONFIG.AUTH.REFRESH_TOKEN_KEY)
    if (!refreshToken) {
      throw new Error('No refresh token available')
    }

    const response = await apiService.post<{ access_token: string }>(
      API_ENDPOINTS.AUTH.REFRESH,
      { refresh_token: refreshToken }
    )

    if (response.data) {
      const { access_token } = response.data
      apiService.setToken(access_token)
      return access_token
    }

    throw new Error('Token refresh failed')
  }
}

export const authService = new AuthService()
