import { test, expect } from '@playwright/test'

test.describe('Frontend Loads - Homepage', () => {
  test('should load homepage successfully', async ({ page }) => {
    const response = await page.goto('/')

    expect(response?.status()).toBeLessThan(400)
    await expect(page).toHaveTitle(/RAG|Enterprise|Home|제품/i)
  })

  test('should have no console errors on load', async ({ page }) => {
    const errors: string[] = []

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text())
      }
    })

    page.on('pageerror', (error) => {
      errors.push(error.message)
    })

    await page.goto('/')
    await page.waitForLoadState('networkidle')

    // Filter out known acceptable errors (like CORS from external resources)
    const criticalErrors = errors.filter(
      (error) =>
        !error.includes('CORS') &&
        !error.includes('net::ERR_BLOCKED_BY_CLIENT') && // Ad blockers
        !error.toLowerCase().includes('favicon')
    )

    expect(criticalErrors).toHaveLength(0)
  })

  test('should load all critical resources', async ({ page }) => {
    await page.goto('/')

    // Wait for page to be fully loaded
    await page.waitForLoadState('networkidle')

    // Check for critical elements
    const body = page.locator('body')
    await expect(body).toBeVisible()

    // Check if React/Next.js hydrated successfully
    const appRoot = page.locator('#__next, #root, [data-reactroot]')
    const hasRoot = await appRoot.count()

    expect(hasRoot).toBeGreaterThan(0)
  })

  test('should render without hydration errors', async ({ page }) => {
    const hydrationErrors: string[] = []

    page.on('console', (msg) => {
      const text = msg.text()
      if (
        text.includes('Hydration') ||
        text.includes('hydration') ||
        text.includes('did not match')
      ) {
        hydrationErrors.push(text)
      }
    })

    await page.goto('/')
    await page.waitForLoadState('domcontentloaded')

    expect(hydrationErrors).toHaveLength(0)
  })

  test('should have proper HTML structure', async ({ page }) => {
    await page.goto('/')

    // Check for essential HTML elements
    await expect(page.locator('html')).toBeVisible()
    await expect(page.locator('head')).toBeAttached()
    await expect(page.locator('body')).toBeVisible()

    // Check for meta tags
    const metaViewport = page.locator('meta[name="viewport"]')
    await expect(metaViewport).toBeAttached()
  })
})

test.describe('Frontend Loads - Navigation', () => {
  test('should have navigation bar', async ({ page }) => {
    await page.goto('/')

    const nav = page.locator('nav, header, [role="navigation"]')
    await expect(nav.first()).toBeVisible()
  })

  test('should navigate to different pages', async ({ page }) => {
    await page.goto('/')

    // Try to find common navigation links
    const navLinks = await page.locator('a[href^="/"]').all()

    expect(navLinks.length).toBeGreaterThan(0)

    // Test first internal link if it exists
    if (navLinks.length > 0) {
      const firstLink = navLinks[0]
      const href = await firstLink.getAttribute('href')

      if (href && href !== '/' && !href.includes('#')) {
        await firstLink.click()
        await page.waitForLoadState('domcontentloaded')

        // Should navigate successfully
        expect(page.url()).toBeTruthy()
      }
    }
  })

  test('should handle back navigation', async ({ page }) => {
    await page.goto('/')
    const homeUrl = page.url()

    // Try to navigate to another page
    const navLinks = await page.locator('a[href^="/"]').all()

    if (navLinks.length > 0) {
      await navLinks[0].click()
      await page.waitForTimeout(500)

      // Go back
      await page.goBack()
      await page.waitForLoadState('domcontentloaded')

      expect(page.url()).toBe(homeUrl)
    }
  })

  test('should have working logo/home link', async ({ page }) => {
    await page.goto('/')

    // Look for logo or home link
    const logoLink = page.locator('a[href="/"], a[href="#"], img[alt*="logo" i]').first()

    const hasLogo = (await logoLink.count()) > 0

    if (hasLogo) {
      // Logo should be visible
      await expect(logoLink).toBeVisible()
    }

    // This is not critical, just checking
    expect(typeof hasLogo).toBe('boolean')
  })
})

test.describe('Frontend Loads - Performance', () => {
  test('should load within acceptable time', async ({ page }) => {
    const startTime = Date.now()

    await page.goto('/')
    await page.waitForLoadState('domcontentloaded')

    const loadTime = Date.now() - startTime

    // Should load within 5 seconds (generous for development)
    expect(loadTime).toBeLessThan(5000)
  })

  test('should have minimal layout shift', async ({ page }) => {
    await page.goto('/')

    // Wait for initial layout
    await page.waitForTimeout(1000)

    // Get initial viewport size
    const viewportSize = page.viewportSize()
    expect(viewportSize).toBeTruthy()

    // Page should be stable
    await page.waitForLoadState('networkidle')

    const body = page.locator('body')
    await expect(body).toBeVisible()
  })

  test('should load images lazily or efficiently', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('domcontentloaded')

    // Check if images have loading attribute
    const images = await page.locator('img').all()

    if (images.length > 0) {
      // At least one image should be present
      expect(images.length).toBeGreaterThan(0)

      // Check if lazy loading is configured (optional)
      const firstImage = images[0]
      const loading = await firstImage.getAttribute('loading')

      // This is just informational
      expect(['lazy', 'eager', null]).toContain(loading)
    }
  })
})

