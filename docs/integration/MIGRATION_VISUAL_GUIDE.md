# Frontend Migration Visual Guide

**Companion to**: FRONTEND_FILE_STRUCTURE_PLAN.md
**Version**: v1.0.0
**Date**: 2025-11-15

---

## Migration Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     CURRENT STATE (v9.3.0)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  frontend/              frontend-v2/           mobile/          │
│  ├── chat.html          ├── app/              ├── react-native/ │
│  ├── realtime-demo.html ├── components/       └── pwa/          │
│  ├── profile.html       └── (85% duplicate)                     │
│  ├── rag_dashboard.html                                         │
│  └── ...                apps/web/             apps/mobile/      │
│                         ├── (partial)         └── (partial)     │
│  frontend-next/         └── ...                                 │
│  └── (abandoned)                                                │
│                                                                 │
│  PROBLEMS:                                                      │
│  • 9 HTML files in production                                   │
│  • 85% code duplication                                         │
│  • 35+ top-level directories                                    │
│  • Fragmented mobile code                                       │
│  • No shared services                                           │
└─────────────────────────────────────────────────────────────────┘
                               │
                               │ 12-Week Migration
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                   TARGET STATE (v10.0.0)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  apps/                        packages/                         │
│  ├── web/                     ├── ui/                           │
│  │   └── app/                 │   ├── components/               │
│  │       ├── (customer)/      │   └── dashboard/  ◄─┐           │
│  │       │   ├── search/      │                     │           │
│  │       │   └── profile/     ├── core/             │           │
│  │       ├── (admin)/         │   ├── api/          │ Shared    │
│  │       │   ├── dashboard/   │   └── services/     │           │
│  │       │   └── rag/         │                     │           │
│  │       └── (super-admin)/   ├── mobile-ui/        │           │
│  │           ├── realtime/    │   └── components/   │           │
│  │           └── streaming/   │                     │           │
│  │                            ├── config/           │           │
│  ├── mobile/                  └── types/            │           │
│  │   └── src/                                       │           │
│  │       ├── screens/   ──────────────────────────┘           │
│  │       └── navigation/                                        │
│  │                                                              │
│  ├── pwa/                                                       │
│  └── api/                                                       │
│                                                                 │
│  .archived/                   backend/                          │
│  ├── frontend-v2/             └── (unified Python)              │
│  ├── frontend-next/                                             │
│  └── mobile-standalone/                                         │
│                                                                 │
│  BENEFITS:                                                      │
│  • 0 HTML files in production                                   │
│  • 90% component reuse                                          │
│  • 12 top-level directories (-65%)                              │
│  • Single mobile codebase                                       │
│  • Centralized services                                         │
│  • <5min builds                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Migration Phases Timeline

```
Week 1-2: Foundation
┌───────────────────────────────────────────────────┐
│ Phase 1: Archive     │ Phase 2: Components       │
│ ─────────────────────┼──────────────────────────  │
│ • Move to .archived/ │ • Extract 7 components    │
│ • Update .ignore     │ • Parameterize            │
│ • Document           │ • Move to packages/ui     │
└───────────────────────────────────────────────────┘

Week 3-6: Core Features
┌─────────────────────────────────────────────────────────────────┐
│ Phase 3.1        │ Phase 3.2       │ Phase 3.3-3.6             │
│ ─────────────────┼─────────────────┼──────────────────────────  │
│ chat.html        │ realtime-demo   │ profile, rag, dashboard,  │
│ (2 weeks)        │ (1 week)        │ streaming (1 week)        │
│                  │                 │                           │
│ • SearchPage     │ • RealtimePage  │ • ProfilePage             │
│ • ProductGrid    │ • WebSocket     │ • RAGDashboard            │
│ • ImageGallery   │ • EventLog      │ • Enhanced Dashboard      │
│ • 6 components   │ • 4 components  │ • StreamingPage           │
└─────────────────────────────────────────────────────────────────┘

Week 7-8: Services
┌───────────────────────────────────────────────────┐
│ Phase 4: Extract Services                        │
│ ──────────────────────────────────────────────── │
│ frontend/js/ → packages/core/src/services/       │
│                                                  │
│ • offline-storage.js → offline.service.ts        │
│ • i18n.js → i18n.service.ts                      │
│ • recommendations.js → recommendations.service.ts│
│ • notifications.js → notifications.service.ts    │
└───────────────────────────────────────────────────┘

Week 9-10: Mobile
┌───────────────────────────────────────────────────┐
│ Phase 5: Mobile Consolidation                    │
│ ──────────────────────────────────────────────── │
│ mobile/ → .archived/mobile-standalone/           │
│ apps/mobile/ (enhanced)                          │
│                                                  │
│ • Archive standalone                             │
│ • Use @rag/mobile-ui                             │
│ • Use @rag/core                                  │
│ • Build iOS/Android                              │
└───────────────────────────────────────────────────┘

Week 11-12: Finalization
┌───────────────────────────────────────────────────┐
│ Phase 6: Claude     │ Phase 7: Validation       │
│ ────────────────────┼──────────────────────────  │
│ • New commands      │ • Full testing            │
│ • MCP optimization  │ • Performance check       │
│ • Custom agents     │ • Documentation           │
│ • Symbol system     │ • Production deploy       │
└───────────────────────────────────────────────────┘
```

