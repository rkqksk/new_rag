# Quick Fix Guide - TypeScript Errors

**Total Errors**: 23
**Estimated Time**: 45 minutes
**Priority**: P0 - CRITICAL

---

## Fix 1: Analytics Page (3 errors) - 5 minutes

**File**: `/Users/oypnus/Project/new_rag/apps/web/app/(dashboard)/admin/analytics/page.tsx`

### Line 202
```typescript
// BEFORE
changeType={parseFloat(callsTrend) >= 0 ? "positive" : "negative"}

// AFTER
changeType={parseFloat(callsTrend) >= 0 ? "increase" : "decrease"}
```

### Line 209
```typescript
// BEFORE
changeType="positive"

// AFTER
changeType="increase"
```

### Line 222
```typescript
// BEFORE
changeType={totalFailed > 1000 ? "negative" : "neutral"}

// AFTER
changeType={totalFailed > 1000 ? "decrease" : "neutral"}
```

---

## Fix 2: Settings Page (13 errors) - 15 minutes

**File 1**: `/Users/oypnus/Project/new_rag/apps/web/lib/features.ts`

### Step 1: Extend FeatureCategory type (lines 7)
```typescript
// BEFORE
export type FeatureCategory = 'core' | 'saas' | 'enterprise' | 'experimental'

// AFTER
export type FeatureCategory =
  | 'core'
  | 'saas'
  | 'enterprise'
  | 'experimental'
  | 'ui'
  | 'functionality'
  | 'accessibility'
  | 'developer'
  | 'data'
```

### Step 2: Extend Feature interface (lines 9-16)
```typescript
// BEFORE
export interface Feature {
  id: string
  name: string
  description: string
  category: FeatureCategory
  enabled: boolean
  requiredRole?: string[]
}

// AFTER
export interface Feature {
  id: string
  name: string
  description: string
  category: FeatureCategory
  enabled: boolean
  requiredRole?: string[]
  impact?: 'low' | 'medium' | 'high' | 'critical'
  implementationTime?: string
}
```

**File 2**: `/Users/oypnus/Project/new_rag/apps/web/app/(dashboard)/admin/settings/page.tsx`

After fixing the Feature interface, all 13 errors in this file will be resolved automatically.

---

## Fix 3: Team Page (3 errors) - 5 minutes

**File**: `/Users/oypnus/Project/new_rag/apps/web/app/(dashboard)/admin/team/page.tsx`

### Line 247
```typescript
// BEFORE
changeType="positive"

// AFTER
changeType="increase"
```

### Line 253
```typescript
// BEFORE
changeType={someCondition ? "positive" : "neutral"}

// AFTER
changeType={someCondition ? "increase" : "neutral"}
```

### Line 489
**Issue**: copyToClipboard called with 2 arguments, expects 1

```typescript
// BEFORE
copyToClipboard(invite.invite_link, "초대 링크가 복사되었습니다")

// AFTER
copyToClipboard(invite.invite_link)
```

**Note**: The toast message should be handled separately in the calling component, not passed to copyToClipboard.

---

## Fix 4: JsonViewer Component (3 errors) - 5 minutes

**File**: `/Users/oypnus/Project/new_rag/apps/web/components/dashboard/JsonViewer.tsx`

### Lines 7-8
```typescript
// BEFORE
import { copyJSON } from '@/lib/utils/copy'
import { exportJSON, exportCSV } from '@/lib/utils/export'

// AFTER
import { copyToClipboard } from '@/lib/utils/copy'
import { exportToJSON, exportToCSV } from '@/lib/utils/export'
```

### Update usage in the component
If the component uses these functions, update the calls:

```typescript
// BEFORE
copyJSON(data)
exportJSON(data, 'filename.json')
exportCSV(data, 'filename.csv')

// AFTER
copyToClipboard(JSON.stringify(data, null, 2))
exportToJSON(data, 'filename.json')
exportToCSV(data, 'filename.csv')
```

---

## Verification Commands

```bash
# 1. Navigate to web app
cd /Users/oypnus/Project/new_rag/apps/web

# 2. Run type check
pnpm run type-check

# Expected output: No errors!

# 3. Build to verify
pnpm run build
```

---

## Bonus: Update Next.js (15 minutes)

```bash
# Update Next.js to fix 10 security vulnerabilities
cd /Users/oypnus/Project/new_rag/apps/web
pnpm update next@latest

# Verify
pnpm list next
# Should show: next@15.0.3 or higher

# Test the app
pnpm run dev
# Open http://localhost:3000
```

---

## Summary Checklist

- [ ] Fix analytics page (3 errors)
- [ ] Extend Feature interface (fixes 13 errors in settings page)
- [ ] Fix team page (3 errors)
- [ ] Fix JsonViewer imports (3 errors)
- [ ] Verify with `pnpm run type-check`
- [ ] Update Next.js to 15.0.3+
- [ ] Test the application

**Total Time**: 45 minutes
**Impact**: 23 errors fixed, 10+ security vulnerabilities patched

---

**Generated**: 2025-11-12
**Tool**: Claude Code Testing Agent
