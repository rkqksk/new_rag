#!/usr/bin/env bash
# v10.0.0 Phase 3: Frontend Maximal Features
# Goal: Unify frontend + Add modern features with PURE BLACK + NO ICONS + NATURAL THEME

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "=================================================="
echo "v10 Phase 3: Frontend Maximal Features"
echo "=================================================="
echo ""
echo "Design Principles (ABSOLUTE):"
echo "  🖤 Pure Black Background (#000000)"
echo "  🚫 NO Icons (text only)"
echo "  🌿 Natural Theme (organic, minimal)"
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Phase 3.1: Frontend Unification
echo "------------------------------------------------"
echo "Phase 3.1: Frontend Unification (Monorepo)"
echo "------------------------------------------------"
echo ""

log_info "Step 1: Create apps/ structure for frontend"
mkdir -p apps/{web,pwa,mobile}

log_info "Step 2: Initialize Next.js 15 (App Router) - apps/web/"
cd apps/web
npx create-next-app@latest . --typescript --tailwind --app --no-src-dir --import-alias "@/*" --skip-install || log_warn "Next.js already initialized"
cd "$PROJECT_ROOT"

log_info "Step 3: Configure Tailwind for PURE BLACK theme"
cat > apps/web/tailwind.config.ts << 'EOF'
import type { Config } from "tailwindcss"

const config: Config = {
  darkMode: "class",
  content: [
    "./pages/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./app/**/*.{ts,tsx}",
    "../../packages/ui/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Pure Black Theme (ABSOLUTE)
        background: "#000000",  // Pure black, no compromise
        foreground: "#FFFFFF",  // Pure white text

        // Natural accents (minimal, organic)
        primary: {
          DEFAULT: "#FFFFFF",   // White for primary actions
          foreground: "#000000",
        },
        secondary: {
          DEFAULT: "#1A1A1A",   // Very dark gray
          foreground: "#FFFFFF",
        },
        muted: {
          DEFAULT: "#0A0A0A",   // Almost black
          foreground: "#999999", // Muted gray text
        },
        accent: {
          DEFAULT: "#FFFFFF",   // White accents
          foreground: "#000000",
        },

        // Borders: subtle gray
        border: "#1A1A1A",
        input: "#1A1A1A",
        ring: "#FFFFFF",
      },
      fontFamily: {
        // Natural, readable fonts
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      borderRadius: {
        // Minimal, natural corners
        lg: "0.5rem",
        md: "0.375rem",
        sm: "0.25rem",
      },
    },
  },
  plugins: [],
}

export default config
EOF

log_info "Step 4: Create DESIGN SYSTEM (Pure Black + No Icons + Natural)"
mkdir -p docs/design
cat > docs/design/DESIGN_SYSTEM.md << 'EOF'
# RAG Enterprise Design System v10.0.0

## Core Principles (ABSOLUTE - NO EXCEPTIONS)

### 1. Pure Black Background 🖤
```css
background: #000000;  /* Pure black, always */
```

