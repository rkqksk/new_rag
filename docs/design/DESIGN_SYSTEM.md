# RAG Enterprise Design System v10.0.0

**Philosophy**: Pure Black + Natural + Minimal

---

## 🖤 Core Principles (ABSOLUTE)

### 1. Pure Black Background

**Rule**: Background MUST be `#000000` (pure black, RGB: 0,0,0)

```css
/* ✅ CORRECT */
background: #000000;
background-color: rgb(0, 0, 0);

/* ❌ WRONG */
background: #111111;
background: #1a1a1a;
background: hsl(0, 0%, 5%);
```

**Rationale**:
- OLED power savings
- Maximum contrast
- Professional aesthetic
- No ambiguity

### 2. NO Icons

**Rule**: ALL UI elements MUST use text only. NO icons, NO emojis, NO symbols.

```tsx
/* ✅ CORRECT */
<button>Search</button>
<button>Submit</button>
<button>Close</button>

/* ❌ WRONG */
<button>🔍 Search</button>
<button><SearchIcon /> Search</button>
<button>⨯</button>
```

**Rationale**:
- Universal accessibility
- Language-agnostic
- Faster rendering
- Simpler maintenance

### 3. Natural Theme

**Rule**: Minimal, organic design. No gradients, no shadows (except subtle), no animations (except functional).

```css
/* ✅ CORRECT - Subtle, functional */
border: 1px solid #1a1a1a;
box-shadow: 0 1px 2px rgba(0,0,0,0.1);
transition: opacity 0.2s ease;

/* ❌ WRONG - Excessive */
background: linear-gradient(45deg, #111, #222);
box-shadow: 0 10px 40px rgba(255,255,255,0.5);
animation: pulse 2s infinite;
```

---

## 🎨 Color Palette

### Primary Colors

```css
--background: #000000;      /* Pure black - ABSOLUTE */
--foreground: #FFFFFF;      /* Pure white text */
--primary: #FFFFFF;         /* Primary actions */
--primary-foreground: #000000;
```

### Neutral Scale

```css
--border: #1A1A1A;          /* Subtle borders */
--input: #0A0A0A;           /* Input backgrounds */
--ring: #FFFFFF;            /* Focus rings */
--muted: #8A8A8A;           /* Muted text */
--muted-foreground: #A0A0A0;
```

### Semantic Colors

```css
--success: #22C55E;         /* Success states */
--warning: #EAB308;         /* Warning states */
--error: #EF4444;           /* Error states */
--info: #3B82F6;            /* Info states */
```

---

## 📐 Typography

### Font Families

```css
/* Body text */
font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;

/* Code/Monospace */
font-family: 'JetBrains Mono', 'Fira Code', monospace;

/* Headings (same as body for consistency) */
font-family: 'Inter', sans-serif;
```

### Font Scale

```css
/* Headings */
h1: 2rem (32px)     font-weight: 600
h2: 1.5rem (24px)   font-weight: 600
h3: 1.25rem (20px)  font-weight: 600
h4: 1rem (16px)     font-weight: 600

/* Body */
body: 0.875rem (14px)  font-weight: 400
small: 0.75rem (12px)  font-weight: 400
```

### Line Heights

```css
--line-height-tight: 1.25;
--line-height-normal: 1.5;
--line-height-relaxed: 1.75;
```

---

## 📏 Spacing

### Scale (Tailwind-compatible)

```
0:   0px
1:   4px
2:   8px
3:   12px
4:   16px
6:   24px
8:   32px
12:  48px
16:  64px
```

### Usage

```tsx
/* ✅ CORRECT - Consistent spacing */
<div className="p-6 space-y-4">
  <h1 className="mb-2">Title</h1>
  <p className="mb-4">Content</p>
</div>

/* ❌ WRONG - Random spacing */
<div style={{ padding: '23px' }}>
  <h1 style={{ marginBottom: '17px' }}>Title</h1>
</div>
```

---

## 🧩 Component Library

### Button

```tsx
/* Primary */
<button className="bg-white text-black px-6 py-3 rounded hover:bg-gray-200">
  Submit
</button>

/* Secondary */
<button className="border border-gray-800 text-white px-6 py-3 rounded hover:border-gray-600">
  Cancel
</button>

/* Danger */
<button className="bg-red-600 text-white px-6 py-3 rounded hover:bg-red-700">
  Delete
</button>
```

### Input

```tsx
<input
  type="text"
  placeholder="Search..."
  className="w-full bg-black border border-gray-800 text-white px-4 py-3 rounded focus:border-white focus:outline-none"
/>
```

### Card

```tsx
<div className="border border-gray-800 rounded-lg p-6 bg-black">
  <h3 className="text-lg font-semibold mb-2">Card Title</h3>
  <p className="text-gray-400">Card content goes here.</p>
</div>
```

---

## ⚙️ Tailwind Configuration

```typescript
// tailwind.config.ts
import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: '#000000',  // ABSOLUTE: Pure black
        foreground: '#FFFFFF',
        primary: {
          DEFAULT: '#FFFFFF',
          foreground: '#000000',
        },
        border: '#1A1A1A',
        input: '#0A0A0A',
        ring: '#FFFFFF',
        muted: {
          DEFAULT: '#8A8A8A',
          foreground: '#A0A0A0',
        },
      },
    },
  },
}

export default config
```