---

## Component Migration Flow

```
┌──────────────────────────────────────────────────────────────┐
│                    COMPONENT EXTRACTION                      │
└──────────────────────────────────────────────────────────────┘

Step 1: Identify Reusable Components
┌────────────────────┐
│ apps/web/          │
│  └── components/   │
│      ├── Sidebar   │ ◄── Used in 3+ pages?
│      ├── Navbar    │ ◄── Generic enough?
│      └── ...       │ ◄── Brand-specific?
└────────────────────┘
         │
         │ Yes → Extract
         ▼
Step 2: Parameterize
┌─────────────────────────────────────────────┐
│ // Before (hardcoded)                       │
│ <h1>RAG Enterprise</h1>                     │
│                                             │
│ // After (parameterized)                    │
│ <h1>{brandName || "RAG Enterprise"}</h1>    │
└─────────────────────────────────────────────┘
         │
         ▼
Step 3: Move to packages/ui
┌────────────────────┐
│ packages/ui/       │
│  └── dashboard/    │
│      ├── sidebar.tsx   ◄── Parameterized
│      ├── navbar.tsx    ◄── Reusable
│      └── index.ts      ◄── Exported
└────────────────────┘
         │
         ▼
Step 4: Update Imports
┌─────────────────────────────────────────────┐
│ // Before                                   │
│ import { Sidebar } from '@/components'      │
│                                             │
│ // After                                    │
│ import { Sidebar } from '@rag/ui/dashboard' │
└─────────────────────────────────────────────┘
         │
         ▼
Step 5: Reuse Across Apps
┌────────────┬────────────┬────────────┐
│ apps/web   │ apps/mobile│ apps/pwa   │
│            │            │            │
│ Sidebar ◄──┼────────────┼───► Sidebar│
│            │            │            │
└────────────┴────────────┴────────────┘
             ▲
             │
    packages/ui/dashboard
```

---

## HTML to React Migration Pattern

```
┌──────────────────────────────────────────────────────────────┐
│              HTML → REACT MIGRATION PATTERN                  │
└──────────────────────────────────────────────────────────────┘

Example: chat.html (894 lines) → SearchPage

HTML Structure:                    React Structure:
┌────────────────┐                ┌────────────────────────────┐
│ chat.html      │                │ apps/web/(customer)/search/│
│                │                │                            │
│ <head>         │                │ page.tsx                   │
│  <link css>    │   ──────────►  │  └── SearchPage component  │
│                │                │                            │
│ <body>         │                │ components/                │
│  <header>      │   ──────────►  │  ├── SearchHeader          │
│  <aside>       │   ──────────►  │  ├── SearchFilters         │
│  <main>        │   ──────────►  │  ├── ProductGrid           │
│   <div cards>  │   ──────────►  │  ├── ProductCard (from ui) │
│   <div modal>  │   ──────────►  │  ├── ImageGallery          │
│  </main>       │                │  └── Recommendations       │
│  <aside>       │                │                            │
│ </body>        │                │ hooks/                     │
│                │                │  ├── useSearch             │
│ <script>       │   ──────────►  │  ├── useInfiniteScroll     │
│  JS logic      │                │  └── useImageGallery       │
│ </script>      │                │                            │
└────────────────┘                └────────────────────────────┘

Key Transformations:
• HTML elements    → React components
• Inline CSS       → Tailwind classes / CSS modules
• Vanilla JS       → React hooks
• DOM manipulation → State management
• Event listeners  → Event handlers
• Emojis           → Removed
• Gradients        → Neutral colors
```

