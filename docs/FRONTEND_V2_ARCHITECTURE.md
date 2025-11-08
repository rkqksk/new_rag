# Frontend v2.0 Architecture - Modern React Dashboard

**Version**: v2.0.0
**Framework**: Next.js 14 + shadcn-ui
**Theme**: Black Background + Natural Theme
**Auth**: Multi-tier (Super-user → Staff → Customer)

---

## Design System

### Color Palette (Black + Natural)

```typescript
// Tailwind Config - Natural theme with Black background
theme: {
  extend: {
    colors: {
      border: "hsl(var(--border))",
      input: "hsl(var(--input))",
      ring: "hsl(var(--ring))",
      background: "hsl(var(--background))",      // Black: #000000
      foreground: "hsl(var(--foreground))",      // Natural text
      primary: {
        DEFAULT: "hsl(var(--primary))",          // Natural accent
        foreground: "hsl(var(--primary-foreground))",
      },
      // Natural color scheme (earthy tones)
      natural: {
        50: '#fafaf9',   // Stone-50
        100: '#f5f5f4',  // Stone-100
        200: '#e7e5e4',  // Stone-200
        300: '#d6d3d1',  // Stone-300
        400: '#a8a29e',  // Stone-400
        500: '#78716c',  // Stone-500 (primary natural)
        600: '#57534e',  // Stone-600
        700: '#44403c',  // Stone-700
        800: '#292524',  // Stone-800
        900: '#1c1917',  // Stone-900
        950: '#0c0a09',  // Stone-950
      }
    },
  }
}
```

### CSS Variables

```css
/* globals.css - Black background + Natural theme */
@layer base {
  :root {
    --background: 0 0% 0%;           /* Pure black */
    --foreground: 60 9.1% 97.8%;     /* Natural white */

    --card: 24 9.8% 10%;             /* Dark gray card */
    --card-foreground: 60 9.1% 97.8%;

    --popover: 0 0% 3.9%;
    --popover-foreground: 60 9.1% 97.8%;

    --primary: 60 9.1% 97.8%;        /* Natural stone */
    --primary-foreground: 24 9.8% 10%;

    --secondary: 12 6.5% 15.1%;      /* Natural dark */
    --secondary-foreground: 60 9.1% 97.8%;

    --muted: 12 6.5% 15.1%;
    --muted-foreground: 24 5.4% 63.9%;

    --accent: 12 6.5% 15.1%;
    --accent-foreground: 60 9.1% 97.8%;

    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 60 9.1% 97.8%;

    --border: 12 6.5% 15.1%;
    --input: 12 6.5% 15.1%;
    --ring: 24 5.7% 82.9%;           /* Natural ring */

    --radius: 0.5rem;
  }
}
```

---

## Authentication System

### User Hierarchy

```
┌─────────────────────────────────────┐
│         SUPER-USER (Level 0)        │  ← 최고 관리자
│  - 모든 권한                         │
│  - 시스템 설정                       │
│  - 사용자 관리                       │
└─────────────────────────────────────┘
                 │
    ┌────────────┴────────────┐
    │                         │
┌───▼────────────┐   ┌────────▼────────┐
│  ADMIN         │   │  MANAGER        │  ← Level 1
│  (내부 관리자)  │   │  (부서 관리자)   │
│  - 전체 조회   │   │  - 부서 데이터   │
│  - 승인/반려   │   │  - 통계 조회     │
└────────────────┘   └─────────────────┘
                 │
    ┌────────────┴────────────┐
    │                         │
┌───▼────────────┐   ┌────────▼────────┐
│  STAFF         │   │  OPERATOR       │  ← Level 2
│  (내부 직원)    │   │  (현장 작업자)   │
│  - 데이터 입력 │   │  - 제한적 조회   │
│  - 부분 조회   │   │  - 작업 기록     │
└────────────────┘   └─────────────────┘
                 │
    ┌────────────┴────────────┐
    │                         │
┌───▼────────────┐   ┌────────▼────────┐
│  CUSTOMER_VIP  │   │  CUSTOMER       │  ← Level 3
│  (프리미엄 고객)│   │  (일반 고객)     │
│  - 우선 지원   │   │  - 기본 검색     │
│  - 맞춤 추천   │   │  - 제품 조회     │
└────────────────┘   └─────────────────┘
```

### Permission Matrix

| Feature | Super-user | Admin | Manager | Staff | Operator | Customer VIP | Customer |
|---------|-----------|-------|---------|-------|----------|--------------|----------|
| **시스템 설정** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **사용자 관리** | ✅ | ✅ | 부분 | ❌ | ❌ | ❌ | ❌ |
| **전체 대시보드** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **데이터 분석** | ✅ | ✅ | ✅ | 읽기 | ❌ | ❌ | ❌ |
| **제조 관리** | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| **제품 검색** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **견적 요청** | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| **API 키 관리** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **결제 관리** | ✅ | ✅ | 읽기 | ❌ | ❌ | 본인 | 본인 |

