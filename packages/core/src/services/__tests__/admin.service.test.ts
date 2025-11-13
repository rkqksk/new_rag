/**
 * Admin Service Tests
 */

import { adminService } from '../admin.service'
import { apiService } from '../api.service'
import type { User, ApiKey, UsageMetrics } from '../../types/api.types'

// Mock apiService
jest.mock('../api.service', () => ({
  apiService: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
  },
}))

describe('AdminService', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('getUsers', () => {
    it('should get users list with pagination', async () => {
      const mockResponse = {
        items: [
          {
            id: '1',
            email: 'user1@example.com',
            name: 'User 1',
            role: 'admin',
            tenantId: 'tenant-1',
            createdAt: '2025-01-01',
            updatedAt: '2025-01-01',
          },
        ] as User[],
        total: 1,
        page: 1,
        limit: 20,
      }

      ;(apiService.get as jest.Mock).mockResolvedValue({ data: mockResponse })

      const result = await adminService.getUsers({ page: 1, limit: 20 })

      expect(apiService.get).toHaveBeenCalledWith('/admin/users', {
        params: { page: 1, limit: 20 },
      })
      expect(result.items).toHaveLength(1)
      expect(result.total).toBe(1)
    })

    it('should get users with role filter', async () => {
      const mockResponse = {
        items: [],
        total: 0,
        page: 1,
        limit: 20,
      }

      ;(apiService.get as jest.Mock).mockResolvedValue({ data: mockResponse })

      await adminService.getUsers({ page: 1, limit: 20, role: 'admin' })

      expect(apiService.get).toHaveBeenCalledWith('/admin/users', {
        params: { page: 1, limit: 20, role: 'admin' },
      })
    })
  })

  describe('getUser', () => {
    it('should get single user by ID', async () => {
      const mockUser: User = {
        id: '1',
        email: 'user@example.com',
        name: 'Test User',
        role: 'admin',
        tenantId: 'tenant-1',
        createdAt: '2025-01-01',
        updatedAt: '2025-01-01',
      }

      ;(apiService.get as jest.Mock).mockResolvedValue({ data: mockUser })

      const result = await adminService.getUser('1')

      expect(apiService.get).toHaveBeenCalledWith('/admin/users/1')
      expect(result).toEqual(mockUser)
    })

    it('should throw error when user not found', async () => {
      ;(apiService.get as jest.Mock).mockResolvedValue({ data: null })

      await expect(adminService.getUser('invalid')).rejects.toThrow('User not found')
    })
  })

  describe('updateUser', () => {
    it('should update user successfully', async () => {
      const updateData = { name: 'Updated Name', role: 'staff' as const }
      const mockUser: User = {
        id: '1',
        email: 'user@example.com',
        name: 'Updated Name',
        role: 'staff',
        tenantId: 'tenant-1',
        createdAt: '2025-01-01',
        updatedAt: '2025-01-02',
      }

      ;(apiService.put as jest.Mock).mockResolvedValue({ data: mockUser })

      const result = await adminService.updateUser('1', updateData)

      expect(apiService.put).toHaveBeenCalledWith('/admin/users/1', updateData)
      expect(result.name).toBe('Updated Name')
    })
  })

  describe('deleteUser', () => {
    it('should delete user successfully', async () => {
      ;(apiService.delete as jest.Mock).mockResolvedValue({ data: { success: true } })

      await adminService.deleteUser('1')

      expect(apiService.delete).toHaveBeenCalledWith('/admin/users/1')
    })
  })

  describe('API Keys', () => {
    describe('getApiKeys', () => {
      it('should get API keys list', async () => {
        const mockResponse = {
          items: [
            {
              id: '1',
              name: 'Production Key',
              key: 'rag_*********************',
              tenantId: 'tenant-1',
              permissions: ['read', 'write'],
              isActive: true,
              createdAt: '2025-01-01',
              expiresAt: '2026-01-01',
            },
          ] as ApiKey[],
          total: 1,
        }

        ;(apiService.get as jest.Mock).mockResolvedValue({ data: mockResponse })

        const result = await adminService.getApiKeys()

        expect(apiService.get).toHaveBeenCalledWith('/admin/api-keys')
        expect(result.items).toHaveLength(1)
      })
    })

    describe('createApiKey', () => {
      it('should create API key successfully', async () => {
        const keyData = {
          name: 'New Key',
          permissions: ['read'],
          expiresAt: '2026-01-01',
        }

        const mockKey: ApiKey = {
          id: '1',
          name: 'New Key',
          key: 'rag_new_key_123',
          tenantId: 'tenant-1',
          permissions: ['read'],
          isActive: true,
          createdAt: '2025-01-01',
          expiresAt: '2026-01-01',
        }

        ;(apiService.post as jest.Mock).mockResolvedValue({ data: mockKey })

        const result = await adminService.createApiKey(keyData)

        expect(apiService.post).toHaveBeenCalledWith('/admin/api-keys', keyData)
        expect(result.name).toBe('New Key')
        expect(result.key).toBe('rag_new_key_123')
      })
    })

    describe('deleteApiKey', () => {
      it('should delete API key successfully', async () => {
        ;(apiService.delete as jest.Mock).mockResolvedValue({ data: { success: true } })

        await adminService.deleteApiKey('1')

        expect(apiService.delete).toHaveBeenCalledWith('/admin/api-keys/1')
      })
    })

    describe('rotateApiKey', () => {
      it('should rotate API key successfully', async () => {
        const mockKey: ApiKey = {
          id: '1',
          name: 'Production Key',
          key: 'rag_rotated_key_456',
          tenantId: 'tenant-1',
          permissions: ['read', 'write'],
          isActive: true,
          createdAt: '2025-01-01',
          expiresAt: '2026-01-01',
        }

        ;(apiService.post as jest.Mock).mockResolvedValue({ data: mockKey })

        const result = await adminService.rotateApiKey('1')

        expect(apiService.post).toHaveBeenCalledWith('/admin/api-keys/1/rotate')
        expect(result.key).toBe('rag_rotated_key_456')
      })
    })
  })

  describe('getUsageMetrics', () => {
    it('should get usage metrics successfully', async () => {
      const mockMetrics: UsageMetrics = {
        searchCount: 1000,
        apiCalls: 5000,
        storageUsed: 1024 * 1024 * 100, // 100MB
        bandwidthUsed: 1024 * 1024 * 500, // 500MB
        activeUsers: 25,
        period: 'month',
        startDate: '2025-01-01',
        endDate: '2025-01-31',
      }

      ;(apiService.get as jest.Mock).mockResolvedValue({ data: mockMetrics })

      const result = await adminService.getUsageMetrics()

      expect(apiService.get).toHaveBeenCalledWith('/admin/usage')
      expect(result.searchCount).toBe(1000)
      expect(result.activeUsers).toBe(25)
    })
  })

  describe('getHealth', () => {
    it('should get system health status', async () => {
      const mockHealth = {
        status: 'healthy',
        services: {
          database: 'healthy',
          redis: 'healthy',
          qdrant: 'healthy',
        },
        version: '9.1.0',
        uptime: 86400,
      }

      ;(apiService.get as jest.Mock).mockResolvedValue({ data: mockHealth })

      const result = await adminService.getHealth()

      expect(apiService.get).toHaveBeenCalledWith('/admin/health')
      expect(result.status).toBe('healthy')
      expect(result.services.database).toBe('healthy')
    })

    it('should handle unhealthy status', async () => {
      const mockHealth = {
        status: 'unhealthy',
        services: {
          database: 'healthy',
          redis: 'unhealthy',
          qdrant: 'healthy',
        },
        version: '9.1.0',
        uptime: 86400,
      }

      ;(apiService.get as jest.Mock).mockResolvedValue({ data: mockHealth })

      const result = await adminService.getHealth()

      expect(result.status).toBe('unhealthy')
      expect(result.services.redis).toBe('unhealthy')
    })
  })
})
