/**
 * Search Service
 * Handles all search-related API calls
 */

import { apiService } from './api.service'
import { API_ENDPOINTS } from '../config/api.config'
import type { SearchRequest, SearchResponse, Product } from '../types/api.types'

export class SearchService {
  /**
   * Basic search
   */
  async search(request: SearchRequest): Promise<SearchResponse> {
    const response = await apiService.post<SearchResponse>(
      API_ENDPOINTS.SEARCH.BASIC,
      request
    )
    return response.data!
  }

  /**
   * Advanced search with filters
   */
  async advancedSearch(request: SearchRequest): Promise<SearchResponse> {
    const response = await apiService.post<SearchResponse>(
      API_ENDPOINTS.SEARCH.ADVANCED,
      request
    )
    return response.data!
  }

  /**
   * Hybrid search (combines multiple strategies)
   */
  async hybridSearch(request: SearchRequest): Promise<SearchResponse> {
    const response = await apiService.post<SearchResponse>(
      API_ENDPOINTS.SEARCH.HYBRID,
      request
    )
    return response.data!
  }

  /**
   * Multimodal search (text + image)
   */
  async multimodalSearch(query: string, image?: File): Promise<SearchResponse> {
    const formData = new FormData()
    formData.append('query', query)
    if (image) {
      formData.append('image', image)
    }

    const response = await apiService.post<SearchResponse>(
      API_ENDPOINTS.SEARCH.MULTIMODAL,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    )
    return response.data!
  }

  /**
   * Get product by ID
   */
  async getProduct(id: string): Promise<Product> {
    const response = await apiService.get<Product>(
      API_ENDPOINTS.PRODUCTS.GET(id)
    )
    return response.data!
  }

  /**
   * List products
   */
  async listProducts(params?: {
    page?: number
    limit?: number
    category?: string
  }): Promise<{ items: Product[]; total: number }> {
    const response = await apiService.get<{ items: Product[]; total: number }>(
      API_ENDPOINTS.PRODUCTS.LIST,
      { params }
    )
    return response.data!
  }
}

export const searchService = new SearchService()
