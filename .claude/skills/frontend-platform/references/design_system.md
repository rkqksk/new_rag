# Complete Design System Reference

**Purpose**: Complete design tokens and specifications for RAG Enterprise Platform.

---

## Color System

### Monochrome Palette

```css
/* Primary Backgrounds */
--color-bg-primary: #ffffff;      /* White, main content */
--color-bg-secondary: #f7f7f8;    /* Very light gray, page background */
--color-bg-tertiary: #ececf1;     /* Light gray, hover states */

/* Text Colors */
--color-text-primary: #2d333a;    /* Dark gray, main text (95% contrast) */
--color-text-secondary: #6e6e80;  /* Medium gray, secondary text */
--color-text-tertiary: #8e8ea0;   /* Light gray, subtle text */
--color-text-inverted: #ffffff;   /* White, on dark backgrounds */

/* Border Colors */
--color-border: #d1d5db;          /* Default border */
--color-border-hover: #9ca3af;    /* Hover state */
--color-border-focus: #10a37f;    /* Focus state (accent) */

/* Accent Colors (minimal usage) */
--color-accent: #10a37f;          /* Primary accent (teal) */
--color-accent-hover: #0d8968;    /* Hover state */
--color-accent-active: #0a6e54;   /* Active/pressed state */

/* State Colors */
--color-error: #ef4444;           /* Error/danger */
--color-error-bg: #fef2f2;        /* Error background */
--color-success: #10b981;         /* Success */
--color-success-bg: #f0fdf4;      /* Success background */
--color-warning: #f59e0b;         /* Warning */
--color-warning-bg: #fffbeb;      /* Warning background */
--color-info: #3b82f6;            /* Info */
--color-info-bg: #eff6ff;         /* Info background */

/* Overlay/Shadow */
--color-overlay: rgba(0, 0, 0, 0.5);
--color-shadow: rgba(0, 0, 0, 0.1);
```

### Usage Guidelines

