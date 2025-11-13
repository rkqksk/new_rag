# v9.2.0 Testing Framework Guide

**Date**: 2025-11-13
**Version**: v9.2.0
**Status**: ✅ Complete

---

## Overview

v9.2.0 establishes a comprehensive testing framework for the RAG Enterprise platform with Jest, React Testing Library, and best practices for testing monorepo packages.

---

## Testing Stack

### Core Technologies
- **Jest**: Test runner and assertion library
- **ts-jest**: TypeScript support for Jest
- **React Testing Library**: Component testing for React
- **jest-environment-jsdom**: DOM environment for React tests

### Coverage Requirements
- **Branches**: 70%
- **Functions**: 70%
- **Lines**: 70%
- **Statements**: 70%

---

## Project Structure

```
new_rag/
├── packages/
│   └── core/
│       ├── jest.config.js                          # Jest config for Node
│       ├── src/
│       │   └── services/
│       │       └── __tests__/                      # Unit tests
│       │           ├── auth.service.test.ts
│       │           ├── search.service.test.ts
│       │           └── admin.service.test.ts
│       └── package.json                            # Test scripts
└── apps/
    └── web/
        ├── jest.config.js                          # Jest config for Next.js
        ├── jest.setup.js                           # Test environment setup
        └── package.json                            # Test scripts
```

---

## Configuration

### packages/core/jest.config.js

```javascript
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/src'],
  testMatch: ['**/__tests__/**/*.test.ts', '**/?(*.)+(spec|test).ts'],
  transform: {
    '^.+\\.tsx?$': 'ts-jest',
  },
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/index.ts',
  ],
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70,
    },
  },
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
}
```

**Key Features**:
- ts-jest preset for TypeScript support
- Node environment for server-side code
- 70% coverage threshold across all metrics
- Path mapping for `@/` imports

### apps/web/jest.config.js

```javascript
const nextJest = require('next/jest')

const createJestConfig = nextJest({
  // Provide the path to your Next.js app to load next.config.js and .env files
  dir: './',
})

const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testEnvironment: 'jest-environment-jsdom',
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
    '^@rag/core$': '<rootDir>/../../packages/core/src/index.ts',
    '^@rag/ui$': '<rootDir>/../../packages/ui/src/index.ts',
  },
  collectCoverageFrom: [
    'app/**/*.{js,jsx,ts,tsx}',
    'components/**/*.{js,jsx,ts,tsx}',
    '!**/*.d.ts',
    '!**/node_modules/**',
    '!**/.next/**',
  ],
  testMatch: [
    '**/__tests__/**/*.test.[jt]s?(x)',
    '**/?(*.)+(spec|test).[jt]s?(x)',
  ],
}

module.exports = createJestConfig(customJestConfig)
```

**Key Features**:
- Next.js integration with `next/jest`
- jsdom environment for React component testing
- Module name mapping for workspace packages
- Automatic Next.js config loading

### apps/web/jest.setup.js

```javascript
import '@testing-library/jest-dom'

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter() {
    return {
      push: jest.fn(),
      replace: jest.fn(),
      prefetch: jest.fn(),
      back: jest.fn(),
      pathname: '/',
      query: {},
      asPath: '/',
    }
  },
  useSearchParams() {
    return new URLSearchParams()
  },
  usePathname() {
    return '/'
  },
}))

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
}
global.localStorage = localStorageMock as Storage

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
})
```

**Key Features**:
- Testing Library Jest-DOM matchers
- Next.js router mocks
- localStorage mock for browser storage
- matchMedia mock for responsive testing

---

## Test Examples

### 1. Service Unit Tests (packages/core)

#### auth.service.test.ts

```typescript
import { authService } from '../auth/authService'
import { apiService } from '../services/api.service'

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

      (apiService.post as jest.Mock).mockResolvedValue(mockResponse)

      const result = await authService.login({
        email: 'test@example.com',
        password: 'password123',
      })

      expect(apiService.post).toHaveBeenCalledWith('/auth/login', {
        email: 'test@example.com',
        password: 'password123',
      })
      expect(apiService.setToken).toHaveBeenCalledWith('test-token')
      expect(apiService.setRefreshToken).toHaveBeenCalledWith('test-refresh-token')
      expect(result).toEqual(mockResponse.data)
    })

    it('should throw error on login failure', async () => {
      (apiService.post as jest.Mock).mockResolvedValue({ data: null })

      await expect(
        authService.login({ email: 'test@example.com', password: 'wrong' })
      ).rejects.toThrow('Login failed')
    })
  })
})
```

**Testing Pattern**:
- Mock external dependencies (apiService)
- Test both success and failure cases
- Verify function calls with correct arguments
- Assert expected return values

#### search.service.test.ts

```typescript
import { searchService } from '../search.service'
import { apiService } from '../api.service'
import type { SearchRequest, SearchResponse } from '../../types/api.types'

jest.mock('../api.service')

describe('SearchService', () => {
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

      (apiService.post as jest.Mock).mockResolvedValue({ data: mockResponse })

      const result = await searchService.search(mockRequest)

      expect(apiService.post).toHaveBeenCalledWith('/search/', mockRequest)
      expect(result).toEqual(mockResponse)
      expect(result.results).toHaveLength(1)
      expect(result.results[0].similarity).toBe(0.95)
    })
  })
})
```