---

## Service Extraction Pattern

```
┌──────────────────────────────────────────────────────────────┐
│               SERVICE EXTRACTION PATTERN                     │
└──────────────────────────────────────────────────────────────┘

Before: Vanilla JavaScript               After: TypeScript Service
┌─────────────────────────────┐         ┌──────────────────────────────┐
│ frontend/js/                │         │ packages/core/src/services/  │
│                             │         │                              │
│ offline-storage.js          │         │ offline.service.ts           │
│ ─────────────────────────── │   ───►  │ ──────────────────────────── │
│ class OfflineStorage {      │         │ export class OfflineStorage  │
│   saveSearchResults(q, r) { │         │   Service {                  │
│     localStorage.setItem()  │         │   async saveSearchResults(   │
│   }                         │         │     query: string,           │
│ }                           │         │     results: Product[]       │
│                             │         │   ): Promise<void> {         │
│                             │         │     await this.db.put()      │
│                             │         │   }                          │
│                             │         │ }                            │
└─────────────────────────────┘         └──────────────────────────────┘

Improvements:
✓ TypeScript (type safety)
✓ Async/await (better error handling)
✓ IndexedDB (better offline storage)
✓ Singleton pattern (shared instance)
✓ Testable (dependency injection)
✓ Reusable (across apps/web, apps/mobile, apps/pwa)
```

---

## Directory Consolidation

```
┌──────────────────────────────────────────────────────────────┐
│            BEFORE: 35+ Top-Level Directories                 │
└──────────────────────────────────────────────────────────────┘

Root/
├── agents/           ◄── Fragmented
├── airflow/
├── alembic/
├── app/              ◄── Backend v7
├── apps/             ◄── Partial
├── backend/          ◄── Duplicate
├── components/       ◄── Unused
├── config/
├── data/
├── dev/
├── docs/
├── examples/
├── exports/
├── finetuning/
├── frontend/         ◄── Legacy HTML
├── frontend-next/    ◄── Abandoned
├── frontend-v2/      ◄── 85% duplicate
├── grafana/
├── k8s/
├── mcp_servers/
├── migrations/
├── mkdocs/
├── mobile/           ◄── Standalone
├── monitoring/
├── node_modules/
├── packages/         ◄── Underutilized
├── plugins/
├── scripts/
├── servers/
├── sql/
├── src/              ◄── Backend v8-v9
├── tests/
├── testsprite_tests/
├── workers/
└── workflows/

PROBLEM: Hard to navigate, confusing for Claude Code, token-inefficient

┌──────────────────────────────────────────────────────────────┐
│            AFTER: 12 Top-Level Directories                   │
└──────────────────────────────────────────────────────────────┘

Root/
├── .archived/        ◄── Deprecated code (gitignored)
│   ├── frontend-v2/
│   ├── frontend-next/
│   └── mobile-standalone/
│
├── apps/             ◄── Applications (web, mobile, pwa, api)
├── packages/         ◄── Shared packages (ui, core, mobile-ui, config, types)
├── backend/          ◄── Unified Python backend
├── docs/             ◄── Organized documentation
├── scripts/          ◄── Migration + deployment
├── data/             ◄── Data files (claudeignored)
├── k8s/              ◄── Kubernetes configs
├── .github/          ◄── CI/CD workflows
├── .claude/          ◄── Claude Code config
├── node_modules/     ◄── Dependencies (ignored)
└── [config files]    ◄── Root configs (package.json, turbo.json, etc.)

BENEFIT: 65% reduction, clear hierarchy, Claude Code optimized
```

---

## Claude Code Token Optimization