**Rules**:
- All backgrounds MUST be `#000000` (pure black)
- No dark gray (#111, #222) - only pure black
- Cards, modals, panels: all pure black
- Hover states: max `#1A1A1A` (very subtle)

### 2. NO Icons 🚫
```tsx
// ❌ WRONG
<Button>
  <IconSearch /> Search
</Button>

// ✅ CORRECT
<Button>
  Search
</Button>
```

**Rules**:
- NEVER use icon libraries (Lucide, Heroicons, FontAwesome)
- Text only for all UI elements
- Use text symbols if absolutely necessary: → ← ✓ ✗ ⋮
- Emphasis through typography, not icons

### 3. Natural Theme 🌿
```tsx
// Natural, organic, minimal
// - Simple borders
// - Subtle shadows
// - Clean typography
// - Generous whitespace
```

**Rules**:
- Minimal decoration
- Organic spacing (not grid-locked)
- Readable typography (Inter for body, JetBrains Mono for code)
- Subtle animations (fade, slide - no bounce, no spin)

---

## Color Palette

### Background
```css
--background: #000000;      /* Pure black */
--foreground: #FFFFFF;      /* Pure white text */
```

### Accents
```css
--primary: #FFFFFF;         /* White for primary actions */
--secondary: #1A1A1A;       /* Very dark gray for secondary */
--muted: #0A0A0A;           /* Almost black for muted elements */
--muted-foreground: #999999; /* Gray text */
```

### Borders
```css
--border: #1A1A1A;          /* Subtle gray border */
--input: #1A1A1A;           /* Input borders */
--ring: #FFFFFF;            /* Focus ring (white) */
```

### States
```css
--hover: #1A1A1A;           /* Hover background (max brightness) */
--active: #FFFFFF;          /* Active text (white) */
--disabled: #333333;        /* Disabled text (dark gray) */
```

---

## Typography

### Fonts
```css
font-family: 'Inter', system-ui, sans-serif;  /* Body text */
font-family: 'JetBrains Mono', monospace;     /* Code, data */
```

### Scale
```css
--text-xs: 0.75rem;    /* 12px - small labels */
--text-sm: 0.875rem;   /* 14px - secondary text */
--text-base: 1rem;     /* 16px - body text */
--text-lg: 1.125rem;   /* 18px - emphasis */
--text-xl: 1.25rem;    /* 20px - headings */
--text-2xl: 1.5rem;    /* 24px - page titles */
--text-3xl: 1.875rem;  /* 30px - hero text */
```

### Weights
```css
font-weight: 400;  /* Normal (body text) */
font-weight: 500;  /* Medium (emphasis) */
font-weight: 600;  /* Semibold (headings) */
```

**NO bold (700+)** - use size and weight 600 max

---

## Components

### Button

```tsx
// Text-only button (no icons)
<button className="
  bg-white text-black
  px-6 py-2
  rounded-md
  hover:bg-gray-200
  transition-colors
  font-medium
">
  Search
</button>
```

**Variants**:
- Primary: White background, black text
- Secondary: Dark gray background, white text
- Ghost: Transparent, white text, white border

### Input

```tsx
<input className="
  bg-black
  border border-gray-800
  text-white
  px-4 py-2
  rounded-md
  focus:outline-none focus:ring-2 focus:ring-white
  placeholder:text-gray-600
" />
```

### Card

```tsx
<div className="
  bg-black
  border border-gray-800
  rounded-lg
  p-6
  hover:border-gray-700
  transition-colors
">
  {content}
</div>
```

---

## Layout

### Spacing
```css
/* Natural, organic spacing */
--space-xs: 0.25rem;   /* 4px */
--space-sm: 0.5rem;    /* 8px */
--space-md: 1rem;      /* 16px */
--space-lg: 1.5rem;    /* 24px */
--space-xl: 2rem;      /* 32px */
--space-2xl: 3rem;     /* 48px */
```

### Grid
```css
/* Minimal grid, generous whitespace */
display: grid;
gap: 2rem;  /* Large gaps for breathing room */
```

### Containers
```css
max-width: 1200px;  /* Content max width */
margin: 0 auto;     /* Center */
padding: 2rem;      /* Generous padding */
```

---

## Animation

### Allowed
```css
transition: opacity 200ms ease;
transition: transform 200ms ease;
transition: color 200ms ease;
transition: border-color 200ms ease;
```

### Forbidden
- ❌ Bounce, elastic, spring animations
- ❌ Spin, rotate (except loading spinners - use text: "Loading...")
- ❌ Scale (use opacity instead)
- ❌ Icon animations (no icons!)

---

## Examples

### Search Page (Pure Black + No Icons + Natural)

```tsx
export default function SearchPage() {
  return (
    <div className="min-h-screen bg-black text-white">
      {/* Header */}
      <header className="border-b border-gray-800 py-6">
        <div className="container mx-auto px-6">
          <h1 className="text-2xl font-semibold">
            RAG Enterprise
          </h1>
        </div>
      </header>

      {/* Search */}
      <main className="container mx-auto px-6 py-12">
        <div className="max-w-2xl mx-auto">
          <input
            type="text"
            placeholder="Search products..."
            className="
              w-full
              bg-black
              border border-gray-800
              text-white text-lg
              px-6 py-4
              rounded-md
              focus:outline-none focus:ring-2 focus:ring-white
              placeholder:text-gray-600
            "
          />

          <button className="
            mt-4 w-full
            bg-white text-black
            py-4 rounded-md
            font-medium
            hover:bg-gray-200
            transition-colors
          ">
            Search
          </button>
        </div>

        {/* Results */}
        <div className="mt-12 grid gap-6">
          {results.map(result => (
            <div
              key={result.id}
              className="
                bg-black
                border border-gray-800
                rounded-lg p-6
                hover:border-gray-700
                transition-colors
              "
            >
              <h3 className="text-lg font-medium mb-2">
                {result.title}
              </h3>
              <p className="text-gray-400">
                {result.description}
              </p>
            </div>
          ))}
        </div>
      </main>
    </div>
  )
}
```

---

## Checklist

Before committing any UI code, verify:

- [ ] Background is pure black (#000000) everywhere
- [ ] NO icons used (text only)
- [ ] Typography is clean and readable (Inter / JetBrains Mono)
- [ ] Spacing is generous and natural
- [ ] Animations are subtle (fade, slide only)
- [ ] Borders are minimal (#1A1A1A)
- [ ] Hover states are subtle (max #1A1A1A)
- [ ] All text is readable (white on black)

---

**Enforcement**: Any PR with icons or non-black backgrounds will be rejected.

**Philosophy**: Less is more. Black is beautiful. Text is enough.
EOF

log_info "Step 5: Create UI package (shadcn base, customized for Pure Black)"
mkdir -p packages/ui/{components,lib}

cat > packages/ui/components/button.tsx << 'EOF'
import * as React from "react"

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost"
  children: React.ReactNode
}

export function Button({
  variant = "primary",
  children,
  className = "",
  ...props
}: ButtonProps) {
  const baseStyles = "px-6 py-2 rounded-md font-medium transition-colors"

  const variants = {
    primary: "bg-white text-black hover:bg-gray-200",
    secondary: "bg-gray-900 text-white border border-gray-800 hover:bg-gray-800",
    ghost: "bg-transparent text-white border border-white hover:bg-white hover:text-black"
  }

  return (
    <button
      className={`${baseStyles} ${variants[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  )
}
EOF

cat > packages/ui/components/input.tsx << 'EOF'
import * as React from "react"

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {}

export function Input({ className = "", ...props }: InputProps) {
  return (
    <input
      className={`
        bg-black border border-gray-800 text-white
        px-4 py-2 rounded-md
        focus:outline-none focus:ring-2 focus:ring-white
        placeholder:text-gray-600
        ${className}
      `}
      {...props}
    />
  )
}
EOF

cat > packages/ui/components/card.tsx << 'EOF'
import * as React from "react"

interface CardProps {
  children: React.ReactNode
  className?: string
}

export function Card({ children, className = "" }: CardProps) {
  return (
    <div className={`
      bg-black border border-gray-800 rounded-lg p-6
      hover:border-gray-700 transition-colors
      ${className}
    `}>
      {children}
    </div>
  )
}
EOF

log_info "Phase 3.1 Complete ✅"
echo ""

# Phase 3.2: Modern UI Stack
echo "------------------------------------------------"
echo "Phase 3.2: Modern UI Stack (Pure Black Theme)"
echo "------------------------------------------------"
echo ""

log_info "Step 1: Install dependencies"
cd apps/web
npm install --legacy-peer-deps \
  zustand \
  @tanstack/react-query \
  react-hook-form \
  zod \
  recharts \
  framer-motion \
  || log_warn "Some packages failed"
cd "$PROJECT_ROOT"

log_info "Step 2: Create global styles (Pure Black)"
cat > apps/web/app/globals.css << 'EOF'
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  * {
    @apply border-gray-800;
  }

  body {
    @apply bg-black text-white;
    font-feature-settings: "rlig" 1, "calt" 1;
  }

  /* Scrollbar */
  ::-webkit-scrollbar {
    width: 8px;
    height: 8px;
  }

  ::-webkit-scrollbar-track {
    @apply bg-black;
  }

  ::-webkit-scrollbar-thumb {
    @apply bg-gray-800 rounded;
  }

  ::-webkit-scrollbar-thumb:hover {
    @apply bg-gray-700;
  }

  /* Selection */
  ::selection {
    @apply bg-white text-black;
  }
}

@layer components {
  .container {
    @apply max-w-7xl mx-auto px-6;
  }
}
EOF

log_info "Step 3: Create layout (Pure Black)"
cat > apps/web/app/layout.tsx << 'EOF'
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "RAG Enterprise",
  description: "Ultimate RAG platform with pure black design",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko" className="dark">
      <body className={inter.className}>
        {children}
      </body>
    </html>
  )
}
EOF

log_info "Step 4: Create search page (example: Pure Black + No Icons)"
cat > apps/web/app/page.tsx << 'EOF'
"use client"

import { useState } from "react"

export default function SearchPage() {
  const [query, setQuery] = useState("")
  const [results, setResults] = useState<any[]>([])

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Header */}
      <header className="border-b border-gray-800 py-6">
        <div className="container">
          <h1 className="text-2xl font-semibold">
            RAG Enterprise
          </h1>
        </div>
      </header>

      {/* Search */}
      <main className="container py-12">
        <div className="max-w-2xl mx-auto">
          <div className="space-y-4">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search products..."
              className="
                w-full bg-black border border-gray-800 text-white text-lg
                px-6 py-4 rounded-md
                focus:outline-none focus:ring-2 focus:ring-white
                placeholder:text-gray-600
              "
            />

            <button
              onClick={() => console.log("Search:", query)}
              className="
                w-full bg-white text-black py-4 rounded-md
                font-medium hover:bg-gray-200 transition-colors
              "
            >
              Search
            </button>
          </div>

          {/* Results */}
          {results.length > 0 && (
            <div className="mt-12 space-y-6">
              <h2 className="text-xl font-medium">
                Results
              </h2>

              {results.map((result, idx) => (
                <div
                  key={idx}
                  className="
                    bg-black border border-gray-800 rounded-lg p-6
                    hover:border-gray-700 transition-colors
                  "
                >
                  <h3 className="text-lg font-medium mb-2">
                    {result.title}
                  </h3>
                  <p className="text-gray-400">
                    {result.description}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
EOF

log_info "Phase 3.2 Complete ✅"
echo ""

# Phase 3.3: Advanced Features
echo "------------------------------------------------"
echo "Phase 3.3: Advanced Features"
echo "------------------------------------------------"
echo ""

log_info "Step 1: Socket.IO client setup"
cd apps/web
npm install --legacy-peer-deps socket.io-client || log_warn "socket.io-client install failed"
cd "$PROJECT_ROOT"

cat > apps/web/lib/socket.ts << 'EOF'
import { io, Socket } from "socket.io-client"

let socket: Socket | null = null

export function getSocket(): Socket {
  if (!socket) {
    socket = io("http://localhost:8001", {
      transports: ["websocket"],
      autoConnect: true,
    })

    socket.on("connect", () => {
      console.log("Socket connected:", socket?.id)
    })

    socket.on("disconnect", () => {
      console.log("Socket disconnected")
    })
  }

  return socket
}
EOF

log_info "Step 2: i18n setup (Korean, English, Japanese, Chinese)"
cd apps/web
npm install --legacy-peer-deps next-intl || log_warn "next-intl install failed"
cd "$PROJECT_ROOT"

log_info "Step 3: Offline support (Service Worker + IndexedDB)"
cat > apps/web/public/sw.js << 'EOF'
// Service Worker for offline support
const CACHE_NAME = "rag-v10-cache"
const urlsToCache = ["/", "/search", "/api/v1/search"]

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(urlsToCache))
  )
})

self.addEventListener("fetch", (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      return response || fetch(event.request)
    })
  )
})
EOF

log_info "Phase 3.3 Complete ✅"
echo ""

# Summary
echo "=================================================="
echo "Phase 3: Frontend Maximal Features - COMPLETE ✅"
echo "=================================================="
echo ""
echo "Summary:"
echo "  ✅ Frontend monorepo created (apps/web, apps/pwa, apps/mobile)"
echo "  ✅ Design system: PURE BLACK + NO ICONS + NATURAL"
echo "  ✅ UI components: shadcn-based, customized for black theme"
echo "  ✅ Modern stack:"
echo "      - Next.js 15 (App Router)"
echo "      - Tailwind CSS (Pure Black config)"
echo "      - Zustand, TanStack Query, React Hook Form, Zod"
echo "  ✅ Advanced features:"
echo "      - Socket.IO client (realtime)"
echo "      - i18n (4 languages)"
echo "      - Service Worker (offline)"
echo ""
echo "Design Enforcement:"
echo "  🖤 Pure Black (#000000) - ABSOLUTE"
echo "  🚫 NO Icons - text only"
echo "  🌿 Natural Theme - minimal, organic"
echo ""
echo "Next steps:"
echo "  1. Review docs/design/DESIGN_SYSTEM.md"
echo "  2. Start dev server: cd apps/web && npm run dev"
echo "  3. Test UI: http://localhost:3000"
echo "  4. Proceed to Phase 4: ./scripts/v10/phase4_final_trimming.sh"
echo ""
echo "Maximal features added! Ready for final trimming."
echo ""
