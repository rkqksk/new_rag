/**
 * Search Service Tests
 */

import { searchService } from '../search.service'
import { apiService } from '../api.service'
import type { SearchRequest, SearchResponse } from '../../types/api.types'

// Mock apiService
jest.mock('../api.service', () => ({
  apiService: {
    post: jest.fn(),
    get: jest.fn(),
  },
}))

describe('SearchService', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('search', () => {
    it('should perform basic search successfully', async () => {
      const mockRequest: SearchRequest = {
        query: '50ml PET container',
        limit: 10,
      }

      const mockResponse: SearchResponse = {
        results: [
          {
            id: '1',
            productId: 'prod-1',
            title: '50ml PET Container',
            description: 'High-quality PET container',
            similarity: 0.95,
            metadata: {},
            highlights: [],
          },
        ],
        total: 1,
        took: 125,
      }

      ;(apiService.post as jest.Mock).mockResolvedValue({ data: mockResponse })

      const result = await searchService.search(mockRequest)

      expect(apiService.post).toHaveBeenCalledWith('/search/', mockRequest)
      expect(result).toEqual(mockResponse)
      expect(result.results).toHaveLength(1)
      expect(result.results[0].similarity).toBe(0.95)
    })

    it('should throw error when search fails', async () => {
      ;(apiService.post as jest.Mock).mockResolvedValue({ data: null })

      await expect(
        searchService.search({ query: 'test', limit: 10 })
      ).rejects.toThrow('Search failed')
    })
  })

  describe('advancedSearch', () => {
    it('should perform advanced search with filters', async () => {
      const mockRequest = {
        query: 'container',
        filters: {
          category: 'PET',
          minCapacity: 50,
          maxCapacity: 100,
        },
        limit: 20,
        offset: 0,
      }

      const mockResponse: SearchResponse = {
        results: [
          {
            id: '1',
            productId: 'prod-1',
            title: '50ml PET Container',
            description: 'Test',
            similarity: 0.9,
            metadata: { category: 'PET', capacity: 50 },
            highlights: [],
          },
        ],
        total: 1,
        took: 150,
      }

      ;(apiService.post as jest.Mock).mockResolvedValue({ data: mockResponse })

      const result = await searchService.advancedSearch(mockRequest)

      expect(apiService.post).toHaveBeenCalledWith('/search/advanced', mockRequest)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('hybridSearch', () => {
    it('should perform hybrid search', async () => {
      const mockRequest = {
        query: 'PET bottle',
        useSemanticSearch: true,
        useKeywordSearch: true,
        weights: { semantic: 0.7, keyword: 0.3 },
      }

      const mockResponse: SearchResponse = {
        results: [],
        total: 0,
        took: 200,
      }

      ;(apiService.post as jest.Mock).mockResolvedValue({ data: mockResponse })

      const result = await searchService.hybridSearch(mockRequest)

      expect(apiService.post).toHaveBeenCalledWith('/search/hybrid', mockRequest)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getProduct', () => {
    it('should get single product by ID', async () => {
      const productId = 'prod-123'
      const mockProduct = {
        id: productId,
        name: 'Test Product',
        description: 'Test Description',
        category: 'PET',
        capacity: 100,
        createdAt: '2025-01-01',
        updatedAt: '2025-01-01',
      }

      ;(apiService.get as jest.Mock).mockResolvedValue({ data: mockProduct })

      const result = await searchService.getProduct(productId)

      expect(apiService.get).toHaveBeenCalledWith(`/search/products/${productId}`)
      expect(result).toEqual(mockProduct)
    })

    it('should throw error when product not found', async () => {
      ;(apiService.get as jest.Mock).mockResolvedValue({ data: null })

      await expect(searchService.getProduct('invalid-id')).rejects.toThrow(
        'Product not found'
      )
    })
  })

  describe('listProducts', () => {
    it('should list products with pagination', async () => {
      const mockResponse = {
        items: [
          {
            id: '1',
            name: 'Product 1',
            description: 'Desc 1',
            category: 'PET',
            capacity: 50,
            createdAt: '2025-01-01',
            updatedAt: '2025-01-01',
          },
          {
            id: '2',
            name: 'Product 2',
            description: 'Desc 2',
            category: 'Glass',
            capacity: 100,
            createdAt: '2025-01-01',
            updatedAt: '2025-01-01',
          },
        ],
        total: 2,
        page: 1,
        limit: 10,
      }

      ;(apiService.get as jest.Mock).mockResolvedValue({ data: mockResponse })

      const result = await searchService.listProducts({ page: 1, limit: 10 })

      expect(apiService.get).toHaveBeenCalledWith('/search/products', {
        params: { page: 1, limit: 10 },
      })
      expect(result.items).toHaveLength(2)
      expect(result.total).toBe(2)
    })
  })
})