```
┌──────────────────────────────────────────────────────────────┐
│               CLAUDE CODE TOKEN EFFICIENCY                   │
└──────────────────────────────────────────────────────────────┘

Before:
┌─────────────────────────────────────────────────────────┐
│ Claude scans 35+ directories                            │
│ ├── Many duplicates (frontend-v2, backend)              │
│ ├── Large data files (data/, models/)                   │
│ ├── Build artifacts (.next/, dist/, node_modules/)      │
│ └── Archives (not excluded)                             │
│                                                         │
│ Token Usage: 100% baseline                              │
│ File Listings: ~500 files indexed                       │
│ Context Windows: Frequently exceeded                    │
└─────────────────────────────────────────────────────────┘

After:
┌─────────────────────────────────────────────────────────┐
│ Claude scans 12 directories                             │
│ ├── .archived/ excluded (claudeignored)                 │
│ ├── data/, models/ excluded                             │
│ ├── Build artifacts excluded (.next/, .turbo/)          │
│ └── Only active code indexed                            │
│                                                         │
│ Token Usage: 30-40% of baseline (60-70% savings)        │
│ File Listings: ~200 files indexed                       │
│ Context Windows: Rarely exceeded                        │
└─────────────────────────────────────────────────────────┘

Enhanced .claudeignore:
─────────────────────────────────────────────────
# Archived code (high priority)
.archived/

# Build artifacts
.next/
.turbo/
dist/
build/

# Dependencies
node_modules/

# Data
data/
models/
*.db

# Generated
claudedocs/
.serena/
─────────────────────────────────────────────────

MCP Optimization:
─────────────────────────────────────────────────
{
  "filesystem": {
    "allowedDirectories": [
      "apps/", "packages/", "backend/", "docs/", "scripts/"
    ],
    "excludePatterns": [
      "**/.archived/**",
      "**/node_modules/**",
      "**/.next/**"
    ]
  }
}
─────────────────────────────────────────────────

Result: 4-5x more efficient Claude Code usage
```

---

## Build Performance Optimization

```
┌──────────────────────────────────────────────────────────────┐
│                  TURBOREPO BUILD PIPELINE                    │
└──────────────────────────────────────────────────────────────┘

Build Order (with caching):

1. Shared Packages (parallel)
   ┌─────────┬─────────┬─────────┬─────────┬─────────┐
   │ @rag/ui │ @rag/   │ @rag/   │ @rag/   │ @rag/   │
   │         │ core    │ mobile- │ config  │ types   │
   │         │         │ ui      │         │         │
   └────┬────┴────┬────┴────┬────┴────┬────┴────┬────┘
        │         │         │         │         │
        └─────────┴─────────┴─────────┴─────────┘
                          │
                          ▼
2. Applications (parallel, depends on packages)
   ┌─────────┬─────────┬─────────┬─────────┐
   │ @rag/   │ @rag/   │ @rag/   │ @rag/   │
   │ web     │ mobile  │ pwa     │ api     │
   │         │         │         │         │
   └─────────┴─────────┴─────────┴─────────┘

With Caching:
─────────────────────────────────────────────────
First build:      5 minutes (full)
Subsequent:       30 seconds (incremental)
No changes:       5 seconds (cached)
─────────────────────────────────────────────────

Turborepo Configuration:
{
  "pipeline": {
    "build": {
      "dependsOn": ["^build"],    ◄── Build deps first
      "outputs": [".next/**", "dist/**"],
      "cache": true               ◄── Enable caching
    }
  }
}

Benefits:
✓ Incremental builds (only changed packages)
✓ Remote caching (optional, for teams)
✓ Parallel execution (faster builds)
✓ Smart dependency tracking
```

---

## Testing Strategy Layers

```
┌──────────────────────────────────────────────────────────────┐
│                     TESTING PYRAMID                          │
└──────────────────────────────────────────────────────────────┘

                     ▲
                    ╱ ╲
                   ╱ E2E ╲           (Playwright)
                  ╱───────╲          5-10 tests
                 ╱         ╲         Critical user flows
                ╱───────────╲
               ╱ Integration ╲       (Jest + Testing Library)
              ╱───────────────╲      20-30 tests
             ╱                 ╲     Component interactions
            ╱─────────────────── ╲
           ╱      Unit Tests      ╲  (Jest)
          ╱─────────────────────── ╲ 100+ tests
         ╱                         ╱ Individual components/functions
        ╱─────────────────────────╱
       ╱                         ╱
      └─────────────────────────┘

Layer 1: Unit Tests (80% coverage target)
───────────────────────────────────────────────
packages/ui/src/dashboard/__tests__/
├── sidebar.test.tsx
├── navbar.test.tsx
├── product-card.test.tsx
└── ...

Test: Individual components in isolation
Example:
  ✓ Sidebar renders with default props
  ✓ Sidebar accepts custom brand name
  ✓ Sidebar handles navigation clicks

Layer 2: Integration Tests
───────────────────────────────────────────────
apps/web/src/app/(customer)/search/__tests__/
├── SearchPage.integration.test.tsx
└── ...

Test: Component interactions
Example:
  ✓ Search query triggers ProductGrid update
  ✓ Filter selection refines results
  ✓ Image click opens gallery modal

Layer 3: E2E Tests
───────────────────────────────────────────────
apps/web/__tests__/e2e/
├── search.spec.ts
├── realtime.spec.ts
└── ...

Test: Complete user flows
Example:
  ✓ User can log in and search for products
  ✓ User can view product details
  ✓ User can save to collection

Layer 4: Visual Regression (bonus)
───────────────────────────────────────────────
apps/web/__tests__/visual/
├── search.visual.test.ts
└── ...

Test: UI consistency
Example:
  ✓ Search page matches snapshot
  ✓ No unintended style changes

Result: Confidence in migration, quick bug detection
```

