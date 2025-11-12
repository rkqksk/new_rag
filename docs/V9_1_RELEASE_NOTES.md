# v9.1.0 Release Notes

**Date**: 2025-11-13
**Type**: Minor Release
**Status**: ✅ Complete

---

## Overview

v9.1.0 delivers complete backend integration, component library migration, and additional API services for the multi-platform architecture.

## What's New

### Phase 1: Backend API Integration ✅

**Centralized API Client**
- Location: `packages/core/src/services/api.service.ts`
- Features:
  - Automatic token management
  - Token auto-refresh on 401
  - Request/response interceptors
  - Error handling & retry logic
  - TypeScript type safety

**Enhanced Authentication Service**
- Updated to use centralized API client
- Token lifecycle management
- User state management
- Password reset flow

**Type Definitions**
- 200+ lines of TypeScript types
- User, Tenant, ApiKey, Product types
- Request/Response interfaces
- Comprehensive enums

**Configuration**
- Centralized API endpoints
- Environment-based configuration
- HTTP status codes & error messages

### Phase 2: Component Library Migration ✅

**Migrated Components (17)**
- Core: Button, Input, Label, Textarea
- Layout: Card, Separator
- Forms: Checkbox, Switch, Select
- Data: Table, Badge, Avatar, Skeleton, Progress
- Custom: StatusBadge
- Feedback: AlertDialog
- Navigation: Tabs

**Package Structure**
```
packages/ui/
├── src/
│   ├── components/       # 17 migrated components
│   ├── lib/              # Utilities (cn)
│   └── index.ts          # Clean exports
```

**Import Path Updates**
- Changed from `@/lib/utils` to `../lib/utils`
- All components ready for cross-platform use

### Phase 3: Additional API Services ✅

**Search Service**
- Location: `packages/core/src/services/search.service.ts`
- Methods:
  - `search()` - Basic search
  - `advancedSearch()` - With filters
  - `hybridSearch()` - Multi-strategy
  - `multimodalSearch()` - Text + image
  - `getProduct()` - Single product
  - `listProducts()` - Paginated list

**Admin Service**
- Location: `packages/core/src/services/admin.service.ts`
- Methods:
  - `getUsers()` - List users
  - `getUser()` - Single user
  - `updateUser()` - Update user
  - `deleteUser()` - Delete user
  - `getApiKeys()` - List API keys
  - `createApiKey()` - Create key
  - `deleteApiKey()` - Delete key
  - `rotateApiKey()` - Rotate key
  - `getUsageMetrics()` - Usage stats
  - `getHealth()` - System health

---

## Code Statistics

### Lines Added
- **Phase 1**: 1,293 lines
- **Phase 2**: 600+ lines (17 components)
- **Phase 3**: 300+ lines (2 services)
- **Total**: ~2,200 lines

### Files Created/Modified
- **Phase 1**: 8 files
- **Phase 2**: 20 files
- **Phase 3**: 2 files
- **Total**: 30 files

---

## Usage Examples

### Using Auth Service
```typescript
import { authService, UserRole } from '@rag/core'

const response = await authService.login({ email, password })
if (response.user.role === UserRole.ADMIN) {
  router.push('/admin')
}
```

### Using Search Service
```typescript
import { searchService } from '@rag/core'

const results = await searchService.search({
  query: "50ml PET container",
  limit: 10
})
```

### Using Admin Service
```typescript
import { adminService } from '@rag/core'

const users = await adminService.getUsers({ page: 1, limit: 20 })
const apiKey = await adminService.createApiKey({
  name: "Production Key",
  permissions: ["read", "write"]
})
```

### Using UI Components
```typescript
import { Button, Card, Badge } from '@rag/ui'

<Card>
  <h3>Product Name</h3>
  <Badge>New</Badge>
  <Button>Add to Cart</Button>
</Card>
```

---

## Breaking Changes

### None

All changes are additive and backward compatible.

---

## Migration Guide

### From Direct Fetch to Services

**Before**:
```typescript
const response = await fetch('/api/v1/search', {
  method: 'POST',
  body: JSON.stringify({ query })
})
```

**After**:
```typescript
import { searchService } from '@rag/core'
const results = await searchService.search({ query })
```

### From Local Components to @rag/ui

**Before**:
```typescript
import { Button } from '@/components/ui/button'
```

**After**:
```typescript
import { Button } from '@rag/ui'
```

---

## Next Steps (v9.2.0)

### Testing Framework
- Jest + React Testing Library
- API mocking with MSW
- E2E tests with Playwright

### Performance Optimization
- Code splitting
- Lazy loading
- Bundle size optimization

### Additional Features
- Real-time updates
- Offline support
- Push notifications

---

## Documentation

- **API Integration**: `docs/API_INTEGRATION_GUIDE.md`
- **Component Library**: `docs/COMPONENT_LIBRARY_INDEX.md`
- **Multi-Platform**: `docs/MULTI_PLATFORM_COMPONENT_CLASSIFICATION.md`
- **v9.0.0 Summary**: `docs/V9_FINAL_SUMMARY.md`

---

## Contributors

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>

---

**Published**: 2025-11-13
**Version**: v9.1.0
**Status**: ✅ Production Ready