**Primary Colors** (95% of UI):
- Backgrounds: White (#ffffff) and light grays
- Text: Dark gray (#2d333a) for high contrast
- Borders: Medium gray (#d1d5db)

**Accent Color** (5% of UI, only for):
- Primary CTAs (Sign in, Save, Submit)
- Links (when needed)
- Active states (selected nav items)

**State Colors** (only for feedback):
- Error messages
- Success notifications
- Warning alerts

---

## Typography

### Font Stack

```css
--font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI",
             Roboto, "Helvetica Neue", Arial, sans-serif,
             "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol";

--font-mono: ui-monospace, SFMono-Regular, "SF Mono",
             Menlo, Consolas, "Liberation Mono", monospace;
```

### Type Scale

```css
/* Font Sizes */
--text-xs: 12px;    /* 0.75rem */
--text-sm: 14px;    /* 0.875rem */
--text-base: 16px;  /* 1rem - DEFAULT */
--text-lg: 18px;    /* 1.125rem */
--text-xl: 20px;    /* 1.25rem */
--text-2xl: 24px;   /* 1.5rem */
--text-3xl: 30px;   /* 1.875rem */
--text-4xl: 36px;   /* 2.25rem */

/* Line Heights */
--leading-none: 1;
--leading-tight: 1.25;
--leading-snug: 1.375;
--leading-normal: 1.5;
--leading-relaxed: 1.625;
--leading-loose: 2;

/* Font Weights */
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;

/* Letter Spacing */
--tracking-tighter: -0.05em;
--tracking-tight: -0.025em;
--tracking-normal: 0em;
--tracking-wide: 0.025em;
--tracking-wider: 0.05em;
```

### Headings

```css
h1 {
  font-size: var(--text-3xl);      /* 30px */
  font-weight: var(--font-semibold);
  line-height: var(--leading-tight);
  letter-spacing: var(--tracking-tight);
  margin-bottom: var(--space-4);
}

h2 {
  font-size: var(--text-2xl);      /* 24px */
  font-weight: var(--font-semibold);
  line-height: var(--leading-tight);
  margin-bottom: var(--space-3);
}

h3 {
  font-size: var(--text-xl);       /* 20px */
  font-weight: var(--font-semibold);
  line-height: var(--leading-snug);
  margin-bottom: var(--space-3);
}

h4 {
  font-size: var(--text-lg);       /* 18px */
  font-weight: var(--font-medium);
  line-height: var(--leading-snug);
  margin-bottom: var(--space-2);
}
```

### Body Text

```css
body {
  font-size: var(--text-base);     /* 16px */
  font-weight: var(--font-normal);
  line-height: var(--leading-normal);
  color: var(--color-text-primary);
}

.text-sm {
  font-size: var(--text-sm);       /* 14px */
  line-height: var(--leading-normal);
}

.text-xs {
  font-size: var(--text-xs);       /* 12px */
  line-height: var(--leading-normal);
}
```

---

## Spacing System

### Space Scale

```css
--space-0: 0px;
--space-1: 4px;     /* 0.25rem */
--space-2: 8px;     /* 0.5rem */
--space-3: 12px;    /* 0.75rem */
--space-4: 16px;    /* 1rem */
--space-5: 20px;    /* 1.25rem */
--space-6: 24px;    /* 1.5rem */
--space-8: 32px;    /* 2rem */
--space-10: 40px;   /* 2.5rem */
--space-12: 48px;   /* 3rem */
--space-16: 64px;   /* 4rem */
--space-20: 80px;   /* 5rem */
--space-24: 96px;   /* 6rem */
```

### Usage Examples

```css
/* Component padding */
.button { padding: var(--space-3) var(--space-6); }  /* 12px 24px */
.card { padding: var(--space-6); }                    /* 24px */

/* Component margin */
.section { margin-bottom: var(--space-12); }          /* 48px */
.paragraph { margin-bottom: var(--space-4); }         /* 16px */

/* Gap in flexbox/grid */
.grid { gap: var(--space-4); }                        /* 16px */
```

---

## Border Radius

```css
--radius-none: 0px;
--radius-sm: 4px;
--radius-base: 6px;    /* DEFAULT */
--radius-md: 8px;
--radius-lg: 12px;
--radius-xl: 16px;
--radius-2xl: 24px;
--radius-full: 9999px; /* Pill shape */
```

### Usage

```css
.button { border-radius: var(--radius-base); }     /* 6px */
.card { border-radius: var(--radius-lg); }         /* 12px */
.modal { border-radius: var(--radius-xl); }        /* 16px */
.avatar { border-radius: var(--radius-full); }     /* Circle */
```

---

## Shadows

```css
--shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
--shadow-base: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
--shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
--shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
--shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
--shadow-2xl: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
```

### Usage (minimal, only for elevation)

```css
/* Elevated cards */
.card-elevated {
  box-shadow: var(--shadow-base);
}

/* Modals */
.modal {
  box-shadow: var(--shadow-xl);
}

/* Dropdowns */
.dropdown {
  box-shadow: var(--shadow-md);
}
```

---

## Transitions

```css
--transition-fast: 150ms;
--transition-base: 200ms;
--transition-slow: 300ms;

--ease-in: cubic-bezier(0.4, 0, 1, 1);
--ease-out: cubic-bezier(0, 0, 0.2, 1);
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
```

### Usage

```css
.button {
  transition: background var(--transition-base) var(--ease-in-out);
}

.link {
  transition: color var(--transition-fast) var(--ease-out);
}
```

---

## Z-Index Scale

```css
--z-0: 0;
--z-10: 10;
--z-20: 20;
--z-30: 30;
--z-40: 40;
--z-50: 50;

/* Named layers */
--z-dropdown: var(--z-40);
--z-modal: var(--z-50);
--z-toast: var(--z-50);
--z-tooltip: var(--z-40);
```

---

## Breakpoints

```css
--screen-sm: 640px;   /* Mobile landscape */
--screen-md: 768px;   /* Tablet */
--screen-lg: 1024px;  /* Desktop */
--screen-xl: 1280px;  /* Large desktop */
--screen-2xl: 1536px; /* Extra large */
```

### Media Queries

```css
/* Mobile first approach */
@media (min-width: 768px) {
  /* Tablet and up */
}

@media (min-width: 1024px) {
  /* Desktop and up */
}
```

---

## Grid System

```css
.container {
  width: 100%;
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 var(--space-4);
}

.container-sm {
  max-width: 768px;  /* Chat, auth pages */
}

.container-md {
  max-width: 1024px; /* Dashboard */
}

.container-lg {
  max-width: 1280px; /* Wide layouts */
}
```

---

## Component Tokens

### Buttons

```css
.btn {
  padding: var(--space-3) var(--space-6);
  border-radius: var(--radius-base);
  font-size: var(--text-base);
  font-weight: var(--font-medium);
  transition: all var(--transition-base);
  cursor: pointer;
  border: none;
}

.btn-sm {
  padding: var(--space-2) var(--space-4);
  font-size: var(--text-sm);
}

.btn-lg {
  padding: var(--space-4) var(--space-8);
  font-size: var(--text-lg);
}
```

### Inputs

```css
.input {
  width: 100%;
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-base);
  background: var(--color-bg-primary);
  font-size: var(--text-base);
  transition: border-color var(--transition-fast);
}

.input:focus {
  outline: none;
  border-color: var(--color-border-focus);
}
```

### Cards

```css
.card {
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
}
```

---

**Complete Tokens**: All design variables ready for implementation
**Framework Agnostic**: Works with CSS, SCSS, CSS-in-JS, Tailwind
**Consistent**: Every value from defined scales