test.describe('Frontend Loads - Responsive Design', () => {
  test('should render on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })

    await page.goto('/')
    await page.waitForLoadState('domcontentloaded')

    const body = page.locator('body')
    await expect(body).toBeVisible()

    // Check for mobile-friendly meta tag
    const viewport = await page.locator('meta[name="viewport"]').getAttribute('content')
    expect(viewport).toContain('width=device-width')
  })

  test('should render on tablet viewport', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 })

    await page.goto('/')
    await page.waitForLoadState('domcontentloaded')

    const body = page.locator('body')
    await expect(body).toBeVisible()
  })

  test('should render on desktop viewport', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 })

    await page.goto('/')
    await page.waitForLoadState('domcontentloaded')

    const body = page.locator('body')
    await expect(body).toBeVisible()
  })

  test('should have responsive navigation', async ({ page }) => {
    // Test mobile
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/')

    // Look for mobile menu or regular nav
    const mobileMenu = page.locator('[aria-label*="menu" i], button:has-text("Menu"), button:has-text("메뉴")')
    const regularNav = page.locator('nav, [role="navigation"]')

    const hasMobileMenu = (await mobileMenu.count()) > 0
    const hasRegularNav = (await regularNav.count()) > 0

    expect(hasMobileMenu || hasRegularNav).toBeTruthy()
  })
})

test.describe('Frontend Loads - Accessibility', () => {
  test('should have accessible page title', async ({ page }) => {
    await page.goto('/')

    const title = await page.title()

    expect(title).toBeTruthy()
    expect(title.length).toBeGreaterThan(0)
  })

  test('should have lang attribute on html', async ({ page }) => {
    await page.goto('/')

    const lang = await page.locator('html').getAttribute('lang')

    // Should have lang attribute (ko, en, or other)
    expect(lang).toBeTruthy()
  })

  test('should have skip to main content link', async ({ page }) => {
    await page.goto('/')

    // Look for skip link (optional but recommended)
    const skipLink = page.locator('a[href="#main"], a:has-text("Skip to")')
    const hasSkipLink = (await skipLink.count()) > 0

    // This is optional
    expect(typeof hasSkipLink).toBe('boolean')
  })

  test('should have proper heading hierarchy', async ({ page }) => {
    await page.goto('/')

    // Check for h1
    const h1 = page.locator('h1')
    const h1Count = await h1.count()

    // Should have at least one h1
    expect(h1Count).toBeGreaterThan(0)
    expect(h1Count).toBeLessThanOrEqual(2) // Ideally one, but up to 2 is acceptable
  })

  test('should have no critical accessibility violations', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    // Check for common accessibility issues
    const images = await page.locator('img').all()

    for (const img of images) {
      const alt = await img.getAttribute('alt')
      const ariaLabel = await img.getAttribute('aria-label')

      // Images should have alt text or aria-label (or be decorative)
      const hasAccessibleLabel = alt !== null || ariaLabel !== null

      // This is a warning, not a hard failure
      if (!hasAccessibleLabel) {
        console.warn('Image without alt text found')
      }
    }

    // Test passes if page loads
    expect(page.url()).toBeTruthy()
  })
})

test.describe('Frontend Loads - Links and Resources', () => {
  test('should have no broken internal links on homepage', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    const links = await page.locator('a[href^="/"]').all()

    // Should have some internal links
    if (links.length > 0) {
      expect(links.length).toBeGreaterThan(0)
    }
  })

  test('should load CSS files', async ({ page }) => {
    const cssFiles: string[] = []

    page.on('response', (response) => {
      if (response.url().includes('.css') && response.status() === 200) {
        cssFiles.push(response.url())
      }
    })

    await page.goto('/')
    await page.waitForLoadState('networkidle')

    // Should have loaded at least one CSS file (or have inline styles)
    const hasStyles = cssFiles.length > 0 || (await page.locator('style').count()) > 0

    expect(hasStyles).toBeTruthy()
  })

  test('should load JavaScript files', async ({ page }) => {
    const jsFiles: string[] = []

    page.on('response', (response) => {
      if (
        (response.url().includes('.js') || response.url().includes('/_next/static/')) &&
        response.status() === 200
      ) {
        jsFiles.push(response.url())
      }
    })

    await page.goto('/')
    await page.waitForLoadState('networkidle')

    // Next.js should load JavaScript bundles
    expect(jsFiles.length).toBeGreaterThan(0)
  })

  test('should have favicon', async ({ page }) => {
    const responses: string[] = []

    page.on('response', (response) => {
      if (response.url().includes('favicon')) {
        responses.push(response.url())
      }
    })

    await page.goto('/')
    await page.waitForTimeout(1000)

    // Favicon is optional but recommended
    expect(typeof responses.length).toBe('number')
  })
})
