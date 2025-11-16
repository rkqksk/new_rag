# Frontend + File Structure Integration Plan

**Version**: v1.0.0
**Date**: 2025-11-15
**Status**: Ready for Implementation
**Estimated Duration**: 12 weeks
**Aligned with**: Claude Code Best Practices, v10.0.0 "Unified" Architecture

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Claude Code Optimized Structure](#1-claude-code-optimized-structure)
3. [Frontend Consolidation Plan](#2-frontend-consolidation-plan)
4. [File Structure Optimization](#3-file-structure-optimization)
5. [Monorepo Configuration](#4-monorepo-configuration)
6. [Claude Code Integration](#5-claude-code-integration)
7. [Migration Execution Plan](#6-migration-execution-plan)
8. [Risk Mitigation](#7-risk-mitigation)
9. [Success Metrics](#8-success-metrics)
10. [Appendix: Scripts & Templates](#appendix-scripts--templates)

---

## Executive Summary

### Current State Analysis

**Frontend Fragmentation:**
- **9 HTML files** in `frontend/` directory (legacy production features)
- **frontend-v2/** - Next.js app (~85% duplicate of apps/web)
- **frontend-next/** - Abandoned experimental directory
- **apps/web/** - Modern Next.js 14 app (partial implementation)
- **mobile/** - Standalone React Native (not integrated with monorepo)
- **apps/mobile/** - Monorepo mobile app (partially implemented)
- **apps/pwa/** - PWA app using Vite

**Code Duplication:**
- 85% overlap between frontend-v2/ and apps/web/
- Shared logic in frontend/js/ not reused by React apps
- Dashboard components duplicated instead of using packages/ui
- Mobile code split between mobile/ and apps/mobile/

**Current Structure Issues:**
- 35+ top-level directories (confusing navigation)
- Duplicate backend code (app/, src/, backend/)
- Inconsistent import patterns
- Large .claudeignore but missing key patterns
- No clear separation between archived and active code

### Target State (v10.0.0 "Unified")

**Clean Monorepo Architecture:**
```
rag-enterprise/
├── apps/                     # Applications (4)
│   ├── web/                  # Next.js 14 web app
│   ├── mobile/               # React Native + Expo
│   ├── pwa/                  # Vite PWA
│   └── api/                  # Cloudflare Workers (future)
├── packages/                 # Shared packages (5)
│   ├── ui/                   # React UI components
│   ├── core/                 # Business logic
│   ├── mobile-ui/            # React Native components
│   ├── config/               # Shared configs
│   └── types/                # TypeScript types
├── backend/                  # Unified Python backend
├── docs/                     # Documentation
├── scripts/                  # Build/deployment scripts
└── .archived/                # Deprecated code
```

**Key Improvements:**
- **90% component reuse** from @rag/ui
- **60% logic reuse** from @rag/core
- **0 HTML files** in production (all migrated to React)
- **Single mobile codebase** (apps/mobile)
- **30% fewer total lines** of code
- **Sub-5min builds** with Turborepo caching

### Migration Phases

| Phase | Duration | Description | Deliverable |
|-------|----------|-------------|-------------|
| **Phase 1** | Week 1 | Archive deprecated code | Clean directory structure |
| **Phase 2** | Week 1-2 | Move components to packages/ui | Shared component library |
| **Phase 3** | Week 3-6 | Migrate HTML → React (6 features) | Modern React apps |
| **Phase 4** | Week 7-8 | Extract shared logic to packages/core | Reusable services |
| **Phase 5** | Week 9-10 | Optimize mobile consolidation | Single mobile app |
| **Phase 6** | Week 11 | Optimize Claude Code integration | Enhanced DX |
| **Phase 7** | Week 12 | Testing & validation | Production-ready |

---

## 1. Claude Code Optimized Structure

### 1.1 Ideal Directory Structure

```
rag-enterprise/
├── .archived/                          # Deprecated code (ignored by Claude)
│   ├── frontend-v2/                    # 85% duplicate of apps/web
│   ├── frontend-next/                  # Abandoned experiment
│   ├── mobile/                         # Legacy standalone mobile
│   └── README.md                       # Archive documentation
│
├── .claude/                            # Claude Code configuration
│   ├── commands/                       # 20+ slash commands
│   │   ├── README.md                   # Command documentation
│   │   ├── excel.md                    # Document processing
│   │   ├── pdf.md
│   │   ├── canvas.md                   # Design commands
│   │   ├── theme.md
│   │   ├── migrate-html.md             # 🆕 Migration helper
│   │   ├── test-rag.md                 # 🆕 RAG testing
│   │   └── validate-mobile.md          # 🆕 Mobile validation
│   ├── agents/                         # Custom agents (optional)
│   │   ├── frontend-migration.md       # 🆕 HTML → React migration agent
│   │   └── component-extractor.md      # 🆕 Component extraction agent
│   ├── mcp.json                        # MCP server config
│   ├── scripts/                        # Utility scripts
│   └── settings.local.json             # Local settings
│
├── apps/                               # Applications
│   ├── web/                            # Next.js 14 web application
│   │   ├── src/
│   │   │   ├── app/                    # App router pages
│   │   │   │   ├── (auth)/             # Auth routes group
│   │   │   │   │   ├── login/
│   │   │   │   │   └── register/
│   │   │   │   ├── (customer)/         # Customer routes
│   │   │   │   │   ├── search/         # 🆕 From chat.html
│   │   │   │   │   └── profile/        # 🆕 From profile.html
│   │   │   │   ├── (admin)/            # Admin routes
│   │   │   │   │   ├── dashboard/      # Enhanced from dashboard.html
│   │   │   │   │   ├── rag/            # 🆕 From rag_dashboard.html
│   │   │   │   │   └── analytics/      # 🆕 From analytics-dashboard.html
│   │   │   │   └── (super-admin)/      # Super admin routes
│   │   │   │       ├── realtime/       # 🆕 From realtime-demo.html
│   │   │   │       └── streaming/      # 🆕 From streaming-demo.html
│   │   │   ├── components/             # Page-specific components
│   │   │   ├── hooks/                  # Custom React hooks
│   │   │   ├── lib/                    # Utilities
│   │   │   └── styles/                 # Global styles
│   │   ├── public/                     # Static assets
│   │   ├── package.json
│   │   ├── next.config.js
│   │   ├── tsconfig.json
│   │   └── jest.config.js
│   │
│   ├── mobile/                         # React Native mobile app
│   │   ├── src/
│   │   │   ├── screens/                # Screen components
│   │   │   │   ├── auth/
│   │   │   │   ├── search/
│   │   │   │   └── profile/
│   │   │   ├── navigation/             # Navigation config
│   │   │   ├── hooks/                  # Mobile-specific hooks
│   │   │   └── lib/                    # Mobile utilities
│   │   ├── app.json                    # Expo config
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   ├── pwa/                            # Progressive Web App
│   │   ├── src/
│   │   │   ├── pages/
│   │   │   ├── components/
│   │   │   └── service-worker.ts       # PWA service worker
│   │   ├── public/
│   │   ├── package.json
│   │   ├── vite.config.ts
│   │   └── tsconfig.json
│   │
│   └── api/                            # Edge API workers (future)
│       ├── src/
│       │   ├── handlers/
│       │   └── middleware/
│       └── package.json
│
├── packages/                           # Shared packages
│   ├── ui/                             # React UI component library
│   │   ├── src/
│   │   │   ├── components/             # 20+ base components (current)
│   │   │   │   ├── button.tsx
│   │   │   │   ├── card.tsx
│   │   │   │   ├── input.tsx
│   │   │   │   └── ...
│   │   │   ├── dashboard/              # 🆕 Dashboard components (7+)
│   │   │   │   ├── sidebar.tsx         # 🆕 From apps/web
│   │   │   │   ├── navbar.tsx          # 🆕 From apps/web
│   │   │   │   ├── stats-card.tsx      # 🆕 From apps/web
│   │   │   │   ├── collection-card.tsx # 🆕 From apps/web
│   │   │   │   ├── product-card.tsx    # 🆕 From apps/web
│   │   │   │   ├── search-bar.tsx      # 🆕 From apps/web
│   │   │   │   └── filters.tsx         # 🆕 From apps/web
│   │   │   ├── hooks/                  # UI-specific hooks
│   │   │   ├── styles/                 # Component styles
│   │   │   └── index.ts                # Barrel exports
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   └── README.md
│   │
│   ├── core/                           # Business logic & services
│   │   ├── src/
│   │   │   ├── api/                    # API client
│   │   │   │   ├── client.ts           # Centralized API client
│   │   │   │   ├── auth.ts             # Auth endpoints
│   │   │   │   ├── search.ts           # Search endpoints
│   │   │   │   ├── admin.ts            # Admin endpoints
│   │   │   │   └── websocket.ts        # WebSocket client
│   │   │   ├── services/               # Business logic services
│   │   │   │   ├── auth.service.ts     # Enhanced from frontend/js/auth.js
│   │   │   │   ├── offline.service.ts  # 🆕 From offline-storage.js
│   │   │   │   ├── i18n.service.ts     # 🆕 From i18n.js
│   │   │   │   ├── recommendations.service.ts # 🆕 From recommendations.js
│   │   │   │   ├── notifications.service.ts   # 🆕 From notifications.js
│   │   │   │   └── search.service.ts   # Search business logic
│   │   │   ├── utils/                  # Shared utilities
│   │   │   │   ├── validation.ts
│   │   │   │   ├── formatting.ts
│   │   │   │   └── storage.ts
│   │   │   ├── constants/              # Shared constants
│   │   │   └── index.ts
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   └── README.md
│   │
│   ├── mobile-ui/                      # React Native UI components
│   │   ├── src/
│   │   │   ├── components/             # Native-compatible components
│   │   │   ├── hooks/
│   │   │   └── index.ts
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   ├── config/                         # Shared configurations
│   │   ├── eslint/
│   │   ├── typescript/
│   │   ├── jest/
│   │   └── package.json
│   │
│   └── types/                          # Shared TypeScript types
│       ├── src/
│       │   ├── api.ts                  # API types
│       │   ├── models.ts               # Data models
│       │   ├── components.ts           # Component prop types
│       │   └── index.ts
│       ├── package.json
│       └── tsconfig.json
│
├── backend/                            # Unified Python backend
│   ├── api/
│   │   ├── v1/                         # Stable APIs
│   │   └── v2/                         # Experimental APIs
│   ├── core/                           # Core infrastructure
│   ├── services/                       # Business logic
│   ├── middleware/                     # Middleware
│   ├── models/                         # Pydantic models
│   └── main.py                         # FastAPI app
│
├── docs/                               # Documentation
│   ├── architecture/                   # Architecture docs
│   │   ├── SYSTEM_OVERVIEW.md
│   │   ├── BACKEND_ARCHITECTURE.md
│   │   └── FRONTEND_ARCHITECTURE.md
│   ├── api/                            # API documentation
│   │   ├── V1_ENDPOINTS.md
│   │   └── V2_ENDPOINTS.md
│   ├── guides/                         # How-to guides
│   │   ├── QUICK_START.md
│   │   ├── LOCAL_SETUP.md
│   │   ├── DEPLOYMENT.md
│   │   ├── TESTING.md
│   │   └── TROUBLESHOOTING.md
│   ├── integration/                    # Integration plans
│   │   ├── FRONTEND_FILE_STRUCTURE_PLAN.md # This document
│   │   ├── BACKEND_MIGRATION_PLAN.md
│   │   └── V10_INTEGRATION_PLAN.md
│   ├── reference/                      # Technical reference
│   │   ├── SYMBOLS.md                  # Claude symbol system
│   │   └── COMPONENT_LIBRARY.md
│   └── logs/                           # Version logs
│       ├── CHANGELOG.md
│       └── PROGRESS.md
│
├── scripts/                            # Build & deployment scripts
│   ├── migration/                      # Migration scripts
│   │   ├── 00_archive_deprecated.sh    # 🆕 Phase 1
│   │   ├── 01_move_components.sh       # 🆕 Phase 2
│   │   ├── 02_migrate_chat.sh          # 🆕 Phase 3
│   │   ├── 03_migrate_realtime.sh      # 🆕 Phase 3
│   │   ├── 04_migrate_profile.sh       # 🆕 Phase 3
│   │   ├── 05_migrate_rag_dashboard.sh # 🆕 Phase 3
│   │   ├── 06_migrate_dashboard.sh     # 🆕 Phase 3
│   │   ├── 07_migrate_streaming.sh     # 🆕 Phase 3
│   │   ├── 08_extract_services.sh      # 🆕 Phase 4
│   │   ├── 09_consolidate_mobile.sh    # 🆕 Phase 5
│   │   └── 10_validate_migration.sh    # 🆕 Phase 7
│   ├── deployment/                     # Deployment scripts
│   │   ├── deploy-optimized.sh
│   │   └── restart-all.sh
│   ├── testing/                        # Testing utilities
│   │   ├── test-optimized.sh
│   │   └── validate-claude-system.sh
│   └── utils/                          # General utilities
│       ├── generate-types.sh
│       └── analyze-bundle.sh
│
├── .archived/                          # Archived code (gitignored, claudeignored)
├── .github/                            # GitHub config
│   └── workflows/                      # CI/CD workflows
├── .gitignore                          # Git ignore patterns
├── .claudeignore                       # Claude ignore patterns (enhanced)
├── package.json                        # Root package.json
├── pnpm-workspace.yaml                 # PNPM workspace config
├── turbo.json                          # Turborepo config
├── tsconfig.json                       # Root TypeScript config
├── CLAUDE.md                           # Claude quick reference
├── README.md                           # Project overview
└── PROGRESS.md                         # Version history
```

### 1.2 Token Efficiency Optimization

**Directory Consolidation:**
- **Before**: 35+ top-level directories
- **After**: 12 top-level directories
- **Token Savings**: ~40% on directory listings

**Code Organization:**
- Feature-based structure in apps/
- Shared packages for reusable code
- Clear separation of concerns
- Fewer duplicate files to index

**Claude Code Benefits:**
1. **Faster file navigation** - Clear hierarchy
2. **Better code search** - Organized by feature
3. **Efficient symbol lookup** - MCP serena can index cleanly
4. **Reduced context switching** - Related files grouped together

### 1.3 MCP Integration Optimization

**Filesystem Server:**
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/rkqksk/projects/new_rag"],
      "allowedDirectories": [
        "/home/rkqksk/projects/new_rag/apps",
        "/home/rkqksk/projects/new_rag/packages",
        "/home/rkqksk/projects/new_rag/backend",
        "/home/rkqksk/projects/new_rag/docs",
        "/home/rkqksk/projects/new_rag/scripts"
      ],
      "excludePatterns": [
        "**/.archived/**",
        "**/node_modules/**",
        "**/.next/**",
        "**/dist/**",
        "**/.turbo/**"
      ]
    }
  }
}
```

**GitHub Server:**
- Already configured
- Unlimited for public repos
- Use for PR creation, issue tracking

**Serena Server:**
- Code navigation and symbol search
- Optimized for TypeScript/Python monorepo
- Memory system for architectural decisions

---

## 2. Frontend Consolidation Plan

### 2.1 Phase 1: Archive Deprecated Code (Week 1)

**Goal**: Clean directory structure by archiving duplicate/abandoned code

**Directories to Archive:**
```
frontend-v2/          → .archived/frontend-v2/
frontend-next/        → .archived/frontend-next/
mobile/ (standalone)  → .archived/mobile-standalone/
```

**Action Items:**

1. **Create Archive Structure**
   ```bash
   mkdir -p .archived/{frontend-v2,frontend-next,mobile-standalone}
   ```

2. **Document Archive Decisions**
   ```bash
   # Create .archived/README.md with:
   # - Why each directory was archived
   # - Date of archival
   # - Migration path (if any)
   # - Restoration instructions (if needed)
   ```

3. **Move Directories**
   ```bash
   mv frontend-v2 .archived/
   mv frontend-next .archived/
   mv mobile .archived/mobile-standalone
   ```

4. **Update .gitignore and .claudeignore**
   ```bash
   # Add to both files:
   .archived/
   ```

5. **Validate Archive**
   ```bash
   # Ensure no import references remain
   grep -r "frontend-v2" apps/ packages/
   grep -r "frontend-next" apps/ packages/
   grep -r "mobile" apps/ packages/ | grep -v "apps/mobile"
   ```

**Success Criteria:**
- ✅ 3 directories archived
- ✅ .archived/README.md created
- ✅ No broken imports
- ✅ Git status clean (archived dirs ignored)
- ✅ ~30% reduction in top-level directories

**Rollback Plan:**
```bash
# If needed, restore:
mv .archived/frontend-v2 ./
mv .archived/frontend-next ./
mv .archived/mobile-standalone ./mobile
```

---

### 2.2 Phase 2: Move Dashboard Components to packages/ui (Week 1-2)

**Goal**: Extract 7 dashboard components from apps/web to packages/ui for reuse

**Current State Analysis:**
```
apps/web/src/components/
├── Sidebar.tsx           # Used in all dashboards
├── Navbar.tsx            # Used in all dashboards
├── StatsCard.tsx         # Used in dashboard, admin
├── CollectionCard.tsx    # Used in dashboard
├── ProductCard.tsx       # Used in search (chat.html migration)
├── SearchBar.tsx         # Used in search, admin
└── Filters.tsx           # Used in search, admin
```

**Target Structure:**
```
packages/ui/src/dashboard/
├── sidebar.tsx           # Generic sidebar (parameterized)
├── navbar.tsx            # Generic navbar (parameterized)
├── stats-card.tsx        # Reusable stats display
├── collection-card.tsx   # Collection display
├── product-card.tsx      # Product display
├── search-bar.tsx        # Search input
├── filters.tsx           # Filter controls
└── index.ts              # Barrel export
```

**Migration Checklist:**

**Step 1: Prepare packages/ui**
```bash
cd packages/ui
mkdir -p src/dashboard
touch src/dashboard/index.ts
```

**Step 2: Parameterize Components**

For each component, ensure it's **brand-agnostic**:

```typescript
// Before (apps/web)
export function Sidebar() {
  return <div className="sidebar">
    <h1>RAG Enterprise</h1> {/* Hardcoded */}
    {/* ... */}
  </div>
}

// After (packages/ui)
interface SidebarProps {
  brandName?: string;
  logo?: string;
  menuItems: MenuItem[];
  onNavigate?: (path: string) => void;
}

export function Sidebar({
  brandName = "RAG Enterprise",
  logo,
  menuItems,
  onNavigate
}: SidebarProps) {
  return <div className="sidebar">
    {logo ? <img src={logo} alt={brandName} /> : <h1>{brandName}</h1>}
    {/* Parameterized menu */}
  </div>
}
```

**Step 3: Move Files**
```bash
# For each component:
mv apps/web/src/components/Sidebar.tsx packages/ui/src/dashboard/sidebar.tsx
mv apps/web/src/components/Navbar.tsx packages/ui/src/dashboard/navbar.tsx
# ... (repeat for all 7 components)
```

**Step 4: Update Imports in apps/web**
```typescript
// Before
import { Sidebar } from '@/components/Sidebar'

// After
import { Sidebar } from '@rag/ui/dashboard'
```

**Step 5: Add Barrel Export**
```typescript
// packages/ui/src/dashboard/index.ts
export { Sidebar } from './sidebar'
export { Navbar } from './navbar'
export { StatsCard } from './stats-card'
export { CollectionCard } from './collection-card'
export { ProductCard } from './product-card'
export { SearchBar } from './search-bar'
export { Filters } from './filters'

// Export types
export type { SidebarProps } from './sidebar'
export type { NavbarProps } from './navbar'
// ... (all component prop types)
```

**Step 6: Update packages/ui/src/index.ts**
```typescript
// packages/ui/src/index.ts
export * from './components'
export * from './dashboard'  // 🆕 Add dashboard exports
```

**Step 7: Test Component Reuse**
```typescript
// Test in apps/web
import { Sidebar, Navbar, ProductCard } from '@rag/ui/dashboard'

// Should work in apps/mobile (React Native compatible variants)
import { ProductCard } from '@rag/mobile-ui/dashboard'

// Should work in apps/pwa
import { SearchBar } from '@rag/ui/dashboard'
```

**Success Criteria:**
- ✅ 7 components moved to packages/ui/dashboard
- ✅ All components parameterized (brand-agnostic)
- ✅ apps/web uses @rag/ui imports
- ✅ No broken imports
- ✅ Component tests updated and passing
- ✅ Storybook updated (if exists)

**Testing Strategy:**

1. **Unit Tests** (packages/ui/src/dashboard/__tests__)
   ```typescript
   // sidebar.test.tsx
   import { render, screen } from '@testing-library/react'
   import { Sidebar } from '../sidebar'

   describe('Sidebar', () => {
     it('renders with default brand name', () => {
       render(<Sidebar menuItems={[]} />)
       expect(screen.getByText('RAG Enterprise')).toBeInTheDocument()
     })

     it('renders with custom brand name', () => {
       render(<Sidebar brandName="Custom Brand" menuItems={[]} />)
       expect(screen.getByText('Custom Brand')).toBeInTheDocument()
     })
   })
   ```

2. **Integration Tests** (apps/web)
   ```bash
   # Test apps/web still works with new imports
   cd apps/web
   pnpm test
   pnpm dev # Visual check
   ```

3. **Cross-Platform Tests** (apps/mobile, apps/pwa)
   ```bash
   # Ensure components work across platforms
   cd apps/mobile && pnpm test
   cd apps/pwa && pnpm test
   ```

---

### 2.3 Phase 3: Migrate Legacy Features (HTML → React) (Week 3-6)

**Goal**: Migrate 6 legacy HTML features to modern React applications

**Priority Order** (from REDESIGN_PLAN.md + complexity analysis):

| Priority | Feature | HTML File | Lines | Target Route | Complexity | Duration |
|----------|---------|-----------|-------|--------------|------------|----------|
| **P0** | Product Search | chat.html | 894 | apps/web/(customer)/search | High | 2 weeks |
| **P0** | Realtime Demo | realtime-demo.html | 498 | apps/web/(super-admin)/realtime | Medium | 1 week |
| **P1** | User Profile | profile.html | ~400 | apps/web/(customer)/profile | Low | 3 days |
| **P1** | RAG Dashboard | rag_dashboard.html | ~500 | apps/web/(admin)/rag | Medium | 1 week |
| **P2** | Dashboard Enhancements | dashboard.html | ~600 | apps/web/(admin)/dashboard | Low | 3 days |
| **P2** | Streaming Demo | streaming-demo.html | ~450 | apps/web/(super-admin)/streaming | Medium | 1 week |

**Notes**:
- login.html ✅ Already migrated
- register.html - Skip (lower priority, can use existing auth flow)
- analytics-dashboard.html - Skip (integrate into dashboard.html enhancements)

---

#### 2.3.1 P0: Migrate chat.html → apps/web/(customer)/search (Week 3-4)

**Complexity**: High (894 lines, complex UI, gallery, progressive loading)

**Feature Analysis:**
```html
<!-- chat.html key features -->
1. Search bar with auto-suggest
2. Collection selector (emoji indicator to remove)
3. Product cards with images
4. Image gallery modal
5. Progressive loading (infinite scroll)
6. Filters (category, material, capacity)
7. Offline support (localStorage)
8. Recommendations sidebar
9. Dark mode toggle (to remove)
10. i18n support (Korean/English)
```

**Component Mapping:**

```typescript
// apps/web/src/app/(customer)/search/page.tsx
import {
  SearchBar,
  Filters,
  ProductCard
} from '@rag/ui/dashboard'
import {
  useSearch,
  useCollections,
  useOfflineStorage
} from '@rag/core/hooks'

export default function SearchPage() {
  const { results, search, loading } = useSearch()
  const { collections } = useCollections()

  return (
    <div className="search-page">
      <SearchHeader />
      <SearchFilters />
      <ProductGrid results={results} loading={loading} />
      <RecommendationsSidebar />
    </div>
  )
}
```

**Detailed Component Breakdown:**

```
apps/web/src/app/(customer)/search/
├── page.tsx                    # Main search page
├── components/
│   ├── SearchHeader.tsx        # Search bar + collection selector
│   ├── SearchFilters.tsx       # Filters (from Filters component)
│   ├── ProductGrid.tsx         # Product cards grid
│   ├── ProductCard.tsx         # Single product (from packages/ui)
│   ├── ImageGallery.tsx        # Image gallery modal
│   ├── RecommendationsSidebar.tsx # Recommendations
│   └── EmptyState.tsx          # No results state
├── hooks/
│   ├── useSearch.ts            # Search logic
│   ├── useInfiniteScroll.ts    # Progressive loading
│   └── useImageGallery.ts      # Gallery state
└── __tests__/
    ├── SearchPage.test.tsx
    └── components/
```

**Dependency Extraction (HTML → React Hooks):**

```javascript
// frontend/js/auth.js → packages/core/src/services/auth.service.ts
// Already exists, enhance with:
export class AuthService {
  // Existing methods...

  getCurrentUser(): User | null {
    const token = this.getToken()
    if (!token) return null
    return parseJwt(token) // Decode JWT
  }

  isAuthenticated(): boolean {
    return !!this.getToken()
  }
}

// frontend/js/offline-storage.js → packages/core/src/services/offline.service.ts
export class OfflineStorageService {
  private dbName = 'rag-enterprise-offline'

  async saveSearchResults(query: string, results: Product[]) {
    // IndexedDB storage
  }

  async getOfflineResults(query: string): Promise<Product[]> {
    // Retrieve from IndexedDB
  }

  async syncPendingActions() {
    // Sync queue when online
  }
}

// frontend/js/recommendations.js → packages/core/src/services/recommendations.service.ts
export class RecommendationsService {
  async getRecommendations(productId: string): Promise<Product[]> {
    // Fetch from API
  }

  async trackUserAction(action: UserAction) {
    // Track for personalization
  }
}

// frontend/js/i18n.js → packages/core/src/services/i18n.service.ts
export class I18nService {
  private locale: Locale = 'ko'
  private translations: Record<Locale, Translations>

  setLocale(locale: Locale) {
    this.locale = locale
  }

  t(key: string): string {
    return this.translations[this.locale][key]
  }
}
```

**React Hooks Creation:**

```typescript
// apps/web/src/app/(customer)/search/hooks/useSearch.ts
import { searchService } from '@rag/core/services'

export function useSearch() {
  const [results, setResults] = useState<Product[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const search = useCallback(async (query: string, filters?: Filters) => {
    setLoading(true)
    try {
      const data = await searchService.search(query, filters)
      setResults(data.results)
    } catch (err) {
      setError(err as Error)
    } finally {
      setLoading(false)
    }
  }, [])

  return { results, search, loading, error }
}

// apps/web/src/app/(customer)/search/hooks/useInfiniteScroll.ts
export function useInfiniteScroll(callback: () => void) {
  const observerRef = useRef<IntersectionObserver>()

  useEffect(() => {
    observerRef.current = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) callback()
      },
      { threshold: 0.5 }
    )

    return () => observerRef.current?.disconnect()
  }, [callback])

  return observerRef
}
```

**Migration Script:**

```bash
#!/bin/bash
# scripts/migration/02_migrate_chat.sh

set -e

echo "🚀 Migrating chat.html → apps/web/(customer)/search"

# Create directory structure
mkdir -p apps/web/src/app/\(customer\)/search/{components,hooks,__tests__}

# Extract CSS (remove emojis, gradients)
echo "📝 Extracting and cleaning CSS..."
# Manual: Convert inline styles to design-system.css classes

# Create page component
cat > apps/web/src/app/\(customer\)/search/page.tsx << 'EOF'
import { SearchHeader } from './components/SearchHeader'
import { SearchFilters } from './components/SearchFilters'
import { ProductGrid } from './components/ProductGrid'
import { RecommendationsSidebar } from './components/RecommendationsSidebar'

export default function SearchPage() {
  return (
    <div className="container">
      <SearchHeader />
      <div className="flex gap-4">
        <aside className="w-64">
          <SearchFilters />
        </aside>
        <main className="flex-1">
          <ProductGrid />
        </main>
        <aside className="w-80">
          <RecommendationsSidebar />
        </aside>
      </div>
    </div>
  )
}
EOF

# Create components (manual extraction required)
echo "⚠️  Manual component extraction required:"
echo "  1. Extract SearchHeader logic from chat.html"
echo "  2. Extract SearchFilters logic"
echo "  3. Extract ProductGrid logic"
echo "  4. Remove all emojis"
echo "  5. Apply design-system.css"

# Create tests
cat > apps/web/src/app/\(customer\)/search/__tests__/SearchPage.test.tsx << 'EOF'
import { render, screen } from '@testing-library/react'
import SearchPage from '../page'

describe('SearchPage', () => {
  it('renders search interface', () => {
    render(<SearchPage />)
    expect(screen.getByRole('searchbox')).toBeInTheDocument()
  })
})
EOF

echo "✅ Directory structure created"
echo "📋 Next steps:"
echo "  1. Extract HTML logic to React components"
echo "  2. Create hooks for state management"
echo "  3. Write unit tests"
echo "  4. Run: cd apps/web && pnpm test"
echo "  5. Visual test: pnpm dev"
```

**Testing Strategy:**

1. **Component Tests**
   ```typescript
   describe('SearchHeader', () => {
     it('renders search bar', () => {})
     it('handles search input', () => {})
     it('displays collection selector', () => {})
     it('does not render emoji indicators', () => {})
   })
   ```

2. **Integration Tests**
   ```typescript
   describe('Search Page Integration', () => {
     it('searches and displays results', async () => {
       render(<SearchPage />)
       const searchInput = screen.getByRole('searchbox')
       fireEvent.change(searchInput, { target: { value: '50ml' } })
       fireEvent.submit(searchInput)

       await waitFor(() => {
         expect(screen.getByText(/results/i)).toBeInTheDocument()
       })
     })
   })
   ```

3. **E2E Tests** (Playwright)
   ```typescript
   test('user can search for products', async ({ page }) => {
     await page.goto('/search')
     await page.fill('[role="searchbox"]', '50ml PET')
     await page.press('[role="searchbox"]', 'Enter')

     await expect(page.locator('.product-card')).toHaveCount(5)
   })
   ```

**Success Criteria:**
- ✅ All chat.html features migrated to React
- ✅ 0 emojis in UI
- ✅ Design system applied (neutral colors, clean design)
- ✅ Progressive loading works (infinite scroll)
- ✅ Image gallery functional
- ✅ Offline support functional
- ✅ i18n works (Korean/English)
- ✅ Unit tests passing (80%+ coverage)
- ✅ E2E tests passing
- ✅ Performance: < 500ms initial render

---

#### 2.3.2 P0: Migrate realtime-demo.html → apps/web/(super-admin)/realtime (Week 5)

**Complexity**: Medium (498 lines, WebSocket integration)

**Feature Analysis:**
```html
<!-- realtime-demo.html key features -->
1. WebSocket connection status
2. Real-time query execution
3. PostgreSQL LISTEN/NOTIFY demo
4. Event log display
5. Query history
6. Connection controls (connect/disconnect)
7. Dark theme (to convert to neutral)
```

**Component Mapping:**

```typescript
// apps/web/src/app/(super-admin)/realtime/page.tsx
import { RealtimeStatus } from './components/RealtimeStatus'
import { QueryExecutor } from './components/QueryExecutor'
import { EventLog } from './components/EventLog'
import { useWebSocket } from '@rag/core/hooks'

export default function RealtimePage() {
  const { status, execute, events } = useWebSocket()

  return (
    <div className="realtime-page">
      <RealtimeStatus status={status} />
      <QueryExecutor onExecute={execute} />
      <EventLog events={events} />
    </div>
  )
}
```

**Directory Structure:**

```
apps/web/src/app/(super-admin)/realtime/
├── page.tsx
├── components/
│   ├── RealtimeStatus.tsx      # Connection status badge
│   ├── QueryExecutor.tsx       # Query input + execute
│   ├── EventLog.tsx            # Event display (monospace)
│   └── ConnectionControls.tsx  # Connect/disconnect buttons
├── hooks/
│   └── useRealtimeDemo.ts      # Demo-specific logic
└── __tests__/
```

**WebSocket Hook Enhancement:**

```typescript
// packages/core/src/hooks/useWebSocket.ts
import { io, Socket } from 'socket.io-client'

export function useWebSocket(url: string = 'http://localhost:8001') {
  const [socket, setSocket] = useState<Socket | null>(null)
  const [status, setStatus] = useState<'disconnected' | 'connected' | 'error'>('disconnected')
  const [events, setEvents] = useState<WebSocketEvent[]>([])

  const connect = useCallback(() => {
    const newSocket = io(url, {
      transports: ['websocket'],
      reconnection: true,
      reconnectionAttempts: 5,
    })

    newSocket.on('connect', () => setStatus('connected'))
    newSocket.on('disconnect', () => setStatus('disconnected'))
    newSocket.on('error', () => setStatus('error'))

    setSocket(newSocket)
  }, [url])

  const disconnect = useCallback(() => {
    socket?.disconnect()
    setSocket(null)
  }, [socket])

  const execute = useCallback((query: string) => {
    if (!socket) return
    socket.emit('query', { query })
  }, [socket])

  useEffect(() => {
    if (!socket) return

    const handleEvent = (data: WebSocketEvent) => {
      setEvents(prev => [...prev, data])
    }

    socket.on('query_result', handleEvent)
    socket.on('notification', handleEvent)

    return () => {
      socket.off('query_result', handleEvent)
      socket.off('notification', handleEvent)
    }
  }, [socket])

  return { status, connect, disconnect, execute, events }
}
```

**Migration Script:**

```bash
#!/bin/bash
# scripts/migration/03_migrate_realtime.sh

set -e

echo "🚀 Migrating realtime-demo.html → apps/web/(super-admin)/realtime"

mkdir -p apps/web/src/app/\(super-admin\)/realtime/{components,hooks,__tests__}

# Create page
cat > apps/web/src/app/\(super-admin\)/realtime/page.tsx << 'EOF'
'use client'

import { useWebSocket } from '@rag/core/hooks'
import { RealtimeStatus } from './components/RealtimeStatus'
import { QueryExecutor } from './components/QueryExecutor'
import { EventLog } from './components/EventLog'
import { ConnectionControls } from './components/ConnectionControls'

export default function RealtimePage() {
  const { status, connect, disconnect, execute, events } = useWebSocket()

  return (
    <div className="container max-w-6xl mx-auto p-6">
      <header className="mb-6">
        <h1 className="text-2xl font-bold">Real-time Backend Demo</h1>
        <p className="text-muted">WebSocket + PostgreSQL LISTEN/NOTIFY</p>
      </header>

      <div className="grid gap-6">
        <div className="flex items-center justify-between">
          <RealtimeStatus status={status} />
          <ConnectionControls
            status={status}
            onConnect={connect}
            onDisconnect={disconnect}
          />
        </div>

        <QueryExecutor onExecute={execute} disabled={status !== 'connected'} />

        <EventLog events={events} />
      </div>
    </div>
  )
}
EOF

echo "✅ Realtime page structure created"
echo "📋 Next: Implement components (RealtimeStatus, QueryExecutor, EventLog)"
```

**Success Criteria:**
- ✅ WebSocket connection functional
- ✅ Real-time query execution works
- ✅ Event log displays correctly (monospace font)
- ✅ Connection status accurate
- ✅ Dark theme removed (neutral light theme)
- ✅ No emojis in UI
- ✅ Auto-reconnect functional
- ✅ Unit tests passing

---

#### 2.3.3 P1: Migrate profile.html → apps/web/(customer)/profile (3 days)

**Complexity**: Low (~400 lines, mostly forms)

**Feature Analysis:**
```html
<!-- profile.html key features -->
1. User avatar display (remove gradient background)
2. Profile information display
3. Password change form
4. Profile badges (neutral style)
5. Account settings
```

**Component Mapping:**

```typescript
// apps/web/src/app/(customer)/profile/page.tsx
import { Avatar } from '@rag/ui'
import { ProfileForm } from './components/ProfileForm'
import { PasswordForm } from './components/PasswordForm'
import { ProfileBadges } from './components/ProfileBadges'

export default function ProfilePage() {
  return (
    <div className="profile-page">
      <ProfileHeader />
      <ProfileForm />
      <PasswordForm />
      <ProfileBadges />
    </div>
  )
}
```

**Success Criteria:**
- ✅ Profile display functional
- ✅ Password change works
- ✅ Avatar gradient removed
- ✅ Badges neutral styled
- ✅ Form validation clean

---

#### 2.3.4 P1: Migrate rag_dashboard.html → apps/web/(admin)/rag (Week 6)

**Complexity**: Medium (~500 lines, file upload, progress tracking)

**Feature Analysis:**
```html
<!-- rag_dashboard.html key features -->
1. File upload area (neutral styling)
2. Collection management
3. Embedding progress bars (neutral colors)
4. Log display (monospace)
5. RAG operations (reindex, delete)
```

**Component Mapping:**

```typescript
// apps/web/src/app/(admin)/rag/page.tsx
import { FileUpload } from '@rag/ui'
import { CollectionManager } from './components/CollectionManager'
import { EmbeddingProgress } from './components/EmbeddingProgress'
import { RAGLogs } from './components/RAGLogs'

export default function RAGDashboardPage() {
  return (
    <div className="rag-dashboard">
      <FileUpload onUpload={handleUpload} />
      <CollectionManager />
      <EmbeddingProgress />
      <RAGLogs />
    </div>
  )
}
```

**Success Criteria:**
- ✅ File upload functional
- ✅ Progress bars neutral
- ✅ Collection management works
- ✅ Logs display correctly
- ✅ No emojis

---

#### 2.3.5 P2: Enhance dashboard.html (3 days)

**Complexity**: Low (~600 lines, mostly layout)

**Feature Analysis:**
```html
<!-- dashboard.html enhancements -->
1. Collection cards with badges (neutral)
2. Stats display (neutral colors)
3. Action buttons (clean design)
4. Recent activity
```

**Success Criteria:**
- ✅ Enhanced with modern React
- ✅ Reuses components from packages/ui
- ✅ Clean, neutral design
- ✅ No emojis

---

#### 2.3.6 P2: Migrate streaming-demo.html (Week 6)

**Complexity**: Medium (~450 lines, SSE streaming)

**Feature Analysis:**
```html
<!-- streaming-demo.html key features -->
1. Mode selector (neutral)
2. Event stream display
3. Type-based borders (subtle)
4. Status indicators (clean)
```

**Component Mapping:**

```typescript
// apps/web/src/app/(super-admin)/streaming/page.tsx
import { useSSE } from '@rag/core/hooks'
import { EventStream } from './components/EventStream'
import { ModeSelector } from './components/ModeSelector'

export default function StreamingPage() {
  const { events, mode, setMode } = useSSE()

  return (
    <div className="streaming-page">
      <ModeSelector mode={mode} onChange={setMode} />
      <EventStream events={events} />
    </div>
  )
}
```

**Success Criteria:**
- ✅ SSE streaming functional
- ✅ Event display clean
- ✅ Mode selector neutral
- ✅ No emojis

---

### 2.4 Phase 4: Extract Shared Logic to packages/core (Week 7-8)

**Goal**: Move frontend/js/ logic to TypeScript services in packages/core

**Files to Migrate:**

| Source File | Target File | Description |
|-------------|-------------|-------------|
| frontend/js/offline-storage.js | packages/core/src/services/offline.service.ts | Offline storage with IndexedDB |
| frontend/js/i18n.js | packages/core/src/services/i18n.service.ts | Internationalization |
| frontend/js/recommendations.js | packages/core/src/services/recommendations.service.ts | Product recommendations |
| frontend/js/auth.js | Enhance packages/core/src/services/auth.service.ts | Auth helpers |
| frontend/js/notifications.js | packages/core/src/services/notifications.service.ts | Push notifications |
| frontend/js/dark-mode.js | ❌ Skip (removing dark mode) | - |
| frontend/js/navbar.js | ✅ Already migrated to React | - |

**Migration Strategy:**

```typescript
// Example: offline-storage.js → offline.service.ts

// Before (frontend/js/offline-storage.js)
class OfflineStorage {
  saveSearchResults(query, results) {
    localStorage.setItem(`search_${query}`, JSON.stringify(results))
  }

  getSearchResults(query) {
    const data = localStorage.getItem(`search_${query}`)
    return data ? JSON.parse(data) : null
  }
}

// After (packages/core/src/services/offline.service.ts)
import { openDB, DBSchema, IDBPDatabase } from 'idb'

interface OfflineDB extends DBSchema {
  searchResults: {
    key: string
    value: {
      query: string
      results: Product[]
      timestamp: number
    }
  }
  pendingActions: {
    key: number
    value: {
      type: string
      payload: any
      timestamp: number
    }
  }
}

export class OfflineStorageService {
  private db: IDBPDatabase<OfflineDB> | null = null

  async init() {
    this.db = await openDB<OfflineDB>('rag-enterprise-offline', 1, {
      upgrade(db) {
        db.createObjectStore('searchResults')
        db.createObjectStore('pendingActions', { autoIncrement: true })
      },
    })
  }

  async saveSearchResults(query: string, results: Product[]) {
    if (!this.db) await this.init()
    await this.db!.put('searchResults', {
      query,
      results,
      timestamp: Date.now(),
    }, query)
  }

  async getSearchResults(query: string): Promise<Product[] | null> {
    if (!this.db) await this.init()
    const data = await this.db!.get('searchResults', query)
    return data?.results || null
  }

  async queueAction(type: string, payload: any) {
    if (!this.db) await this.init()
    await this.db!.add('pendingActions', {
      type,
      payload,
      timestamp: Date.now(),
    })
  }

  async syncPendingActions() {
    if (!this.db) await this.init()
    const actions = await this.db!.getAll('pendingActions')

    for (const action of actions) {
      try {
        await this.executePendingAction(action)
        await this.db!.delete('pendingActions', action.timestamp)
      } catch (error) {
        console.error('Failed to sync action:', error)
      }
    }
  }

  private async executePendingAction(action: any) {
    // Execute API call based on action type
  }
}

export const offlineStorageService = new OfflineStorageService()
```

**Migration Script:**

```bash
#!/bin/bash
# scripts/migration/08_extract_services.sh

set -e

echo "🚀 Extracting shared logic to packages/core"

cd packages/core

# Create services
echo "Creating OfflineStorageService..."
cat > src/services/offline.service.ts << 'EOF'
// (TypeScript implementation above)
EOF

echo "Creating I18nService..."
cat > src/services/i18n.service.ts << 'EOF'
// TypeScript i18n implementation
EOF

echo "Creating RecommendationsService..."
cat > src/services/recommendations.service.ts << 'EOF'
// TypeScript recommendations implementation
EOF

echo "Creating NotificationsService..."
cat > src/services/notifications.service.ts << 'EOF'
// TypeScript notifications implementation
EOF

# Update index exports
cat >> src/services/index.ts << 'EOF'
export * from './offline.service'
export * from './i18n.service'
export * from './recommendations.service'
export * from './notifications.service'
EOF

# Install dependencies
pnpm add idb
pnpm add -D @types/node

echo "✅ Services created"
echo "📋 Next: Update apps to use new services"
```

**Success Criteria:**
- ✅ 4 services created in packages/core
- ✅ TypeScript with full type safety
- ✅ Unit tests written (80%+ coverage)
- ✅ Apps using new services
- ✅ frontend/js/ deprecated (moved to .archived)

---

### 2.5 Phase 5: Optimize Mobile Consolidation (Week 9-10)

**Goal**: Consolidate mobile/ and apps/mobile/ into single apps/mobile/

**Current State:**
```
mobile/                           # Standalone (to archive)
├── react-native/                 # React Native code
├── pwa/                          # PWA code (duplicate)
└── service-worker.js             # Service worker

apps/mobile/                      # Monorepo app (to enhance)
├── src/
│   ├── screens/
│   └── navigation/
└── package.json
```

**Target State:**
```
apps/mobile/                      # Unified mobile app
├── src/
│   ├── screens/                  # React Native screens
│   │   ├── auth/
│   │   ├── search/
│   │   └── profile/
│   ├── navigation/               # Navigation config
│   ├── hooks/                    # Mobile hooks
│   └── lib/                      # Mobile utilities
├── app.json                      # Expo config
├── package.json
└── tsconfig.json
```

**Migration Steps:**

1. **Archive Standalone Mobile**
   ```bash
   mv mobile/ .archived/mobile-standalone/
   ```

2. **Enhance apps/mobile**
   ```bash
   cd apps/mobile

   # Add missing screens from standalone
   cp -r ../.archived/mobile-standalone/react-native/src/screens/* src/screens/

   # Update to use @rag/mobile-ui and @rag/core
   pnpm add @rag/mobile-ui @rag/core
   ```

3. **Update Imports**
   ```typescript
   // Before (standalone)
   import { Button } from '../components/Button'

   // After (monorepo)
   import { Button } from '@rag/mobile-ui'
   import { authService } from '@rag/core/services'
   ```

4. **Configure Expo**
   ```json
   // apps/mobile/app.json
   {
     "expo": {
       "name": "RAG Enterprise Mobile",
       "slug": "rag-enterprise",
       "platforms": ["ios", "android"],
       "version": "1.0.0"
     }
   }
   ```

**Success Criteria:**
- ✅ Single mobile app (apps/mobile)
- ✅ Uses @rag/mobile-ui components
- ✅ Uses @rag/core services
- ✅ Expo configured
- ✅ iOS/Android builds successful
- ✅ PWA functionality preserved (apps/pwa)

---

## 3. File Structure Optimization

### 3.1 Enhanced .claudeignore

**Current Issues:**
- Missing build artifacts (.next, dist, .turbo)
- Missing generated types
- Not ignoring .archived/

**Optimized .claudeignore:**

```gitignore
# ============================================
# RAG Enterprise .claudeignore (v2.0)
# Optimized for Claude Code token efficiency
# ============================================

# ============================================
# Archived Code (HIGH PRIORITY)
# ============================================
.archived/
frontend-v2/
frontend-next/
mobile/

# ============================================
# Build Artifacts & Caches
# ============================================
# Next.js
.next/
out/
*.next/

# Vite
dist/
.vite/

# Turborepo
.turbo/

# General
build/
.cache/
*.tsbuildinfo

# ============================================
# Dependencies
# ============================================
node_modules/
.pnp/
.pnp.js

# Python
__pycache__/
*.pyc
*.pyo
.venv/
venv/
ENV/
env/

# ============================================
# Generated Files
# ============================================
# TypeScript
*.d.ts.map
apps/*/dist/
packages/*/dist/

# Documentation
claudedocs/
.serena/

# ============================================
# Data & Large Files
# ============================================
data/
documents/
images/
exports/
*.sqlite3
*.db

# Media
*.jpg
*.jpeg
*.png
*.gif
*.webp
*.pdf

# Archives
*.tar.gz
*.zip
*.backup
*.bak

# ============================================
# ML Models & Checkpoints
# ============================================
models/
checkpoints/
finetuning/models/
*.pt
*.pth
*.ckpt
*.safetensors
*.bin
*.onnx

# ============================================
# Logs & Reports
# ============================================
*.log
logs/
htmlcov/
.coverage
*.out
test-results/
coverage/

# Large reports
*_REPORT.md
*_DEBUGGING_*.md
*_results.json
benchmark_*.json

# ============================================
# Testing Output
# ============================================
.pytest_cache/
.tox/
.hypothesis/
testsprite_tests/
.nyc_output/

# ============================================
# Claude Internal
# ============================================
.claude/agents/_archived/
.claude/debug/
.claude/logs/
.claude/shell-snapshots/
.claude/file-history/
.agent/

# ============================================
# IDE & Tools
# ============================================
.vscode/
.idea/
.cursor/
.DS_Store

# ============================================
# Docker Volumes
# ============================================
data/qdrant/
data/redis/
data/postgres/
data/mongodb/

# ============================================
# Development Experiments
# ============================================
dev/experiments/
dev/prototypes/
dev/sandbox/
dev/notebooks/

# ============================================
# Git & CI/CD
# ============================================
.git/
.github/workflows/
.githooks/

# ============================================
# Package Manager
# ============================================
pnpm-lock.yaml
package-lock.json
yarn.lock

# ============================================
# Environment
# ============================================
.env
.env.local
.env.*.local
*.secret
*.key
```

**Token Savings:**
- Before: ~35 directories scanned
- After: ~12 directories scanned (excluding .archived/, build artifacts)
- **Estimated savings**: 60-70% on file listings

---

### 3.2 Documentation Structure

```
docs/
├── architecture/              # System design
│   ├── SYSTEM_OVERVIEW.md
│   ├── BACKEND_ARCHITECTURE.md
│   ├── FRONTEND_ARCHITECTURE.md # 🆕
│   ├── DATA_FLOW.md
│   └── SECURITY.md
│
├── api/                       # API documentation
│   ├── V1_ENDPOINTS.md
│   ├── V2_ENDPOINTS.md
│   └── WEBSOCKET_API.md
│
├── guides/                    # How-to guides
│   ├── QUICK_START.md         # 5-minute setup
│   ├── LOCAL_SETUP.md         # Detailed setup
│   ├── DEPLOYMENT.md          # Deployment guide
│   ├── TESTING.md             # Testing guide
│   ├── TROUBLESHOOTING.md     # Common issues
│   ├── CONTRIBUTING.md        # Contribution guide
│   └── MIGRATION.md           # 🆕 v9 → v10 migration
│
├── integration/               # Integration plans
│   ├── FRONTEND_FILE_STRUCTURE_PLAN.md  # This document
│   ├── BACKEND_MIGRATION_PLAN.md
│   ├── V10_INTEGRATION_PLAN.md
│   └── PHASE_STATUS.md        # 🆕 Migration progress
│
├── reference/                 # Technical reference
│   ├── SYMBOLS.md             # Claude symbol system
│   ├── COMPONENT_LIBRARY.md   # UI component reference
│   ├── API_CLIENT.md          # @rag/core API client docs
│   └── TYPESCRIPT_TYPES.md    # Type definitions
│
└── logs/                      # Version logs
    ├── CHANGELOG.md           # User-facing changes
    ├── PROGRESS.md            # Version history
    └── MIGRATION_LOG.md       # 🆕 Migration activities
```

**Key Improvements:**
- **Clear categorization**: architecture, api, guides, integration, reference, logs
- **Progressive detail**: Quick start → Detailed setup → Advanced topics
- **Migration tracking**: integration/ folder for migration plans
- **Developer experience**: guides/ for common workflows

---

### 3.3 Script Organization

```
scripts/
├── migration/                 # Migration scripts (executable)
│   ├── README.md              # Migration guide
│   ├── 00_archive_deprecated.sh
│   ├── 01_move_components.sh
│   ├── 02_migrate_chat.sh
│   ├── 03_migrate_realtime.sh
│   ├── 04_migrate_profile.sh
│   ├── 05_migrate_rag_dashboard.sh
│   ├── 06_migrate_dashboard.sh
│   ├── 07_migrate_streaming.sh
│   ├── 08_extract_services.sh
│   ├── 09_consolidate_mobile.sh
│   └── 10_validate_migration.sh
│
├── deployment/                # Deployment scripts
│   ├── deploy-optimized.sh
│   ├── deploy-production.sh
│   ├── restart-all.sh
│   └── docker-cleanup.sh
│
├── testing/                   # Testing utilities
│   ├── test-optimized.sh
│   ├── test-coverage.sh
│   ├── validate-claude-system.sh
│   ├── visual-regression.sh   # 🆕
│   └── performance-benchmark.sh # 🆕
│
└── utils/                     # General utilities
    ├── generate-types.sh      # Generate TypeScript types
    ├── analyze-bundle.sh      # Bundle size analysis
    ├── sync-packages.sh       # Sync package versions
    └── cleanup-deps.sh        # Remove unused deps
```

---

## 4. Monorepo Configuration

### 4.1 Updated pnpm-workspace.yaml

```yaml
# pnpm-workspace.yaml
packages:
  # Applications
  - 'apps/*'

  # Shared packages
  - 'packages/*'

  # Workers (future)
  - 'workers/*'

# Exclude archived code
exclude:
  - '.archived/**'
```

---

### 4.2 Optimized turbo.json

```json
{
  "$schema": "https://turbo.build/schema.json",
  "globalDependencies": [
    "tsconfig.json",
    ".env"
  ],
  "pipeline": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": [
        "dist/**",
        ".next/**",
        "!.next/cache/**",
        "build/**",
        "out/**"
      ],
      "cache": true
    },
    "dev": {
      "cache": false,
      "persistent": true
    },
    "test": {
      "dependsOn": ["^build"],
      "outputs": [
        "coverage/**"
      ],
      "cache": true
    },
    "lint": {
      "outputs": [],
      "cache": true
    },
    "type-check": {
      "dependsOn": ["^build"],
      "outputs": [],
      "cache": true
    },
    "clean": {
      "cache": false
    }
  },
  "remoteCache": {
    "enabled": false
  }
}
```

**Key Features:**
- **Build caching**: Incremental builds with Turborepo
- **Dependency ordering**: Packages build before apps
- **Output tracking**: Proper cache invalidation
- **Parallel execution**: Tasks run in parallel when possible

**Performance Targets:**
- **Full build**: < 5 minutes (with caching: < 2 minutes)
- **Incremental build**: < 30 seconds
- **Test suite**: < 3 minutes

---

### 4.3 Root package.json

```json
{
  "name": "rag-enterprise",
  "version": "10.0.0",
  "private": true,
  "description": "RAG Enterprise - Unified Multi-platform AI-powered Search System",
  "scripts": {
    "dev": "turbo run dev",
    "dev:web": "turbo run dev --filter=@rag/web",
    "dev:mobile": "turbo run dev --filter=@rag/mobile",
    "dev:pwa": "turbo run dev --filter=@rag/pwa",
    "dev:api": "turbo run dev --filter=@rag/api",

    "build": "turbo run build",
    "build:web": "turbo run build --filter=@rag/web",
    "build:mobile": "turbo run build --filter=@rag/mobile",

    "test": "turbo run test",
    "test:watch": "turbo run test:watch",
    "test:coverage": "turbo run test:coverage",

    "lint": "turbo run lint",
    "lint:fix": "turbo run lint -- --fix",

    "type-check": "turbo run type-check",

    "format": "prettier --write \"**/*.{ts,tsx,md,json}\"",
    "format:check": "prettier --check \"**/*.{ts,tsx,md,json}\"",

    "clean": "turbo run clean && rm -rf node_modules .turbo",

    "changeset": "changeset",
    "version": "changeset version",
    "publish": "turbo run build --filter=./packages/* && changeset publish",

    "migration:archive": "bash scripts/migration/00_archive_deprecated.sh",
    "migration:components": "bash scripts/migration/01_move_components.sh",
    "migration:chat": "bash scripts/migration/02_migrate_chat.sh",
    "migration:realtime": "bash scripts/migration/03_migrate_realtime.sh",
    "migration:profile": "bash scripts/migration/04_migrate_profile.sh",
    "migration:rag": "bash scripts/migration/05_migrate_rag_dashboard.sh",
    "migration:dashboard": "bash scripts/migration/06_migrate_dashboard.sh",
    "migration:streaming": "bash scripts/migration/07_migrate_streaming.sh",
    "migration:services": "bash scripts/migration/08_extract_services.sh",
    "migration:mobile": "bash scripts/migration/09_consolidate_mobile.sh",
    "migration:validate": "bash scripts/migration/10_validate_migration.sh"
  },
  "devDependencies": {
    "@changesets/cli": "^2.27.1",
    "@turbo/gen": "^2.0.0",
    "eslint": "^8.57.0",
    "prettier": "^3.2.5",
    "turbo": "^2.0.0",
    "typescript": "^5.3.3"
  },
  "packageManager": "pnpm@9.1.0",
  "engines": {
    "node": ">=18.0.0",
    "pnpm": ">=9.0.0"
  }
}
```

**Key Features:**
- **Scoped commands**: Run specific apps with `--filter`
- **Migration commands**: Easy-to-run migration scripts
- **Consistent tooling**: Prettier, ESLint, TypeScript
- **Versioning**: Changesets for package versioning

---

## 5. Claude Code Integration

### 5.1 Slash Commands Organization

**Current Commands** (18 total):
```
.claude/commands/
├── README.md                   # Command documentation
├── excel.md                    # Excel processing
├── pdf.md                      # PDF processing
├── docx.md                     # DOCX processing
├── pptx.md                     # PPTX processing
├── canvas.md                   # Design canvas
├── theme.md                    # Theme customization
├── art.md                      # ASCII art generation
├── artifact.md                 # Artifact management
├── brand.md                    # Brand guidelines
├── comms.md                    # Communication templates
├── component.md                # Component generation
├── gif.md                      # GIF generation
├── guide.md                    # Guide generation
├── requirements-info.md        # Requirements analysis
├── webapp.md                   # Web app scaffolding
├── workflow.md                 # Workflow automation
└── xlsx.md                     # XLSX processing
```

**Proposed New Commands:**

```bash
# Migration helpers
.claude/commands/migrate-html.md       # 🆕 HTML → React migration wizard
.claude/commands/test-rag.md           # 🆕 RAG testing utilities
.claude/commands/validate-mobile.md    # 🆕 Mobile validation

# Development workflow
.claude/commands/new-component.md      # 🆕 Generate new component
.claude/commands/new-service.md        # 🆕 Generate new service
.claude/commands/analyze-bundle.md     # 🆕 Bundle size analysis
```

**Example: /migrate-html Command**

```markdown
<!-- .claude/commands/migrate-html.md -->
# Migrate HTML to React

This command helps migrate legacy HTML files to modern React components.

## Usage

```
/migrate-html [html-file] [target-route]
```

## Example

```
/migrate-html frontend/chat.html apps/web/(customer)/search
```

## Steps

1. Analyze HTML structure
2. Extract components
3. Create React components
4. Create hooks for state management
5. Write unit tests
6. Create migration validation tests

## Output

- Component files in target route
- Hook files
- Test files
- Migration checklist

## Validation

After migration:
- [ ] All features functional
- [ ] No emojis in UI
- [ ] Design system applied
- [ ] Unit tests passing (80%+ coverage)
- [ ] E2E tests passing
- [ ] Performance benchmarks met
```

---

### 5.2 MCP Server Optimization

**Updated .claude/mcp.json:**

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/home/rkqksk/projects/new_rag"
      ],
      "env": {
        "ALLOWED_DIRECTORIES": [
          "/home/rkqksk/projects/new_rag/apps",
          "/home/rkqksk/projects/new_rag/packages",
          "/home/rkqksk/projects/new_rag/backend",
          "/home/rkqksk/projects/new_rag/docs",
          "/home/rkqksk/projects/new_rag/scripts"
        ],
        "EXCLUDE_PATTERNS": [
          "**/.archived/**",
          "**/node_modules/**",
          "**/.next/**",
          "**/dist/**",
          "**/.turbo/**",
          "**/build/**",
          "**/__pycache__/**",
          "**/data/**",
          "**/models/**"
        ]
      }
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "serena": {
      "command": "npx",
      "args": [
        "-y",
        "@serenaai/mcp-server-serena",
        "--workspaces",
        "/home/rkqksk/projects/new_rag"
      ],
      "env": {
        "SERENA_LANGUAGE_SERVERS": "typescript,python",
        "SERENA_INDEX_PATHS": [
          "/home/rkqksk/projects/new_rag/apps",
          "/home/rkqksk/projects/new_rag/packages",
          "/home/rkqksk/projects/new_rag/backend"
        ]
      }
    }
  }
}
```

**Key Benefits:**
1. **Filesystem**: Restricted to relevant directories, excludes archives
2. **GitHub**: Unlimited access for public repos
3. **Serena**: Optimized for TypeScript + Python code navigation

---

### 5.3 Custom Agents (Optional)

**Frontend Migration Agent:**

```markdown
<!-- .claude/agents/frontend-migration.md -->
# Frontend Migration Agent

Specialized agent for migrating HTML files to React components.

## Capabilities

1. **HTML Analysis**: Parse HTML structure and extract components
2. **Component Generation**: Create React components from HTML
3. **Hook Extraction**: Convert JS logic to React hooks
4. **Test Generation**: Generate unit and integration tests
5. **Style Migration**: Convert inline styles to CSS modules/Tailwind

## Usage

Activate this agent when migrating legacy HTML files to React.

## Workflow

1. Analyze HTML file structure
2. Identify reusable components
3. Extract state management logic
4. Generate React components
5. Create hooks for side effects
6. Write comprehensive tests
7. Validate migration

## Best Practices

- Remove all emojis from UI
- Apply design system (neutral colors)
- Ensure accessibility (ARIA, keyboard navigation)
- Optimize for performance (code splitting, lazy loading)
- Maintain feature parity with legacy HTML
```

**Component Extractor Agent:**

```markdown
<!-- .claude/agents/component-extractor.md -->
# Component Extractor Agent

Extracts reusable components from apps/ to packages/ui.

## Capabilities

1. **Usage Analysis**: Find component usage across apps
2. **Parameterization**: Make components brand-agnostic
3. **Type Safety**: Generate comprehensive TypeScript types
4. **Test Migration**: Move and update component tests
5. **Documentation**: Generate component documentation

## Usage

Activate when moving components to shared packages.

## Workflow

1. Analyze component usage across apps
2. Identify shared props/behavior
3. Parameterize hardcoded values
4. Move to packages/ui
5. Update all imports
6. Migrate tests
7. Generate documentation

## Output

- Parameterized component in packages/ui
- Updated imports in all apps
- Migrated tests
- Component documentation (props, examples, variants)
```

---

## 6. Migration Execution Plan

### 6.1 Timeline Overview

**Total Duration**: 12 weeks
**Team Size**: 2-3 developers
**Estimated Effort**: ~400 hours

```
Week 1:  Phase 1 + Phase 2 (Archive + Components)
Week 2:  Phase 2 (Finish components)
Week 3:  Phase 3.1 (Migrate chat.html - part 1)
Week 4:  Phase 3.1 (Migrate chat.html - part 2)
Week 5:  Phase 3.2 (Migrate realtime-demo.html)
Week 6:  Phase 3.3-3.6 (Migrate profile, rag_dashboard, dashboard, streaming)
Week 7:  Phase 4 (Extract services - part 1)
Week 8:  Phase 4 (Extract services - part 2)
Week 9:  Phase 5 (Mobile consolidation)
Week 10: Phase 5 (Mobile testing)
Week 11: Phase 6 (Claude Code optimization)
Week 12: Phase 7 (Testing, validation, documentation)
```

---

### 6.2 Detailed Phase Breakdown

#### Week 1: Archive + Component Migration

**Phase 1: Archive Deprecated Code**
- **Duration**: 1 day
- **Deliverables**:
  - `.archived/` directory created
  - `frontend-v2/`, `frontend-next/`, `mobile/` archived
  - `.archived/README.md` with documentation
  - `.gitignore` and `.claudeignore` updated

**Phase 2: Move Components (Start)**
- **Duration**: 4 days
- **Deliverables**:
  - `packages/ui/src/dashboard/` created
  - 7 components moved and parameterized
  - All imports updated in `apps/web`
  - Component tests updated

---

#### Week 2: Finish Component Migration

**Phase 2: Move Components (Complete)**
- **Duration**: 5 days
- **Deliverables**:
  - All component tests passing
  - Storybook updated (if exists)
  - Component documentation written
  - Visual regression tests setup

---

#### Week 3-4: Migrate chat.html (Most Complex)

**Phase 3.1: Product Search Migration**
- **Duration**: 2 weeks
- **Week 3 Deliverables**:
  - Directory structure created
  - SearchHeader component
  - SearchFilters component
  - ProductGrid component
  - ProductCard component (reused from packages/ui)

- **Week 4 Deliverables**:
  - ImageGallery component
  - RecommendationsSidebar component
  - useSearch hook
  - useInfiniteScroll hook
  - useImageGallery hook
  - All unit tests passing
  - E2E tests written
  - Performance optimization

---

#### Week 5: Migrate realtime-demo.html

**Phase 3.2: Realtime Demo Migration**
- **Duration**: 1 week
- **Deliverables**:
  - RealtimePage component
  - RealtimeStatus component
  - QueryExecutor component
  - EventLog component
  - ConnectionControls component
  - useWebSocket hook enhancement
  - Tests passing

---

#### Week 6: Migrate Remaining Features

**Phase 3.3-3.6: Profile, RAG, Dashboard, Streaming**
- **Duration**: 1 week
- **Deliverables**:
  - ProfilePage (3.3)
  - RAGDashboardPage (3.4)
  - Enhanced Dashboard (3.5)
  - StreamingPage (3.6)
  - All tests passing

---

#### Week 7-8: Extract Services

**Phase 4: Shared Logic Extraction**
- **Duration**: 2 weeks
- **Week 7 Deliverables**:
  - OfflineStorageService
  - I18nService
  - RecommendationsService

- **Week 8 Deliverables**:
  - NotificationsService
  - AuthService enhancements
  - All services tested
  - Apps updated to use services
  - `frontend/js/` deprecated

---

#### Week 9-10: Mobile Consolidation

**Phase 5: Mobile Optimization**
- **Duration**: 2 weeks
- **Week 9 Deliverables**:
  - `mobile/` archived
  - `apps/mobile/` enhanced with standalone features
  - All imports updated to use @rag/mobile-ui and @rag/core

- **Week 10 Deliverables**:
  - iOS build successful
  - Android build successful
  - Mobile tests passing
  - PWA functionality validated

---

#### Week 11: Claude Code Optimization

**Phase 6: Developer Experience**
- **Duration**: 1 week
- **Deliverables**:
  - New slash commands created
  - Custom agents implemented (optional)
  - MCP configuration optimized
  - Documentation updated
  - Symbol system refined

---

#### Week 12: Testing & Validation

**Phase 7: Production Readiness**
- **Duration**: 1 week
- **Deliverables**:
  - All migration validation tests passing
  - Performance benchmarks met
  - Visual regression tests passing
  - Documentation complete
  - Deployment guide updated
  - v10.0.0 release notes

---

### 6.3 Milestones

| Milestone | Week | Description | Success Criteria |
|-----------|------|-------------|------------------|
| **M1: Clean Structure** | 1 | Archived deprecated code | 3 dirs archived, .claudeignore updated |
| **M2: Shared Components** | 2 | Component library complete | 7 components in packages/ui, all tests passing |
| **M3: Critical Features** | 4 | chat.html migrated | Search functional, tests passing, <500ms load |
| **M4: Admin Features** | 6 | All HTML migrated | 0 HTML in production, all React |
| **M5: Unified Services** | 8 | Services extracted | packages/core complete, frontend/js archived |
| **M6: Single Mobile** | 10 | Mobile consolidated | iOS/Android builds, apps/mobile complete |
| **M7: Production Ready** | 12 | v10.0.0 release | All tests passing, docs complete, deployed |

---

### 6.4 Scripts to Create

All scripts are located in `scripts/migration/`. Each script is:
- **Executable** (`chmod +x`)
- **Idempotent** (can run multiple times safely)
- **Validated** (checks before making changes)
- **Rollback-capable** (creates backups)

---

#### Script 1: 00_archive_deprecated.sh

```bash
#!/bin/bash
# scripts/migration/00_archive_deprecated.sh
# Phase 1: Archive deprecated code

set -e

echo "========================================="
echo "Phase 1: Archive Deprecated Code"
echo "========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create .archived directory
echo -e "${YELLOW}Creating .archived directory...${NC}"
mkdir -p .archived

# Archive frontend-v2
if [ -d "frontend-v2" ]; then
  echo -e "${YELLOW}Archiving frontend-v2/...${NC}"
  mv frontend-v2 .archived/
  echo -e "${GREEN}✓ frontend-v2 archived${NC}"
else
  echo -e "${YELLOW}⚠  frontend-v2 already archived${NC}"
fi

# Archive frontend-next
if [ -d "frontend-next" ]; then
  echo -e "${YELLOW}Archiving frontend-next/...${NC}"
  mv frontend-next .archived/
  echo -e "${GREEN}✓ frontend-next archived${NC}"
else
  echo -e "${YELLOW}⚠  frontend-next already archived${NC}"
fi

# Archive standalone mobile
if [ -d "mobile" ]; then
  echo -e "${YELLOW}Archiving mobile/...${NC}"
  mv mobile .archived/mobile-standalone
  echo -e "${GREEN}✓ mobile archived${NC}"
else
  echo -e "${YELLOW}⚠  mobile already archived${NC}"
fi

# Create archive README
cat > .archived/README.md << 'EOF'
# Archived Code

This directory contains deprecated code that has been replaced by the v10.0.0 unified architecture.

## Archived Directories

### frontend-v2/
- **Archived**: 2025-11-15
- **Reason**: 85% duplicate of apps/web
- **Replaced by**: apps/web (Next.js 14)
- **Migration**: All features migrated to apps/web with modern React

### frontend-next/
- **Archived**: 2025-11-15
- **Reason**: Abandoned experimental directory
- **Status**: Never completed, no production features

### mobile-standalone/
- **Archived**: 2025-11-15
- **Reason**: Not integrated with monorepo
- **Replaced by**: apps/mobile (React Native + Expo)
- **Migration**: All screens migrated to apps/mobile with @rag/mobile-ui

## Restoration

If you need to restore any archived code:

```bash
# Example: Restore frontend-v2
mv .archived/frontend-v2 ./
```

**Warning**: Restoring archived code may conflict with v10.0.0 structure.

## Deletion

After 6 months (2025-05-15), if no issues found, this directory can be safely deleted.
EOF

# Update .gitignore
if ! grep -q "^.archived/" .gitignore; then
  echo -e "${YELLOW}Updating .gitignore...${NC}"
  echo "" >> .gitignore
  echo "# Archived code" >> .gitignore
  echo ".archived/" >> .gitignore
  echo -e "${GREEN}✓ .gitignore updated${NC}"
fi

# Update .claudeignore
if ! grep -q "^.archived/" .claudeignore; then
  echo -e "${YELLOW}Updating .claudeignore...${NC}"
  sed -i '1s/^/.archived\/\n/' .claudeignore
  echo -e "${GREEN}✓ .claudeignore updated${NC}"
fi

# Validate
echo -e "${YELLOW}Validating archive...${NC}"
if [ -d ".archived/frontend-v2" ] || [ -d ".archived/frontend-next" ] || [ -d ".archived/mobile-standalone" ]; then
  echo -e "${GREEN}✓ Validation passed${NC}"
else
  echo -e "${RED}✗ Validation failed: No directories archived${NC}"
  exit 1
fi

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Phase 1 Complete!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "Summary:"
echo "  ✓ 3 directories archived"
echo "  ✓ .archived/README.md created"
echo "  ✓ .gitignore updated"
echo "  ✓ .claudeignore updated"
echo ""
echo "Next: Run 01_move_components.sh"
```

---

#### Script 2: 01_move_components.sh

```bash
#!/bin/bash
# scripts/migration/01_move_components.sh
# Phase 2: Move dashboard components to packages/ui

set -e

echo "========================================="
echo "Phase 2: Move Dashboard Components"
echo "========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Create directory structure
echo -e "${YELLOW}Creating packages/ui/src/dashboard/...${NC}"
mkdir -p packages/ui/src/dashboard/__tests__

# Component list
COMPONENTS=(
  "Sidebar"
  "Navbar"
  "StatsCard"
  "CollectionCard"
  "ProductCard"
  "SearchBar"
  "Filters"
)

# Move components
for component in "${COMPONENTS[@]}"; do
  SOURCE="apps/web/src/components/${component}.tsx"
  TARGET="packages/ui/src/dashboard/$(echo $component | tr '[:upper:]' '[:lower:]' | sed 's/\([A-Z]\)/-\1/g' | sed 's/^-//').tsx"

  if [ -f "$SOURCE" ]; then
    echo -e "${YELLOW}Moving ${component}...${NC}"

    # Check if component needs parameterization
    if grep -q "RAG Enterprise" "$SOURCE"; then
      echo -e "${YELLOW}  ⚠  ${component} contains hardcoded brand name${NC}"
      echo -e "${YELLOW}  ℹ  Manual parameterization required${NC}"
    fi

    mv "$SOURCE" "$TARGET"
    echo -e "${GREEN}  ✓ ${component} moved${NC}"
  else
    echo -e "${YELLOW}  ⚠  ${component} not found, skipping${NC}"
  fi
done

# Create barrel export
cat > packages/ui/src/dashboard/index.ts << 'EOF'
// Dashboard components
export { Sidebar } from './sidebar'
export { Navbar } from './navbar'
export { StatsCard } from './stats-card'
export { CollectionCard } from './collection-card'
export { ProductCard } from './product-card'
export { SearchBar } from './search-bar'
export { Filters } from './filters'

// Types
export type { SidebarProps } from './sidebar'
export type { NavbarProps } from './navbar'
export type { StatsCardProps } from './stats-card'
export type { CollectionCardProps } from './collection-card'
export type { ProductCardProps } from './product-card'
export type { SearchBarProps } from './search-bar'
export type { FiltersProps } from './filters'
EOF

# Update packages/ui/src/index.ts
if ! grep -q "export \* from './dashboard'" packages/ui/src/index.ts; then
  echo "export * from './dashboard'" >> packages/ui/src/index.ts
fi

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Phase 2 Complete!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "Summary:"
echo "  ✓ packages/ui/src/dashboard/ created"
echo "  ✓ ${#COMPONENTS[@]} components moved"
echo "  ✓ Barrel export created"
echo ""
echo "⚠  Manual Steps Required:"
echo "  1. Parameterize components (remove hardcoded brand names)"
echo "  2. Update imports in apps/web"
echo "  3. Move and update component tests"
echo "  4. Run: cd packages/ui && pnpm test"
echo ""
echo "Next: Run 02_migrate_chat.sh"
```

---

#### Script 3: 02_migrate_chat.sh

```bash
#!/bin/bash
# scripts/migration/02_migrate_chat.sh
# Phase 3.1: Migrate chat.html to React

set -e

echo "========================================="
echo "Phase 3.1: Migrate chat.html"
echo "========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Create directory structure
echo -e "${YELLOW}Creating apps/web/src/app/(customer)/search/...${NC}"
mkdir -p "apps/web/src/app/(customer)/search"/{components,hooks,__tests__}

# Create page.tsx
cat > "apps/web/src/app/(customer)/search/page.tsx" << 'EOF'
'use client'

import { SearchHeader } from './components/SearchHeader'
import { SearchFilters } from './components/SearchFilters'
import { ProductGrid } from './components/ProductGrid'
import { RecommendationsSidebar } from './components/RecommendationsSidebar'

export default function SearchPage() {
  return (
    <div className="container max-w-7xl mx-auto p-6">
      <SearchHeader />

      <div className="flex gap-6 mt-6">
        {/* Filters sidebar */}
        <aside className="w-64 flex-shrink-0">
          <SearchFilters />
        </aside>

        {/* Product grid */}
        <main className="flex-1">
          <ProductGrid />
        </main>

        {/* Recommendations sidebar */}
        <aside className="w-80 flex-shrink-0">
          <RecommendationsSidebar />
        </aside>
      </div>
    </div>
  )
}
EOF

# Create component stubs
COMPONENTS=(
  "SearchHeader"
  "SearchFilters"
  "ProductGrid"
  "RecommendationsSidebar"
  "ImageGallery"
  "EmptyState"
)

for component in "${COMPONENTS[@]}"; do
  cat > "apps/web/src/app/(customer)/search/components/${component}.tsx" << EOF
'use client'

export function ${component}() {
  return (
    <div>
      {/* TODO: Implement ${component} */}
      <p>${component} - To be implemented</p>
    </div>
  )
}
EOF
done

# Create hook stubs
HOOKS=(
  "useSearch"
  "useInfiniteScroll"
  "useImageGallery"
)

for hook in "${HOOKS[@]}"; do
  cat > "apps/web/src/app/(customer)/search/hooks/${hook}.ts" << EOF
import { useState } from 'react'

export function ${hook}() {
  // TODO: Implement ${hook}
  return {}
}
EOF
done

# Create test file
cat > "apps/web/src/app/(customer)/search/__tests__/SearchPage.test.tsx" << 'EOF'
import { render, screen } from '@testing-library/react'
import SearchPage from '../page'

describe('SearchPage', () => {
  it('renders search interface', () => {
    render(<SearchPage />)
    // TODO: Add assertions
  })
})
EOF

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Phase 3.1 Structure Created!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "Summary:"
echo "  ✓ Directory structure created"
echo "  ✓ Page component created"
echo "  ✓ ${#COMPONENTS[@]} component stubs created"
echo "  ✓ ${#HOOKS[@]} hook stubs created"
echo "  ✓ Test file created"
echo ""
echo "⚠  Manual Implementation Required:"
echo "  1. Extract HTML logic from frontend/chat.html"
echo "  2. Implement SearchHeader component"
echo "  3. Implement SearchFilters component"
echo "  4. Implement ProductGrid component"
echo "  5. Implement RecommendationsSidebar component"
echo "  6. Implement ImageGallery component"
echo "  7. Implement hooks (useSearch, useInfiniteScroll, useImageGallery)"
echo "  8. Remove all emojis from UI"
echo "  9. Apply design-system.css"
echo "  10. Write comprehensive tests"
echo ""
echo "Reference:"
echo "  HTML: frontend/chat.html (894 lines)"
echo "  Target: apps/web/src/app/(customer)/search/"
echo ""
echo "Next: Implement components and run tests"
```

---

#### Script 10: 10_validate_migration.sh

```bash
#!/bin/bash
# scripts/migration/10_validate_migration.sh
# Phase 7: Validate entire migration

set -e

echo "========================================="
echo "Migration Validation"
echo "========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

FAILED=0

# Function to check
check() {
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ $1${NC}"
  else
    echo -e "${RED}✗ $1${NC}"
    FAILED=$((FAILED + 1))
  fi
}

# 1. Check archived directories
echo -e "${YELLOW}Checking archived directories...${NC}"
[ -d ".archived/frontend-v2" ]; check "frontend-v2 archived"
[ -d ".archived/frontend-next" ]; check "frontend-next archived"
[ -d ".archived/mobile-standalone" ]; check "mobile archived"

# 2. Check component migration
echo -e "${YELLOW}Checking component migration...${NC}"
[ -d "packages/ui/src/dashboard" ]; check "Dashboard components directory exists"
[ -f "packages/ui/src/dashboard/sidebar.tsx" ]; check "Sidebar component exists"
[ -f "packages/ui/src/dashboard/navbar.tsx" ]; check "Navbar component exists"

# 3. Check HTML migration
echo -e "${YELLOW}Checking HTML migration...${NC}"
[ -d "apps/web/src/app/(customer)/search" ]; check "Search page exists"
[ -d "apps/web/src/app/(super-admin)/realtime" ]; check "Realtime page exists"
[ -d "apps/web/src/app/(customer)/profile" ]; check "Profile page exists"
[ -d "apps/web/src/app/(admin)/rag" ]; check "RAG dashboard exists"

# 4. Check service extraction
echo -e "${YELLOW}Checking service extraction...${NC}"
[ -f "packages/core/src/services/offline.service.ts" ]; check "OfflineStorageService exists"
[ -f "packages/core/src/services/i18n.service.ts" ]; check "I18nService exists"
[ -f "packages/core/src/services/recommendations.service.ts" ]; check "RecommendationsService exists"

# 5. Check mobile consolidation
echo -e "${YELLOW}Checking mobile consolidation...${NC}"
[ -d "apps/mobile" ]; check "Mobile app exists"
[ ! -d "mobile" ]; check "Standalone mobile archived"

# 6. Run tests
echo -e "${YELLOW}Running tests...${NC}"
cd apps/web && pnpm test --passWithNoTests > /dev/null 2>&1; check "Web app tests"
cd ../../packages/ui && pnpm test --passWithNoTests > /dev/null 2>&1; check "UI package tests"
cd ../core && pnpm test --passWithNoTests > /dev/null 2>&1; check "Core package tests"
cd ../..

# 7. Check build
echo -e "${YELLOW}Checking builds...${NC}"
pnpm build > /dev/null 2>&1; check "Monorepo builds successfully"

# 8. Check for legacy code
echo -e "${YELLOW}Checking for legacy code...${NC}"
! grep -r "frontend-v2" apps/ packages/ > /dev/null 2>&1; check "No frontend-v2 imports"
! grep -r "frontend-next" apps/ packages/ > /dev/null 2>&1; check "No frontend-next imports"

# Summary
echo ""
echo -e "${GREEN}=========================================${NC}"
if [ $FAILED -eq 0 ]; then
  echo -e "${GREEN}✓ Migration Validated Successfully!${NC}"
  echo -e "${GREEN}=========================================${NC}"
  echo ""
  echo "All checks passed. Ready for production!"
  exit 0
else
  echo -e "${RED}✗ Migration Validation Failed${NC}"
  echo -e "${RED}=========================================${NC}"
  echo ""
  echo "Failed checks: $FAILED"
  echo "Please fix issues before proceeding to production."
  exit 1
fi
```

---

### 6.5 Validation Strategy

**1. Component Unit Tests**
```typescript
// packages/ui/src/dashboard/__tests__/sidebar.test.tsx
import { render, screen } from '@testing-library/react'
import { Sidebar } from '../sidebar'

describe('Sidebar', () => {
  it('renders with default brand name', () => {
    render(<Sidebar menuItems={[]} />)
    expect(screen.getByText('RAG Enterprise')).toBeInTheDocument()
  })

  it('renders with custom brand name', () => {
    render(<Sidebar brandName="Custom Brand" menuItems={[]} />)
    expect(screen.getByText('Custom Brand')).toBeInTheDocument()
  })

  it('handles menu navigation', () => {
    const onNavigate = jest.fn()
    render(<Sidebar menuItems={[{ path: '/test', label: 'Test' }]} onNavigate={onNavigate} />)

    fireEvent.click(screen.getByText('Test'))
    expect(onNavigate).toHaveBeenCalledWith('/test')
  })
})
```

**2. Integration Tests**
```typescript
// apps/web/src/app/(customer)/search/__tests__/integration.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import SearchPage from '../page'

describe('Search Page Integration', () => {
  it('performs search and displays results', async () => {
    render(<SearchPage />)

    const searchInput = screen.getByRole('searchbox')
    fireEvent.change(searchInput, { target: { value: '50ml PET' } })
    fireEvent.submit(searchInput)

    await waitFor(() => {
      expect(screen.getByText(/results/i)).toBeInTheDocument()
    })
  })
})
```

**3. Visual Regression Tests**
```typescript
// apps/web/__tests__/visual/search.visual.test.ts
import { test, expect } from '@playwright/test'

test('search page matches snapshot', async ({ page }) => {
  await page.goto('/search')
  await expect(page).toHaveScreenshot('search-page.png')
})
```

**4. Performance Benchmarks**
```typescript
// apps/web/__tests__/performance/search.perf.test.ts
import { test, expect } from '@playwright/test'

test('search page loads within 500ms', async ({ page }) => {
  const startTime = Date.now()
  await page.goto('/search')
  const loadTime = Date.now() - startTime

  expect(loadTime).toBeLessThan(500)
})
```

---

## 7. Risk Mitigation

### 7.1 Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Feature parity loss** | Medium | High | Comprehensive feature checklist, side-by-side testing |
| **User disruption** | Low | High | Phased rollout, feature flags, rollback plan |
| **Performance regression** | Medium | Medium | Benchmarking, bundle size analysis, lazy loading |
| **Team coordination** | Medium | Medium | Daily standups, shared migration board, documentation |
| **Technical debt** | High | Low | Code reviews, automated testing, refactoring sprints |
| **Migration delays** | High | Medium | Buffer time in timeline, parallel workstreams |

---

### 7.2 Mitigation Strategies

**1. Feature Parity**
```bash
# Create feature checklist for each HTML file
# Example: chat.html feature checklist

✓ Search bar with auto-suggest
✓ Collection selector
✓ Product cards with images
✓ Image gallery modal
✓ Progressive loading (infinite scroll)
✓ Filters (category, material, capacity)
✓ Offline support (IndexedDB)
✓ Recommendations sidebar
✗ Dark mode (intentionally removed)
✓ i18n support (Korean/English)
```

**2. User Disruption**

*Side-by-Side Deployment:*
```nginx
# nginx.conf - Serve both legacy and new apps
server {
  listen 80;

  # Legacy HTML (production)
  location /legacy/ {
    root /var/www/frontend;
  }

  # New React app (beta)
  location / {
    proxy_pass http://localhost:3000;
  }
}
```

*Feature Flags:*
```typescript
// Feature flag for gradual rollout
const useNewSearch = process.env.NEXT_PUBLIC_USE_NEW_SEARCH === 'true'

export default function SearchLayout() {
  if (useNewSearch) {
    return <NewSearchPage />
  } else {
    // Redirect to legacy
    window.location.href = '/legacy/chat.html'
  }
}
```

**3. Performance Regression**

*Bundle Size Monitoring:*
```bash
# scripts/utils/analyze-bundle.sh
#!/bin/bash

echo "Analyzing bundle sizes..."

cd apps/web
pnpm build

# Check bundle size
BUNDLE_SIZE=$(du -sh .next/static/chunks | awk '{print $1}')
echo "Bundle size: $BUNDLE_SIZE"

# Alert if > 1MB
if [ $(du -b .next/static/chunks | awk '{print $1}') -gt 1048576 ]; then
  echo "⚠️  Warning: Bundle size exceeds 1MB"
  exit 1
fi
```

*Lighthouse CI:*
```yaml
# .github/workflows/lighthouse.yml
name: Lighthouse CI
on: [pull_request]

jobs:
  lighthouse:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: treosh/lighthouse-ci-action@v9
        with:
          urls: |
            http://localhost:3000/search
          uploadArtifacts: true
          temporaryPublicStorage: true
```

**4. Team Coordination**

*Daily Standups:*
- What did you migrate yesterday?
- What will you migrate today?
- Any blockers?

*Shared Migration Board (GitHub Projects):*
```
Backlog → In Progress → Review → Testing → Done

Backlog:
- [ ] Migrate streaming-demo.html
- [ ] Extract NotificationsService

In Progress:
- [ ] Migrate chat.html (John, 50% complete)
- [ ] Move Sidebar component (Jane, 80% complete)

Review:
- [ ] PR #123: Migrate realtime-demo.html (awaiting review)

Testing:
- [ ] Validate OfflineStorageService (QA testing)

Done:
- [x] Archive deprecated code
- [x] Move dashboard components
```

---

### 7.3 Rollback Plan

**Scenario**: Migration fails, need to rollback to legacy HTML

**Step 1: Keep Legacy HTML**
```bash
# Don't delete frontend/*.html until migration fully validated
# Keep for 6 months minimum
```

**Step 2: Git Branches**
```bash
# All migration work on feature branch
git checkout -b feature/v10-migration

# Easy rollback
git checkout main
```

**Step 3: Nginx Fallback**
```nginx
# nginx.conf - Fallback to legacy
location / {
  try_files @new @legacy;
}

location @new {
  proxy_pass http://localhost:3000;
}

location @legacy {
  root /var/www/frontend;
  try_files $uri $uri.html =404;
}
```

**Step 4: Environment Variables**
```bash
# Quick toggle between legacy and new
NEXT_PUBLIC_USE_LEGACY=true  # Serve legacy
NEXT_PUBLIC_USE_LEGACY=false # Serve new
```

---

## 8. Success Metrics

### 8.1 Quantitative Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| **Code Reduction** | Baseline | -30% | Total LOC (lines of code) |
| **Component Reuse** | ~20% | 90% | Components from @rag/ui |
| **Build Time** | ~8 min | <5 min | Turborepo build time |
| **Test Coverage** | ~50% | 80% | Jest coverage report |
| **Legacy Deprecation** | 9 HTML files | 0 HTML files | Count of *.html in production |
| **Bundle Size (Web)** | Unknown | <1MB | .next/static/chunks size |
| **Mobile Build Time** | Unknown | <3 min | iOS + Android build time |
| **Top-level Directories** | 35+ | 12 | Count of directories in root |
| **Duplicate Code** | 85% | <5% | Code duplication analysis |

---

### 8.2 Qualitative Metrics

| Metric | Assessment Method | Target |
|--------|-------------------|--------|
| **Developer Experience** | Survey (1-5 scale) | 4.5+ |
| **Code Maintainability** | Code review feedback | "Easy to maintain" |
| **Documentation Quality** | Peer review | "Complete and clear" |
| **Migration Smoothness** | Retrospective | "Minimal blockers" |

---

### 8.3 Progress Tracking

**Weekly Report Template:**

```markdown
## Week X Migration Report

### Completed
- ✅ Task 1
- ✅ Task 2

### In Progress
- 🔄 Task 3 (50%)
- 🔄 Task 4 (30%)

### Blocked
- 🚫 Task 5 (waiting for API update)

### Metrics
- Code reduced: -15% (target: -30%)
- Component reuse: 60% (target: 90%)
- Tests written: 45 (target: 80)
- Coverage: 65% (target: 80%)

### Risks
- None this week

### Next Week
- [ ] Task 6
- [ ] Task 7
```

---

### 8.4 Final Validation Checklist

**Before Production Deployment:**

```markdown
## v10.0.0 Production Checklist

### Code Quality
- [ ] All migration scripts executed successfully
- [ ] 0 HTML files in production
- [ ] 90%+ component reuse from @rag/ui
- [ ] 80%+ test coverage
- [ ] All tests passing (unit, integration, E2E)
- [ ] Visual regression tests passing
- [ ] No emojis in UI
- [ ] Design system applied consistently

### Performance
- [ ] Build time <5 min
- [ ] Web bundle size <1MB
- [ ] Search page load <500ms
- [ ] Mobile build <3 min
- [ ] Lighthouse score >90

### Architecture
- [ ] Backend migration complete (app/ + src/ → backend/)
- [ ] Frontend consolidation complete
- [ ] Mobile consolidation complete
- [ ] Shared packages functional (@rag/ui, @rag/core, @rag/mobile-ui)
- [ ] Monorepo optimized (Turborepo + pnpm)

### Documentation
- [ ] All migration docs updated
- [ ] FRONTEND_FILE_STRUCTURE_PLAN.md validated
- [ ] BACKEND_MIGRATION_PLAN.md validated
- [ ] Component library documented
- [ ] API client documented
- [ ] Deployment guide updated

### Deployment
- [ ] Development environment validated
- [ ] Staging environment validated
- [ ] Production environment ready
- [ ] Rollback plan tested
- [ ] Monitoring configured
- [ ] Alerts configured

### Team
- [ ] All team members trained on new structure
- [ ] Migration guide reviewed
- [ ] Retrospective completed
- [ ] v10.0.0 release notes published
```

---

## Appendix: Scripts & Templates

### A.1 Component Template

```typescript
// templates/component.template.tsx
'use client'

import React from 'react'
import { cn } from '@rag/ui/utils'

export interface {{COMPONENT_NAME}}Props {
  children?: React.ReactNode
  className?: string
}

export function {{COMPONENT_NAME}}({
  children,
  className,
}: {{COMPONENT_NAME}}Props) {
  return (
    <div className={cn('{{COMPONENT_NAME}}', className)}>
      {children}
    </div>
  )
}
```

---

### A.2 Service Template

```typescript
// templates/service.template.ts
export class {{SERVICE_NAME}}Service {
  private static instance: {{SERVICE_NAME}}Service

  private constructor() {
    // Initialize
  }

  static getInstance(): {{SERVICE_NAME}}Service {
    if (!{{SERVICE_NAME}}Service.instance) {
      {{SERVICE_NAME}}Service.instance = new {{SERVICE_NAME}}Service()
    }
    return {{SERVICE_NAME}}Service.instance
  }

  // Service methods
}

export const {{SERVICE_NAME_LOWER}}Service = {{SERVICE_NAME}}Service.getInstance()
```

---

### A.3 Test Template

```typescript
// templates/test.template.tsx
import { render, screen } from '@testing-library/react'
import { {{COMPONENT_NAME}} } from '../{{COMPONENT_FILE}}'

describe('{{COMPONENT_NAME}}', () => {
  it('renders without crashing', () => {
    render(<{{COMPONENT_NAME}} />)
  })

  it('renders children', () => {
    render(
      <{{COMPONENT_NAME}}>
        <span>Test Child</span>
      </{{COMPONENT_NAME}}>
    )
    expect(screen.getByText('Test Child')).toBeInTheDocument()
  })

  it('applies custom className', () => {
    const { container } = render(<{{COMPONENT_NAME}} className="custom-class" />)
    expect(container.firstChild).toHaveClass('custom-class')
  })
})
```

---

### A.4 Migration Script Template

```bash
#!/bin/bash
# templates/migration-script.template.sh
# Phase X: {{PHASE_NAME}}

set -e

echo "========================================="
echo "Phase X: {{PHASE_NAME}}"
echo "========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# TODO: Add migration logic

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Phase X Complete!${NC}"
echo -e "${GREEN}=========================================${NC}"
```

---

## Summary

This comprehensive plan provides:

1. **Claude Code Optimized Structure** - 12 top-level directories, clear hierarchy, token-efficient
2. **Frontend Consolidation** - 7 phases over 12 weeks, from archive to production
3. **File Structure Optimization** - Enhanced .claudeignore, documentation structure, script organization
4. **Monorepo Configuration** - Turborepo + pnpm, optimized for <5min builds
5. **Claude Code Integration** - MCP optimization, custom commands, optional agents
6. **Migration Execution** - Detailed timeline, 10 executable scripts, validation strategy
7. **Risk Mitigation** - Feature parity, rollback plan, performance monitoring
8. **Success Metrics** - Quantitative (30% code reduction, 90% reuse) and qualitative

**Ready for Implementation**: All scripts, templates, and checklists provided for immediate execution.

**Alignment**: Fully aligned with v10.0.0 "Unified" architecture and Claude Code best practices.

---

**End of Plan**
