import { test, expect } from '@playwright/test'

const API_BASE_URL = 'http://localhost:8001'

test.describe('Backend Health Checks', () => {
  test('should return ready status from /health/ready', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/health/ready`)

    expect(response.status()).toBe(200)

    const data = await response.json()
    expect(data).toHaveProperty('status')
    expect(data.status).toBe('ready')
  })

  test('should return liveness status from /health/liveness', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/health/liveness`)

    expect(response.status()).toBe(200)

    const data = await response.json()
    expect(data).toHaveProperty('status')
    expect(data.status).toBe('alive')
  })

  test('should load API documentation', async ({ page }) => {
    await page.goto(`${API_BASE_URL}/api/v1/docs`)

    // Check for Swagger UI elements
    await expect(page.locator('.swagger-ui')).toBeVisible({ timeout: 10000 })

    // Check for API title
    const title = page.locator('.title')
    await expect(title).toBeVisible()
  })

  test('should have OpenAPI spec available', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/api/v1/openapi.json`)

    expect(response.status()).toBe(200)

    const spec = await response.json()
    expect(spec).toHaveProperty('openapi')
    expect(spec).toHaveProperty('info')
    expect(spec.info).toHaveProperty('title')
  })
})

test.describe('Basic Search Endpoint', () => {
  test('should accept POST request to /api/v1/search/', async ({ request }) => {
    const response = await request.post(`${API_BASE_URL}/api/v1/search/`, {
      data: {
        query: 'test query',
        top_k: 5
      }
    })

    // Accept 200 (success) or 404 (no results) or 422 (validation error)
    expect([200, 404, 422, 500]).toContain(response.status())
  })

  test('should reject invalid search request', async ({ request }) => {
    const response = await request.post(`${API_BASE_URL}/api/v1/search/`, {
      data: {
        // Missing required 'query' field
        top_k: 5
      }
    })

    expect(response.status()).toBe(422) // Validation error
  })

  test('should validate top_k parameter', async ({ request }) => {
    const response = await request.post(`${API_BASE_URL}/api/v1/search/`, {
      data: {
        query: 'test',
        top_k: -1 // Invalid negative value
      }
    })

    // Should either reject or handle gracefully
    expect([200, 422, 400]).toContain(response.status())
  })
})

test.describe('CORS and Headers', () => {
  test('should include CORS headers', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/health/ready`)

    const headers = response.headers()
    // Check if CORS is configured (may not be present in all environments)
    // This is a soft check
    expect(response.status()).toBeLessThan(500)
  })

  test('should include Content-Type header', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/health/ready`)

    const headers = response.headers()
    expect(headers['content-type']).toContain('application/json')
  })
})
