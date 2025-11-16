---
name: web-testing
description: Frontend webapp E2E testing Playwright Selenium UI automation browser test visual regression 프론트엔드 테스트 브라우저 자동화 시각적 회귀 테스트 accessibility a11y performance
---

# Web Application Testing

## When to Use
- 프론트엔드 테스트, frontend testing
- UI 테스트, UI testing
- E2E 자동화, E2E automation
- 브라우저 테스트, browser testing
- 시각적 회귀, visual regression
- 접근성 검사, accessibility testing
- 성능 테스트, performance testing

## Core Capabilities
1. **E2E Testing** - Playwright, automated user flows
2. **Visual Regression** - Screenshot comparison
3. **Accessibility** - a11y audits, WCAG compliance
4. **Performance** - Lighthouse, Core Web Vitals
5. **Cross-Browser** - Chrome, Firefox, Safari, Edge

## Quick Actions

### Generate E2E Tests
```python
# Auto-generate from user flows
python scripts/create_e2e_suite.py \
  --flows login,search,checkout \
  --pages frontend/*.html \
  --output tests/e2e/
```

### Run Playwright Tests
```bash
# All tests
npx playwright test

# Specific test
npx playwright test tests/e2e/search.spec.ts

# Headed mode (see browser)
npx playwright test --headed

# Debug mode
npx playwright test --debug
```

### Visual Regression
```bash
# Generate baseline
npx playwright test --update-snapshots

# Compare
npx playwright test
```

### Accessibility Audit
```bash
# Using axe-core
npx playwright test tests/a11y/

# Lighthouse CI
npx lhci autorun
```

## Test Templates

### Basic E2E Test
```typescript
import { test, expect } from '@playwright/test';

test('user can search for products', async ({ page }) => {
  // Navigate
  await page.goto('http://localhost:8080');

  // Interact
  await page.fill('[data-testid="search-input"]', '50ml 용기');
  await page.click('[data-testid="search-button"]');

  // Assert
  await expect(page.locator('[data-testid="results"]')).toBeVisible();
  await expect(page.locator('.product-card')).toHaveCount(5);
});
```

### Visual Regression
```typescript
test('homepage looks correct', async ({ page }) => {
  await page.goto('http://localhost:8080');
  await expect(page).toHaveScreenshot('homepage.png');
});
```

### Accessibility Test
```typescript
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('should not have accessibility violations', async ({ page }) => {
  await page.goto('http://localhost:8080');

  const accessibilityScanResults = await new AxeBuilder({ page })
    .analyze();

  expect(accessibilityScanResults.violations).toEqual([]);
});
```

### Performance Test
```typescript
test('page loads within 3 seconds', async ({ page }) => {
  const startTime = Date.now();
  await page.goto('http://localhost:8080');
  await page.waitForLoadState('networkidle');
  const loadTime = Date.now() - startTime;

  expect(loadTime).toBeLessThan(3000);
});
```

## Page Object Model

```typescript
// pages/SearchPage.ts
export class SearchPage {
  constructor(private page: Page) {}

  async search(query: string) {
    await this.page.fill('[data-testid="search-input"]', query);
    await this.page.click('[data-testid="search-button"]');
  }

  async getResults() {
    return await this.page.locator('.product-card').count();
  }
}

// tests/search.spec.ts
import { SearchPage } from '../pages/SearchPage';

test('search works', async ({ page }) => {
  const searchPage = new SearchPage(page);
  await page.goto('http://localhost:8080');
  await searchPage.search('bottle');
  expect(await searchPage.getResults()).toBeGreaterThan(0);
});
```

## User Flows

### Login Flow
```typescript
test('complete login flow', async ({ page }) => {
  await page.goto('http://localhost:8080/login');
  await page.fill('#email', 'user@example.com');
  await page.fill('#password', 'password123');
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL('http://localhost:8080/dashboard');
});
```

### Search & Filter Flow
```typescript
test('search and filter products', async ({ page }) => {
  await page.goto('http://localhost:8080');

  // Search
  await page.fill('[data-testid="search"]', '용기');
  await page.click('[data-testid="submit"]');

  // Filter
  await page.check('[data-testid="filter-pet"]');
  await page.selectOption('[data-testid="size"]', '50ml');

  // Verify
  const results = await page.locator('.product-card').count();
  expect(results).toBeGreaterThan(0);
});
```

## Integration
- **testing-suite**: Part of comprehensive testing
- **deployment-automation**: Run E2E tests in CI/CD
- **rag-optimization**: Test search UI

## Key Files
- `tests/e2e/` - Playwright tests
- `playwright.config.ts` - Configuration
- `package.json` - Test scripts

## Best Practices
- Use data-testid for selectors
- Implement Page Object Model
- Run in CI/CD pipeline
- Test critical user paths
- Check accessibility
- Monitor performance
