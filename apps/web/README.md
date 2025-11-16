# RAG Enterprise Web App

**Framework**: Next.js 15
**Theme**: Pure Black (#000000)
**Design**: NO Icons, Text Only, Natural

## Design Principles (ABSOLUTE)

1. **Pure Black Background**: `#000000` - Always, no exceptions
2. **NO Icons**: Text only, no icon libraries (Lucide, Heroicons, etc.)
3. **Natural Theme**: Minimal, organic, clean typography

## Quick Start

```bash
cd apps/web
npm install
npm run dev
```

Open: http://localhost:3000

## Structure

```
apps/web/
├── app/
│   ├── layout.tsx (Root layout)
│   ├── page.tsx (Search page - Pure Black)
│   └── globals.css (Pure Black styles)
├── components/ (UI components - NO icons)
├── lib/ (Utilities)
└── public/ (Static assets)
```

## Design Rules

### Colors
- Background: `#000000` (pure black)
- Text: `#FFFFFF` (pure white)
- Border: `#1A1A1A` (very dark gray)
- Hover: `#1A1A1A` (max brightness)

### Typography
- Body: Inter (sans-serif)
- Code: JetBrains Mono (monospace)
- Sizes: text-base to text-2xl (no huge sizes)

### Components
- NO icon libraries
- Text-only buttons
- Simple borders
- Minimal shadows
- Natural spacing

## Examples

### Button (Text Only)
```tsx
<button className="bg-white text-black px-6 py-2 rounded-md hover:bg-gray-200">
  Search
</button>
```

### Input (Pure Black)
```tsx
<input className="bg-black border border-gray-800 text-white px-4 py-2 rounded-md" />
```

### Card (No Icons)
```tsx
<div className="bg-black border border-gray-800 rounded-lg p-6">
  <h3 className="text-lg font-medium mb-2">Title</h3>
  <p className="text-gray-400">Description</p>
</div>
```

## Enforcement

Any PR with:
- Non-black backgrounds
- Icons
- Overly decorative elements

Will be **rejected**.

## Version

v10.0.0 - Pure Black Design
