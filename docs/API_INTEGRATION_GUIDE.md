# API Integration Guide - v9.1.0

**Version**: v9.1.0
**Date**: 2025-11-13
**Status**: Phase 1 Complete

---

## Overview

This guide explains how to use the new centralized API client in the RAG Enterprise multi-platform architecture.

## What's New in v9.1.0

### ✅ Centralized API Client
- **Location**: `packages/core/src/services/api.service.ts`
- **Features**:
  - Automatic token management
  - Token refresh on 401
  - Request/response interceptors
  - Retry logic
  - Error handling

### ✅ Authentication Service
- **Location**: `packages/core/src/auth/authService.ts`
- **Methods**:
  - `login(credentials)` - User login
  - `register(data)` - User registration
  - `logout()` - User logout
  - `getCurrentUser()` - Get current user
  - `forgotPassword(data)` - Password reset request
  - `resetPassword(data)` - Reset password with token
  - `isAuthenticated()` - Check auth status
  - `getUser()` - Get stored user data

### ✅ Type Definitions
- **Location**: `packages/core/src/types/api.types.ts`
- **Includes**:
  - User, Tenant, ApiKey types
  - Request/Response interfaces
  - Enums for roles, statuses, plans

### ✅ API Configuration
- **Location**: `packages/core/src/config/api.config.ts`
- **Contains**:
  - Base URL configuration
  - API endpoints
  - HTTP status codes
  - Error messages

---

## Quick Start

### 1. Install Dependencies

The `@rag/core` package is already configured in the monorepo.

```bash
pnpm install
```

### 2. Environment Configuration

Create `.env.local` in your app:

```bash
# apps/web/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8001
```

### 3. Import and Use

```typescript
import { authService, UserRole } from '@rag/core'

// Login
const handleLogin = async (email: string, password: string) => {
  try {
    const response = await authService.login({ email, password })
    // Token is automatically stored
    // User is stored in localStorage

    // Redirect based on role
    if (response.user.role === UserRole.ADMIN) {
      router.push('/admin')
    }
  } catch (error) {
    console.error('Login failed:', error)
  }
}

// Check if authenticated
if (authService.isAuthenticated()) {
  const user = authService.getUser()
  console.log('Current user:', user)
}

// Logout
await authService.logout()
```

---

## API Client Usage

### Basic Usage

```typescript
import { apiService } from '@rag/core'

// GET request
const products = await apiService.get('/products')

// POST request
const newProduct = await apiService.post('/products', {
  name: 'Product Name',
  price: 100
})

// PUT request
await apiService.put(`/products/${id}`, {
  name: 'Updated Name'
})

// DELETE request
await apiService.delete(`/products/${id}`)
```

### With Types

```typescript
import { apiService, Product, ApiResponse } from '@rag/core'

const response = await apiService.get<Product[]>('/products')
if (response.data) {
  const products: Product[] = response.data
  console.log(products)
}
```

### Error Handling

```typescript
import { apiService, ApiError } from '@rag/core'

try {
  await apiService.post('/products', data)
} catch (error) {
  const apiError = error as ApiError
  console.error(apiError.code, apiError.message)

  if (apiError.details) {
    console.error('Details:', apiError.details)
  }
}
```

---

## Authentication Flow

### 1. Login
```typescript
const response = await authService.login({ email, password })
// Tokens and user data are automatically stored
```

### 2. Authenticated Requests
```typescript
// API client automatically includes token in Authorization header
const data = await apiService.get('/protected-endpoint')
```

### 3. Token Refresh
```typescript
// Automatic on 401 responses
// No manual intervention needed
```

### 4. Logout
```typescript
await authService.logout()
// Clears tokens and user data
// Redirects to login (if configured)
```

---

## API Endpoints

All endpoints are defined in `API_ENDPOINTS`:

```typescript
import { API_ENDPOINTS } from '@rag/core'

// Authentication
API_ENDPOINTS.AUTH.LOGIN          // /auth/login
API_ENDPOINTS.AUTH.REGISTER       // /auth/register
API_ENDPOINTS.AUTH.ME             // /auth/me

// SaaS
API_ENDPOINTS.SAAS.TENANTS.LIST   // /saas/tenants
API_ENDPOINTS.SAAS.API_KEYS.LIST  // /saas/api-keys

// Search
API_ENDPOINTS.SEARCH.BASIC        // /search
API_ENDPOINTS.SEARCH.ADVANCED     // /search/advanced
```

