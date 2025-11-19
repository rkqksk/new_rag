import { test, expect } from '@playwright/test'

test.describe('Authentication', () => {
  test('should show login page', async ({ page }) => {
    await page.goto('/login')
    await expect(page.locator('h1')).toContainText(/login/i)
  })

  test('should validate email field', async ({ page }) => {
    await page.goto('/login')
    
    const emailInput = page.locator('input[type="email"]')
    const submitButton = page.locator('button[type="submit"]')
    
    await emailInput.fill('invalid-email')
    await submitButton.click()
    
    await expect(page.locator('text=/invalid.*email/i')).toBeVisible()
  })

  test('should show register page', async ({ page }) => {
    await page.goto('/register')
    await expect(page.locator('h1')).toContainText(/register|sign up/i)
  })
})