---

## Directory Structure

```
frontend-v2/
├── app/                          # Next.js App Router
│   ├── (auth)/                   # Auth pages (no layout)
│   │   ├── login/
│   │   │   └── page.tsx         # Login page
│   │   ├── register/
│   │   │   └── page.tsx         # Registration
│   │   └── forgot-password/
│   │       └── page.tsx         # Password reset
│   │
│   ├── (dashboard)/              # Protected dashboard routes
│   │   ├── layout.tsx           # Dashboard layout (sidebar + navbar)
│   │   │
│   │   ├── super-admin/         # Super-user only (Level 0)
│   │   │   ├── page.tsx         # System overview
│   │   │   ├── users/           # User management
│   │   │   ├── system/          # System settings
│   │   │   └── logs/            # Audit logs
│   │   │
│   │   ├── admin/               # Admin + Manager (Level 1)
│   │   │   ├── page.tsx         # Admin dashboard
│   │   │   ├── analytics/       # Data analytics
│   │   │   ├── billing/         # Billing management
│   │   │   └── api-keys/        # API key management
│   │   │
│   │   ├── staff/               # Staff + Operator (Level 2)
│   │   │   ├── page.tsx         # Staff dashboard
│   │   │   ├── manufacturing/   # Manufacturing management
│   │   │   ├── quality/         # Quality control
│   │   │   └── inventory/       # Inventory
│   │   │
│   │   └── customer/            # Customer area (Level 3)
│   │       ├── page.tsx         # Customer dashboard
│   │       ├── search/          # Product search
│   │       ├── orders/          # Order history
│   │       └── support/         # Customer support
│   │
│   ├── api/                      # API routes
│   │   ├── auth/
│   │   │   ├── login/
│   │   │   ├── logout/
│   │   │   └── session/
│   │   └── user/
│   │       └── profile/
│   │
│   ├── layout.tsx               # Root layout
│   ├── globals.css              # Global styles (Black + Natural)
│   └── page.tsx                 # Landing page
│
├── components/
│   ├── ui/                      # shadcn-ui components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── input.tsx
│   │   ├── dialog.tsx
│   │   ├── dropdown-menu.tsx
│   │   ├── sidebar.tsx
│   │   ├── table.tsx
│   │   └── ... (30+ components)
│   │
│   ├── auth/                    # Auth components
│   │   ├── LoginForm.tsx
│   │   ├── RegisterForm.tsx
│   │   ├── ForgotPasswordForm.tsx
│   │   └── ProtectedRoute.tsx
│   │
│   ├── dashboard/               # Dashboard components
│   │   ├── Sidebar.tsx          # Navigation sidebar
│   │   ├── Navbar.tsx           # Top navbar
│   │   ├── StatCard.tsx         # Statistics card
│   │   ├── ChartCard.tsx        # Chart card
│   │   └── DataTable.tsx        # Data table
│   │
│   └── layout/
│       ├── DashboardLayout.tsx
│       └── AuthLayout.tsx
│
├── lib/
│   ├── auth.ts                  # Auth utilities
│   ├── permissions.ts           # Permission checks
│   ├── api.ts                   # API client
│   └── utils.ts                 # Utility functions
│
├── hooks/
│   ├── useAuth.ts               # Auth hook
│   ├── usePermission.ts         # Permission hook
│   └── useUser.ts               # User data hook
│
├── types/
│   ├── user.ts                  # User types
│   ├── auth.ts                  # Auth types
│   └── api.ts                   # API types
│
├── middleware.ts                # Auth middleware
├── tailwind.config.ts           # Tailwind config (Natural theme)
├── components.json              # shadcn-ui config
└── package.json
```

---

## Component Examples

### 1. Login Form (Black + Natural)

```tsx
// components/auth/LoginForm.tsx
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export function LoginForm() {
  return (
    <Card className="w-full max-w-md bg-stone-900 border-stone-800">
      <CardHeader>
        <CardTitle className="text-2xl text-stone-100">로그인</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm text-stone-300">이메일</label>
          <Input
            type="email"
            placeholder="user@example.com"
            className="bg-black border-stone-700 text-stone-100"
          />
        </div>
        <div className="space-y-2">
          <label className="text-sm text-stone-300">비밀번호</label>
          <Input
            type="password"
            className="bg-black border-stone-700 text-stone-100"
          />
        </div>
        <Button className="w-full bg-stone-700 hover:bg-stone-600 text-stone-100">
          로그인
        </Button>
      </CardContent>
    </Card>
  )
}
```