---

## 🚫 What NOT to Do

### ❌ Never use icons

```tsx
/* WRONG */
<FaSearch />
<Icon name="search" />
<i className="fa fa-search"></i>
```

### ❌ Never use non-black backgrounds

```tsx
/* WRONG */
<div className="bg-gray-900">  /* Not pure black */
<div style={{ background: '#111' }}>
```

### ❌ Never use emojis

```tsx
/* WRONG */
<button>🔍 Search</button>
<h1>Welcome 👋</h1>
```

### ❌ Never use excessive effects

```tsx
/* WRONG */
<div className="shadow-2xl blur-lg backdrop-filter">
<button className="animate-bounce bg-gradient-to-r">
```

---

## ✅ Examples

### Good Search Page

```tsx
export default function SearchPage() {
  return (
    <div className="min-h-screen bg-black text-white">
      <header className="border-b border-gray-800 py-6">
        <h1 className="text-2xl font-semibold">RAG Enterprise</h1>
      </header>

      <main className="container mx-auto px-6 py-12">
        <input
          type="text"
          placeholder="Search products..."
          className="w-full bg-black border border-gray-800 text-white px-6 py-4 rounded-lg focus:border-white focus:outline-none mb-6"
        />

        <button className="w-full bg-white text-black py-4 rounded-lg font-semibold hover:bg-gray-200">
          Search
        </button>
      </main>
    </div>
  )
}
```

### Good Product Card

```tsx
export function ProductCard({ product }: { product: Product }) {
  return (
    <div className="border border-gray-800 rounded-lg p-6 bg-black hover:border-gray-600 transition-colors">
      <h3 className="text-lg font-semibold mb-2">{product.name}</h3>
      <p className="text-gray-400 mb-4">{product.description}</p>
      <div className="flex justify-between items-center">
        <span className="text-xl font-bold">{product.price}</span>
        <button className="border border-gray-800 px-4 py-2 rounded hover:border-white">
          Add to Cart
        </button>
      </div>
    </div>
  )
}
```

---

## 📱 Responsive Design

### Breakpoints

```css
sm: 640px   /* Mobile landscape */
md: 768px   /* Tablet */
lg: 1024px  /* Desktop */
xl: 1280px  /* Large desktop */
2xl: 1536px /* Extra large */
```

### Mobile-First

```tsx
/* ✅ CORRECT - Mobile first */
<div className="p-4 md:p-6 lg:p-12">
  <h1 className="text-xl md:text-2xl lg:text-4xl">Title</h1>
</div>

/* ❌ WRONG - Desktop first */
<div className="p-12 lg:p-6 md:p-4">
```

---

## ♿ Accessibility

### Focus States

```tsx
/* Always provide visible focus states */
<button className="focus:outline-none focus:ring-2 focus:ring-white">
  Click me
</button>
```

### Semantic HTML

```tsx
/* ✅ CORRECT */
<button>Submit</button>
<nav><a href="/about">About</a></nav>

/* ❌ WRONG */
<div onClick={submit}>Submit</div>
<div><div onClick={navigate}>About</div></div>
```

### ARIA Labels

```tsx
/* Use when text alone isn't clear */
<button aria-label="Close dialog">Close</button>
<input aria-label="Search products" placeholder="Search..." />
```

---

## 🧪 Testing

### Visual Regression

- Background MUST be `rgb(0, 0, 0)`
- Text MUST be readable (WCAG AA: 4.5:1 contrast)
- NO icons present
- NO emojis present

### Code Linting

```bash
# Check for icon imports
grep -r "Icon" apps/web/app/
grep -r "fa-" apps/web/app/

# Check for non-black backgrounds
grep -r "bg-gray-9" apps/web/app/
grep -r "background.*#[^0]" apps/web/app/
```

---

## 📦 Package: @rag/ui

All shared components MUST follow this design system.

```tsx
// packages/ui/components/Button.tsx
export function Button({ children, variant = 'primary' }: ButtonProps) {
  const variants = {
    primary: 'bg-white text-black hover:bg-gray-200',
    secondary: 'border border-gray-800 text-white hover:border-white',
    danger: 'bg-red-600 text-white hover:bg-red-700',
  }

  return (
    <button className={`px-6 py-3 rounded font-semibold ${variants[variant]}`}>
      {children}
    </button>
  )
}
```

---

## 📚 Resources

- **Tailwind Docs**: https://tailwindcss.com
- **shadcn/ui**: https://ui.shadcn.com (base, customized for Pure Black)
- **WCAG Guidelines**: https://www.w3.org/WAI/WCAG21/quickref/

---

## 🔄 Version History

- **v10.0.0**: Initial Pure Black design system
- **ABSOLUTE RULES**: Pure Black (#000000), NO icons, Natural theme

---

**Enforcement**: These rules are ABSOLUTE and apply to ALL code contributions.

**Validation**: `grep -r "bg-gray-9" apps/ packages/` should return ZERO results.

**Questions**: See `apps/web/README.md` or ask the team.

---

**v10.0.0** | **Pure Black + Natural + Minimal** | **ABSOLUTE**
