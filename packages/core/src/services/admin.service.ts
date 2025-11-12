/**
 * Admin Service
 * Handles admin-related API calls
 */

import { apiService } from './api.service'
import { API_ENDPOINTS } from '../config/api.config'
import type { User, ApiKey, UsageMetrics } from '../types/api.types'

export class AdminService {
  /**
   * Get all users
   */
  async getUsers(params?: {
    page?: number
    limit?: number
    role?: string
  }): Promise<{ items: User[]; total: number }> {
    const response = await apiService.get<{ items: User[]; total: number }>(
      API_ENDPOINTS.ADMIN.USERS.LIST,
      { params }
    )
    return response.data!
  }

  /**
   * Get user by ID
   */
  async getUser(id: string): Promise<User> {
    const response = await apiService.get<User>(
      API_ENDPOINTS.ADMIN.USERS.GET(id)
    )
    return response.data!
  }

  /**
   * Update user
   */
  async updateUser(id: string, data: Partial<User>): Promise<User> {
    const response = await apiService.put<User>(
      API_ENDPOINTS.ADMIN.USERS.UPDATE(id),
      data
    )
    return response.data!
  }

  /**
   * Delete user
   */
  async deleteUser(id: string): Promise<void> {
    await apiService.delete(API_ENDPOINTS.ADMIN.USERS.DELETE(id))
  }

  /**
   * Get API keys
   */
  async getApiKeys(): Promise<ApiKey[]> {
    const response = await apiService.get<ApiKey[]>(
      API_ENDPOINTS.SAAS.API_KEYS.LIST
    )
    return response.data!
  }

  /**
   * Create API key
   */
  async createApiKey(data: {
    name: string
    permissions: string[]
    expiresAt?: string
  }): Promise<ApiKey> {
    const response = await apiService.post<ApiKey>(
      API_ENDPOINTS.SAAS.API_KEYS.CREATE,
      data
    )
    return response.data!
  }

  /**
   * Delete API key
   */
  async deleteApiKey(id: string): Promise<void> {
    await apiService.delete(API_ENDPOINTS.SAAS.API_KEYS.DELETE(id))
  }

  /**
   * Rotate API key
   */
  async rotateApiKey(id: string): Promise<ApiKey> {
    const response = await apiService.post<ApiKey>(
      API_ENDPOINTS.SAAS.API_KEYS.ROTATE(id)
    )
    return response.data!
  }

  /**
   * Get usage metrics
   */
  async getUsageMetrics(): Promise<UsageMetrics> {
    const response = await apiService.get<UsageMetrics>(
      API_ENDPOINTS.SAAS.USAGE.CURRENT
    )
    return response.data!
  }

  /**
   * Get system health
   */
  async getHealth(): Promise<{ status: string; version: string }> {
    const response = await apiService.get<{ status: string; version: string }>(
      API_ENDPOINTS.ADMIN.HEALTH
    )
    return response.data!
  }
}

export const adminService = new AdminService()