---

## Configuration

### API Base URL

```typescript
// Override default base URL
import { API_CONFIG } from '@rag/core'

// Use environment variable
process.env.NEXT_PUBLIC_API_URL

// Or configure directly (not recommended)
API_CONFIG.BASE_URL = 'https://api.example.com'
```

### Token Storage

Tokens are stored in localStorage:
- `rag_auth_token` - Access token
- `rag_refresh_token` - Refresh token
- `rag_user` - User data (JSON)

---

## Example: Login Page

```typescript
"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { authService, UserRole } from "@rag/core"

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError("")

    try {
      const response = await authService.login({ email, password })

      // Redirect based on role
      switch (response.user.role) {
        case UserRole.ADMIN:
          router.push("/admin")
          break
        case UserRole.CUSTOMER:
          router.push("/customer")
          break
        default:
          router.push("/")
      }
    } catch (err: any) {
      setError(err.message || "Login failed")
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleLogin}>
      <input type="email" value={email} onChange={e => setEmail(e.target.value)} />
      <input type="password" value={password} onChange={e => setPassword(e.target.value)} />
      {error && <p>{error}</p>}
      <button type="submit" disabled={loading}>
        {loading ? "Logging in..." : "Login"}
      </button>
    </form>
  )
}
```

---

## Backend API Structure

The backend API is located in `app/api/` and `src/api/`:

### Authentication Endpoints

**Location**: `src/api/routes/auth.py`

- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/refresh` - Refresh token
- `GET /api/v1/auth/me` - Get current user
- `POST /api/v1/auth/logout` - Logout

### SaaS Endpoints

**Location**: `src/api/v1/saas.py`

- Tenant management
- API key management
- Subscription management
- Usage tracking

### Search Endpoints

**Location**: `app/api/v1/search.py`

- Basic search
- Advanced search
- Hybrid search
- Multimodal search

---

## Testing

### Manual Testing

1. Start backend:
```bash
./scripts/deploy-optimized.sh development
```

2. Start frontend:
```bash
cd apps/web
pnpm dev
```

3. Open http://localhost:3000/login

4. Test login with credentials

### Automated Testing (TODO)

- Unit tests for API client
- Integration tests for auth flow
- E2E tests for complete flows

---

## Next Steps

### Phase 2: Component Migration
- Move common components to `@rag/ui`
- Create platform-specific variants
- Implement design tokens

### Phase 3: Testing
- Jest + React Testing Library
- E2E tests with Playwright
- API mocking with MSW

### Phase 4: Advanced Features
- Real-time updates with Socket.IO
- Offline support with Service Workers
- Push notifications

---

## Troubleshooting

### "Module not found: @rag/core"

```bash
# Ensure packages are linked
pnpm install

# Restart dev server
pnpm dev
```

### "Cannot read property 'data' of undefined"

Check that your backend is running and accessible:

```bash
curl http://localhost:8001/health
```

### "401 Unauthorized"

Check that tokens are being sent:

```javascript
// Check localStorage
console.log(localStorage.getItem('rag_auth_token'))

// Check if authenticated
console.log(authService.isAuthenticated())
```

### CORS Errors

Ensure backend CORS is configured:

```python
# app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## API Client Features

### ✅ Implemented
- Token management
- Auto-refresh on 401
- Error handling
- Request interceptors
- Response interceptors

### 🔜 Coming Soon
- Request queuing during refresh
- Retry with exponential backoff
- Request cancellation
- Upload progress tracking
- Download progress tracking

---

## Support

For questions or issues:
- Check `docs/V9_FINAL_SUMMARY.md`
- Check `docs/COMPONENT_IMPLEMENTATION_GUIDE.md`
- Review backend API docs: http://localhost:8001/api/v1/docs

---

**Updated**: 2025-11-13
**Version**: v9.1.0 Phase 1
**Status**: ✅ Backend Integration Complete
