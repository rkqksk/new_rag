# @rag/ui

Shared UI components for RAG Enterprise v10.0.0

## Purpose

Platform-agnostic React components with Pure Black design.

## Design Rules (ABSOLUTE)

- **Pure Black**: #000000 background (always)
- **NO Icons**: Text-only UI
- **Natural Theme**: Minimal, organic

## Usage

```tsx
import { Button, Input, Card } from '@rag/ui'

export default function MyComponent() {
  return (
    <Card>
      <Input placeholder="Search..." />
      <Button>Submit</Button>
    </Card>
  )
}
```

## Components

- Button
- Input
- Card
- Modal
- Table
- Form
- SearchBar
- ProductCard

## Structure

```
packages/ui/
├── package.json
├── index.ts
├── components/
│   ├── Button.tsx
│   ├── Input.tsx
│   ├── Card.tsx
│   └── ...
└── styles/
    └── theme.ts
```

## Version

10.0.0 - Unified Maximum