---

## Success Metrics Dashboard

```
┌──────────────────────────────────────────────────────────────┐
│              MIGRATION SUCCESS DASHBOARD                     │
└──────────────────────────────────────────────────────────────┘

Code Quality
─────────────────────────────────────────────────
Metric              Current    Target    Status
─────────────────────────────────────────────────
Code Reduction      0%         -30%      ░░░░░░░░░░░░
Component Reuse     20%        90%       ████░░░░░░░░
Duplicate Code      85%        <5%       ░░░░░░░░░░░░
─────────────────────────────────────────────────

Performance
─────────────────────────────────────────────────
Metric              Current    Target    Status
─────────────────────────────────────────────────
Build Time          8 min      <5 min    ░░░░░░░░░░░░
Bundle Size         ?          <1 MB     ░░░░░░░░░░░░
Page Load           ?          <500ms    ░░░░░░░░░░░░
─────────────────────────────────────────────────

Testing
─────────────────────────────────────────────────
Metric              Current    Target    Status
─────────────────────────────────────────────────
Test Coverage       50%        80%       ██████░░░░░░
Unit Tests          ?          100+      ░░░░░░░░░░░░
Integration Tests   ?          20+       ░░░░░░░░░░░░
E2E Tests           ?          5+        ░░░░░░░░░░░░
─────────────────────────────────────────────────

Architecture
─────────────────────────────────────────────────
Metric              Current    Target    Status
─────────────────────────────────────────────────
HTML in Production  9 files    0 files   ░░░░░░░░░░░░
Top-level Dirs      35+        12        ░░░░░░░░░░░░
Mobile Apps         2          1         ░░░░░░░░░░░░
─────────────────────────────────────────────────

Legend: ░ Not started  ▒ In progress  █ Complete
```

---

## Quick Reference Commands

```bash
# ============================================
# MIGRATION COMMANDS (package.json scripts)
# ============================================

# Phase 1: Archive
pnpm migration:archive

# Phase 2: Components
pnpm migration:components

# Phase 3: Features
pnpm migration:chat         # Week 3-4
pnpm migration:realtime     # Week 5
pnpm migration:profile      # Week 6
pnpm migration:rag          # Week 6
pnpm migration:dashboard    # Week 6
pnpm migration:streaming    # Week 6

# Phase 4: Services
pnpm migration:services     # Week 7-8

# Phase 5: Mobile
pnpm migration:mobile       # Week 9-10

# Phase 7: Validate
pnpm migration:validate     # Week 12

# ============================================
# DEVELOPMENT COMMANDS
# ============================================

# Run all apps
pnpm dev

# Run specific app
pnpm dev:web
pnpm dev:mobile
pnpm dev:pwa

# Build all
pnpm build

# Test all
pnpm test

# Format code
pnpm format

# Type check
pnpm type-check

# ============================================
# VALIDATION COMMANDS
# ============================================

# Full test suite
pnpm test

# Coverage report
pnpm test:coverage

# Build check
pnpm build

# Bundle analysis
pnpm analyze-bundle

# ============================================
# CLAUDE CODE COMMANDS (new slash commands)
# ============================================

/migrate-html frontend/chat.html apps/web/(customer)/search
/test-rag search
/validate-mobile
/new-component ProductCard
/new-service OfflineStorage
```

---

**Next**: Review FRONTEND_FILE_STRUCTURE_PLAN.md for detailed implementation guide.

**File**: `/home/rkqksk/projects/new_rag/FRONTEND_FILE_STRUCTURE_PLAN.md`
**Size**: 3,415 lines | 94 KB