### 2. Dashboard Sidebar

```tsx
// components/dashboard/Sidebar.tsx
import { useAuth } from '@/hooks/useAuth'
import { usePermission } from '@/hooks/usePermission'

export function Sidebar() {
  const { user } = useAuth()
  const { hasPermission } = usePermission()

  return (
    <div className="h-screen bg-black border-r border-stone-800 w-64">
      <div className="p-6">
        <h1 className="text-xl font-bold text-stone-100">RAG Enterprise</h1>
        <p className="text-sm text-stone-400">{user.role}</p>
      </div>

      <nav className="space-y-1 px-3">
        {/* Super-user menu */}
        {hasPermission('super-admin') && (
          <>
            <NavItem icon="⚙️" href="/super-admin">시스템 관리</NavItem>
            <NavItem icon="👥" href="/super-admin/users">사용자 관리</NavItem>
          </>
        )}

        {/* Admin menu */}
        {hasPermission('admin') && (
          <>
            <NavItem icon="📊" href="/admin">대시보드</NavItem>
            <NavItem icon="💰" href="/admin/billing">결제 관리</NavItem>
          </>
        )}

        {/* Staff menu */}
        {hasPermission('staff') && (
          <>
            <NavItem icon="🏭" href="/staff/manufacturing">제조 관리</NavItem>
            <NavItem icon="✅" href="/staff/quality">품질 관리</NavItem>
          </>
        )}

        {/* Customer menu (everyone) */}
        <NavItem icon="🔍" href="/search">제품 검색</NavItem>
        <NavItem icon="📦" href="/orders">주문 내역</NavItem>
      </nav>
    </div>
  )
}
```

### 3. Permission Hook

```tsx
// hooks/usePermission.ts
import { useAuth } from './useAuth'

type Role = 'super-user' | 'admin' | 'manager' | 'staff' | 'operator' | 'customer-vip' | 'customer'

const roleHierarchy: Record<Role, number> = {
  'super-user': 0,
  'admin': 1,
  'manager': 1,
  'staff': 2,
  'operator': 2,
  'customer-vip': 3,
  'customer': 3,
}

export function usePermission() {
  const { user } = useAuth()

  const hasPermission = (requiredRole: string): boolean => {
    if (!user) return false

    const userLevel = roleHierarchy[user.role as Role]
    const requiredLevel = roleHierarchy[requiredRole as Role]

    return userLevel <= requiredLevel
  }

  const canAccess = (resource: string, action: 'read' | 'write' | 'delete'): boolean => {
    // Permission matrix logic
    // ...
  }

  return { hasPermission, canAccess }
}
```

---

## API Integration

### Auth API

```typescript
// lib/auth.ts
export async function login(email: string, password: string) {
  const response = await fetch('http://localhost:8001/api/v1/saas/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })

  if (!response.ok) throw new Error('Login failed')

  const data = await response.json()
  // Store JWT token
  localStorage.setItem('token', data.access_token)
  localStorage.setItem('user', JSON.stringify(data.user))

  return data
}

export async function logout() {
  await fetch('http://localhost:8001/api/v1/saas/auth/logout', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    }
  })

  localStorage.removeItem('token')
  localStorage.removeItem('user')
}

export function getCurrentUser() {
  const userStr = localStorage.getItem('user')
  return userStr ? JSON.parse(userStr) : null
}
```

---

## Dashboard Features

### Super-user Dashboard

```
┌─────────────────────────────────────────────────────────┐
│  📊 시스템 개요                                          │
├─────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐│
│  │ 총 사용자 │  │  API 호출 │  │  활성세션 │  │ 시스템상태 ││
│  │  1,234  │  │ 45.2K    │  │   89     │  │   정상   ││
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘│
├─────────────────────────────────────────────────────────┤
│  📈 사용량 추이 (최근 7일)                                │
│  [Line Chart - API Calls, Users, Errors]                │
├─────────────────────────────────────────────────────────┤
│  👥 사용자 관리                                          │
│  [User Table - Name, Email, Role, Status, Actions]      │
└─────────────────────────────────────────────────────────┘
```

### Admin Dashboard

```
┌─────────────────────────────────────────────────────────┐
│  💼 관리자 대시보드                                       │
├─────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐│
│  │ 이번달수익│  │  신규고객 │  │   주문수  │  │  처리율  ││
│  │ $12.5K  │  │   34     │  │   156    │  │  94.2%  ││
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘│
├─────────────────────────────────────────────────────────┤
│  📊 매출 분석                                            │
│  [Bar Chart - Monthly Revenue]                          │
├─────────────────────────────────────────────────────────┤
│  🔑 API 키 관리                                          │
│  [API Keys Table - Name, Key, Created, Actions]         │
└─────────────────────────────────────────────────────────┘
```

