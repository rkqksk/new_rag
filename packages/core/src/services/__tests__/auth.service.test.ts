/**
 * Auth Service Tests
 */

import { authService } from '../auth/authService'
import { apiService } from '../services/api.service'

// Mock apiService
jest.mock('../services/api.service', () => ({
  apiService: {
    post: jest.fn(),
    get: jest.fn(),
    setToken: jest.fn(),
    setRefreshToken: jest.fn(),
    clearTokens: jest.fn(),
  },
}))

describe('AuthService', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    localStorage.clear()
  })

  describe('login', () => {
    it('should login successfully and store tokens', async () => {
      const mockResponse = {
        data: {
          access_token: 'test-token',
          refresh_token: 'test-refresh-token',
          user: {
            id: '1',
            email: 'test@example.com',
            name: 'Test User',
            role: 'admin',
          },
        },
      }

      ;(apiService.post as jest.Mock).mockResolvedValue(mockResponse)

      const credentials = {
        email: 'test@example.com',
        password: 'password123',
      }

      const result = await authService.login(credentials)

      expect(apiService.post).toHaveBeenCalledWith('/auth/login', credentials)
      expect(apiService.setToken).toHaveBeenCalledWith('test-token')
      expect(apiService.setRefreshToken).toHaveBeenCalledWith('test-refresh-token')
      expect(result).toEqual(mockResponse.data)
    })

    it('should throw error on login failure', async () => {
      ;(apiService.post as jest.Mock).mockResolvedValue({ data: null })

      await expect(
        authService.login({ email: 'test@example.com', password: 'wrong' })
      ).rejects.toThrow('Login failed')
    })
  })

  describe('logout', () => {
    it('should clear tokens on logout', async () => {
      ;(apiService.post as jest.Mock).mockResolvedValue({})

      await authService.logout()

      expect(apiService.post).toHaveBeenCalledWith('/auth/logout')
      expect(apiService.clearTokens).toHaveBeenCalled()
    })

    it('should clear tokens even if API call fails', async () => {
      ;(apiService.post as jest.Mock).mockRejectedValue(new Error('Network error'))

      await authService.logout()

      expect(apiService.clearTokens).toHaveBeenCalled()
    })
  })

  describe('isAuthenticated', () => {
    it('should return true if token exists', () => {
      localStorage.setItem('rag_auth_token', 'test-token')

      expect(authService.isAuthenticated()).toBe(true)
    })

    it('should return false if token does not exist', () => {
      expect(authService.isAuthenticated()).toBe(false)
    })
  })

  describe('getUser', () => {
    it('should return user from localStorage', () => {
      const user = {
        id: '1',
        email: 'test@example.com',
        name: 'Test User',
        role: 'admin',
      }

      localStorage.setItem('rag_user', JSON.stringify(user))

      expect(authService.getUser()).toEqual(user)
    })

    it('should return null if user not found', () => {
      expect(authService.getUser()).toBeNull()
    })

    it('should return null if user data is invalid', () => {
      localStorage.setItem('rag_user', 'invalid-json')

      expect(authService.getUser()).toBeNull()
    })
  })
})