**Testing Pattern**:
- Type-safe mocks with TypeScript
- Test API integration points
- Verify response structure
- Assert data transformations

### 2. Component Tests (apps/web)

Future component tests will use React Testing Library:

```typescript
import { render, screen, fireEvent } from '@testing-library/react'
import { Button } from '@rag/ui'

describe('Button', () => {
  it('should render button with text', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByText('Click me')).toBeInTheDocument()
  })

  it('should call onClick when clicked', () => {
    const handleClick = jest.fn()
    render(<Button onClick={handleClick}>Click me</Button>)

    fireEvent.click(screen.getByText('Click me'))
    expect(handleClick).toHaveBeenCalledTimes(1)
  })
})
```

---

## Running Tests

### Core Package

```bash
# Run all tests
cd packages/core
pnpm test

# Watch mode
pnpm test:watch

# With coverage
pnpm test:coverage
```

### Web App

```bash
# Run all tests
cd apps/web
pnpm test

# Watch mode
pnpm test:watch

# With coverage
pnpm test:coverage
```

### From Root (All Packages)

```bash
# Run all tests in monorepo
pnpm -r test

# Run tests with coverage
pnpm -r test:coverage
```

---

## Best Practices

### 1. Test Organization

```
src/
├── services/
│   ├── auth.service.ts
│   ├── search.service.ts
│   └── __tests__/
│       ├── auth.service.test.ts
│       └── search.service.test.ts
```

- Keep tests close to source files
- Use `__tests__/` directories
- Name test files with `.test.ts` or `.spec.ts` suffix

### 2. Test Structure

```typescript
describe('ServiceName', () => {
  beforeEach(() => {
    // Setup before each test
    jest.clearAllMocks()
  })

  describe('methodName', () => {
    it('should handle success case', async () => {
      // Arrange
      const input = { ... }
      const expected = { ... }

      // Act
      const result = await service.method(input)

      // Assert
      expect(result).toEqual(expected)
    })

    it('should handle error case', async () => {
      // Test error scenarios
    })
  })
})
```

### 3. Mocking Strategy

**Mock External Dependencies**:
```typescript
jest.mock('../services/api.service')
```

**Mock Return Values**:
```typescript
(apiService.post as jest.Mock).mockResolvedValue({ data: mockData })
```

**Verify Calls**:
```typescript
expect(apiService.post).toHaveBeenCalledWith('/endpoint', payload)
expect(apiService.post).toHaveBeenCalledTimes(1)
```

### 4. Coverage Guidelines

- **70% minimum** across all metrics
- **100% for critical paths**: Authentication, payment, data access
- **Don't test framework code**: React hooks, Next.js internals
- **Focus on business logic**: Services, utilities, custom hooks

---

## CI/CD Integration

### GitHub Actions (Future)

```yaml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: pnpm/action-setup@v2
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'pnpm'

      - run: pnpm install
      - run: pnpm -r test:coverage

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## Troubleshooting

### Common Issues

#### 1. Module Not Found

**Error**: `Cannot find module '@rag/core'`

**Solution**: Check `moduleNameMapper` in jest.config.js:
```javascript
moduleNameMapper: {
  '^@rag/core$': '<rootDir>/../../packages/core/src/index.ts',
}
```

#### 2. TypeScript Errors

**Error**: `Type error: Cannot find name 'jest'`

**Solution**: Install @types/jest:
```bash
pnpm add -D @types/jest
```

#### 3. Next.js Mocking Issues

**Error**: `useRouter is not a function`

**Solution**: Ensure jest.setup.js is loaded in jest.config.js:
```javascript
setupFilesAfterEnv: ['<rootDir>/jest.setup.js']
```

---

## Test Statistics

### packages/core

- **Test Files**: 3
- **Test Suites**: 13
- **Test Cases**: 30+
- **Coverage Target**: 70%

**Test Files**:
1. `auth.service.test.ts` - 9 tests
2. `search.service.test.ts` - 11 tests
3. `admin.service.test.ts` - 12 tests

### Services Covered

✅ **Authentication Service**
- Login (success/failure)
- Logout (success/failure)
- isAuthenticated
- getUser

✅ **Search Service**
- Basic search
- Advanced search with filters
- Hybrid search
- Multimodal search
- Single product retrieval
- Product listing with pagination

✅ **Admin Service**
- User management (CRUD)
- API key management (CRUD + rotate)
- Usage metrics
- System health checks

---

## Next Steps (v9.3.0)

### Additional Tests Needed

1. **Component Tests**
   - Button, Input, Card components
   - Form validation
   - User interactions

2. **Integration Tests**
   - API endpoint integration
   - Authentication flow
   - Search workflow

3. **E2E Tests**
   - User registration flow
   - Login to search journey
   - Admin dashboard operations

### Testing Tools to Add

- **Playwright**: E2E testing
- **MSW**: API mocking for integration tests
- **Storybook**: Component visual testing

---

## Resources

- **Jest Documentation**: https://jestjs.io/
- **React Testing Library**: https://testing-library.com/react
- **ts-jest**: https://kulshekhar.github.io/ts-jest/
- **Next.js Testing**: https://nextjs.org/docs/testing

---

**Version**: v9.2.0
**Date**: 2025-11-13
**Status**: ✅ Testing Framework Complete

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