### Staff Dashboard

```
┌─────────────────────────────────────────────────────────┐
│  🏭 제조 관리 대시보드                                    │
├─────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐│
│  │ 금일생산 │  │  불량률   │  │  재고량   │  │ 가동률   ││
│  │  1,245  │  │  2.1%    │  │  4,567   │  │  87.3%  ││
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘│
├─────────────────────────────────────────────────────────┤
│  ✅ 품질 관리                                            │
│  [Defect Detection Results + Vision Inspection]         │
├─────────────────────────────────────────────────────────┤
│  📦 재고 현황                                            │
│  [Inventory Table - Product, Stock, Location]           │
└─────────────────────────────────────────────────────────┘
```

### Customer Dashboard

```
┌─────────────────────────────────────────────────────────┐
│  🔍 제품 검색                                            │
├─────────────────────────────────────────────────────────┤
│  [Search Bar - "50ml PET 용기"]                         │
├─────────────────────────────────────────────────────────┤
│  📦 검색 결과                                            │
│  ┌────────────────┐  ┌────────────────┐                │
│  │ [Product Image]│  │ [Product Image]│                │
│  │  50ml PET병    │  │  100ml PET병   │                │
│  │  ₩1,200       │  │  ₩1,800        │                │
│  │  [견적 요청]   │  │  [견적 요청]    │                │
│  └────────────────┘  └────────────────┘                │
├─────────────────────────────────────────────────────────┤
│  📋 최근 주문                                            │
│  [Orders Table - Date, Product, Quantity, Status]       │
└─────────────────────────────────────────────────────────┘
```

---

## Routing & Protection

### Middleware (middleware.ts)

```typescript
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const token = request.cookies.get('token')?.value
  const { pathname } = request.nextUrl

  // Public routes
  if (pathname.startsWith('/login') || pathname.startsWith('/register')) {
    if (token) {
      // Already logged in, redirect to dashboard
      return NextResponse.redirect(new URL('/dashboard', request.url))
    }
    return NextResponse.next()
  }

  // Protected routes
  if (pathname.startsWith('/super-admin') ||
      pathname.startsWith('/admin') ||
      pathname.startsWith('/staff') ||
      pathname.startsWith('/customer')) {

    if (!token) {
      // Not logged in, redirect to login
      return NextResponse.redirect(new URL('/login', request.url))
    }

    // Check role-based access
    const user = getUserFromToken(token)

    if (pathname.startsWith('/super-admin') && user.role !== 'super-user') {
      return NextResponse.redirect(new URL('/unauthorized', request.url))
    }

    if (pathname.startsWith('/admin') && !['super-user', 'admin', 'manager'].includes(user.role)) {
      return NextResponse.redirect(new URL('/unauthorized', request.url))
    }

    // ... more role checks
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
}
```

---

## Installation Commands

```bash
# 1. Create Next.js project
npx create-next-app@latest frontend-v2 \
  --typescript \
  --tailwind \
  --app \
  --src-dir false \
  --import-alias "@/*"

# 2. Install shadcn-ui
npx shadcn-ui@latest init

# 3. Add components (Black + Natural theme)
npx shadcn-ui@latest add button
npx shadcn-ui@latest add card
npx shadcn-ui@latest add input
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add dropdown-menu
npx shadcn-ui@latest add sidebar
npx shadcn-ui@latest add table
npx shadcn-ui@latest add tabs
npx shadcn-ui@latest add avatar
npx shadcn-ui@latest add badge

# 4. Install additional dependencies
npm install recharts             # Charts
npm install lucide-react         # Icons
npm install react-hook-form      # Forms
npm install zod                  # Validation
npm install @tanstack/react-table  # Data tables
npm install date-fns             # Date utilities

# 5. Run development server
npm run dev
```

---

## Next Steps

1. ✅ **Design System Defined** - Black background + Natural theme
2. ⏳ **Create Next.js Project** - Initialize with shadcn-ui
3. ⏳ **Implement Auth System** - Multi-tier authentication
4. ⏳ **Build Dashboard Layouts** - Super-user, Admin, Staff, Customer
5. ⏳ **Integrate Backend APIs** - Connect to FastAPI (localhost:8001)
6. ⏳ **Add Role-based Routing** - Middleware + Permission hooks
7. ⏳ **Deploy** - Production deployment

---

**Status**: Architecture designed, ready for implementation
**Estimated Time**: 2-3 days for full implementation
**Dependencies**: Node.js ≥18, npm ≥9
