import { test, expect } from '@playwright/test'

test.describe('Homepage', () => {
  test('should load successfully', async ({ page }) => {
    await page.goto('/')
    await expect(page).toHaveTitle(/RAG Enterprise/)
  })

  test('should have navigation', async ({ page }) => {
    await page.goto('/')
    const nav = page.locator('nav')
    await expect(nav).toBeVisible()
  })

  test('should navigate to login', async ({ page }) => {
    await page.goto('/')
    await page.click('text=Login')
    await expect(page).toHaveURL(/.*login/)
  })
})

test.describe('Search functionality', () => {
  test('should display search bar', async ({ page }) => {
    await page.goto('/')
    const searchInput = page.locator('input[type="search"]')
    await expect(searchInput).toBeVisible()
  })

  test('should perform search', async ({ page }) => {
    await page.goto('/')
    const searchInput = page.locator('input[type="search"]')
    await searchInput.fill('test query')
    await searchInput.press('Enter')
    
    // Wait for results
    await page.waitForSelector('[data-testid="search-results"]', { timeout: 5000 })
  })
})
