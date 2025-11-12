# PETER Frontend v2.0

**Modern React Dashboard** with Black Background + Natural Theme

## 🎨 Design System

- **Framework**: Next.js 14 (App Router)
- **UI Library**: shadcn-ui (Radix UI primitives)
- **Styling**: Tailwind CSS
- **Color Scheme**: Black (#000000) + Natural (Stone palette)
- **Theme**: Natural earthy tones for professional enterprise feel

## 🔐 Authentication System

### Multi-tier User Hierarchy

```
Level 0: Super-user     ← 시스템 관리자 (모든 권한)
Level 1: Admin/Manager  ← 내부 관리자 (전체 조회, 승인/반려)
Level 2: Staff/Operator ← 내부 직원 (데이터 입력, 부분 조회)
Level 3: Customer (VIP/Regular) ← 고객 (제품 검색, 주문 관리)
```

### Demo Accounts

| Role | Email | Password | Access |
|------|-------|----------|--------|
| Super-user | super@example.com | demo1234 | 모든 기능 |
| Admin | admin@example.com | demo1234 | 관리 대시보드 |
| Staff | staff@example.com | demo1234 | 제조/품질 관리 |
| Customer | customer@example.com | demo1234 | 제품 검색 |

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Open browser
http://localhost:3000
```

## 📁 Project Structure

```
frontend-v2/
├── app/
│   ├── (auth)/           # Authentication pages
│   │   └── login/        # Login page ✅
│   ├── (dashboard)/      # Protected dashboard (TODO)
│   │   ├── super-admin/  # Super-user dashboard
│   │   ├── admin/        # Admin dashboard
│   │   ├── staff/        # Staff portal
│   │   └── customer/     # Customer area
│   ├── globals.css       # Black + Natural theme ✅
│   ├── layout.tsx        # Root layout ✅
│   └── page.tsx          # Landing page ✅
│
├── components/
│   └── ui/               # shadcn-ui components ✅
│       ├── button.tsx
│       ├── card.tsx
│       ├── input.tsx
│       └── label.tsx
│
├── lib/
│   └── utils.ts          # Utility functions ✅
│
├── hooks/                # Custom hooks (TODO)
│   ├── useAuth.ts
│   └── usePermission.ts
│
└── types/                # TypeScript types (TODO)
    ├── user.ts
    └── auth.ts
```

## 🎯 Features

### Implemented ✅

- [x] Next.js 14 project structure
- [x] Black background + Natural (Stone) color theme
- [x] Tailwind CSS configuration
- [x] shadcn-ui setup (Button, Card, Input, Label)
- [x] Landing page with feature overview
- [x] Login page with demo accounts
- [x] Responsive design
- [x] TypeScript support

### In Progress 🔄

- [ ] Authentication API integration
- [ ] Dashboard layouts (Super-user, Admin, Staff, Customer)
- [ ] Permission-based routing
- [ ] User profile management

### Planned 📋

- [ ] Super-user dashboard (System overview, User management)
- [ ] Admin dashboard (Analytics, Billing, API keys)
- [ ] Staff portal (Manufacturing, Quality control, Inventory)
- [ ] Customer area (Product search, Orders, Support)
- [ ] Real-time notifications
- [ ] Dark mode toggle (optional - already dark by default)

## 🎨 Color Palette

```css
/* Natural (Stone) Theme */
background: #000000        /* Pure black */
foreground: #fafaf9        /* Stone-50 (light text) */

card: #1c1917             /* Stone-900 (dark cards) */
border: #292524           /* Stone-800 (borders) */
primary: #d6d3d1          /* Stone-300 (accents) */
muted: #78716c            /* Stone-500 (muted text) */
```

## 📡 API Integration

### Backend API

- **Base URL**: `http://localhost:8001`
- **Auth Endpoint**: `/api/v1/saas/auth/login`
- **Protected Routes**: Require JWT token in Authorization header

### Example API Call

```typescript
const response = await fetch('/api/v1/saas/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password }),
})

const data = await response.json()
localStorage.setItem('token', data.access_token)
```

## 🛠️ Tech Stack

- **Framework**: Next.js 14.2
- **Language**: TypeScript 5.7
- **Styling**: Tailwind CSS 3.4
- **UI Components**: shadcn-ui (Radix UI)
- **Icons**: Lucide React
- **Forms**: React Hook Form + Zod
- **Tables**: TanStack Table
- **Charts**: Recharts
- **State**: React Context (no Redux needed for auth)

## 📚 Documentation

- [Architecture](../docs/FRONTEND_V2_ARCHITECTURE.md) - Detailed system architecture
- [shadcn-ui Docs](https://ui.shadcn.com/) - Component documentation
- [Next.js Docs](https://nextjs.org/docs) - Framework documentation
- [Tailwind CSS](https://tailwindcss.com/docs) - Styling documentation

## 🔄 Development Workflow

```bash
# Install new shadcn-ui component
npx shadcn-ui@latest add <component-name>

# Example: Add dropdown menu
npx shadcn-ui@latest add dropdown-menu

# Run linter
npm run lint

# Build for production
npm run build

# Start production server
npm run start
```

## 🌐 Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## 📄 License

MIT

## 👥 Authors

RAG Enterprise Team

---

**Version**: 2.0.0
**Last Updated**: 2025-11-08
**Status**: In Development 🔄
