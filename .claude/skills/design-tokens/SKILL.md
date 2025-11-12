# Design Tokens Skill

## Overview
Expert in creating and managing design token systems for consistent theming across platforms.

## Trigger Words
- design tokens
- design system
- theme system
- style tokens
- css variables
- token architecture

## Capabilities

### Token Architecture

#### Token Structure
```json
{
  "color": {
    "$type": "color",
    "base": {
      "gray": {
        "50": { "$value": "#f9fafb" },
        "100": { "$value": "#f3f4f6" },
        "900": { "$value": "#111827" }
      }
    },
    "semantic": {
      "primary": { "$value": "{color.base.blue.500}" },
      "secondary": { "$value": "{color.base.gray.600}" },
      "error": { "$value": "{color.base.red.500}" },
      "success": { "$value": "{color.base.green.500}" }
    }
  },
  "spacing": {
    "$type": "dimension",
    "xs": { "$value": "0.25rem" },
    "sm": { "$value": "0.5rem" },
    "md": { "$value": "1rem" },
    "lg": { "$value": "1.5rem" },
    "xl": { "$value": "2rem" }
  },
  "typography": {
    "$type": "typography",
    "fontSize": {
      "xs": { "$value": "0.75rem" },
      "sm": { "$value": "0.875rem" },
      "base": { "$value": "1rem" },
      "lg": { "$value": "1.125rem" },
      "xl": { "$value": "1.25rem" }
    },
    "fontWeight": {
      "normal": { "$value": "400" },
      "medium": { "$value": "500" },
      "semibold": { "$value": "600" },
      "bold": { "$value": "700" }
    }
  }
}
```

### Platform-Specific Tokens

#### Web (CSS Variables)
```css
:root {
  /* Colors */
  --color-primary: #3b82f6;
  --color-secondary: #4b5563;
  --color-error: #ef4444;
  --color-success: #10b981;

  /* Spacing */
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  --spacing-xl: 2rem;

  /* Typography */
  --font-size-xs: 0.75rem;
  --font-size-sm: 0.875rem;
  --font-size-base: 1rem;
  --font-size-lg: 1.125rem;
  --font-size-xl: 1.25rem;

  /* Shadows */
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
}

/* Dark mode */
[data-theme="dark"] {
  --color-primary: #60a5fa;
  --color-background: #111827;
  --color-text: #f9fafb;
}
```

#### React Native
```typescript
export const tokens = {
  colors: {
    primary: '#3B82F6',
    secondary: '#4B5563',
    error: '#EF4444',
    success: '#10B981',
    // Platform specific
    ios: {
      systemBlue: '#007AFF',
      systemGray: '#8E8E93'
    },
    android: {
      primaryDark: '#1976D2',
      accent: '#FF4081'
    }
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32
  },
  typography: {
    fontSize: {
      xs: 12,
      sm: 14,
      base: 16,
      lg: 18,
      xl: 20
    }
  }
}
```

#### Tailwind Config
```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: 'var(--color-primary)',
        secondary: 'var(--color-secondary)',
        error: 'var(--color-error)',
        success: 'var(--color-success)'
      },
      spacing: {
        'xs': 'var(--spacing-xs)',
        'sm': 'var(--spacing-sm)',
        'md': 'var(--spacing-md)',
        'lg': 'var(--spacing-lg)',
        'xl': 'var(--spacing-xl)'
      },
      fontSize: {
        'xs': 'var(--font-size-xs)',
        'sm': 'var(--font-size-sm)',
        'base': 'var(--font-size-base)',
        'lg': 'var(--font-size-lg)',
        'xl': 'var(--font-size-xl)'
      }
    }
  }
}
```

### Token Management

#### Style Dictionary Configuration
```javascript
module.exports = {
  source: ['tokens/**/*.json'],
  platforms: {
    css: {
      transformGroup: 'css',
      buildPath: 'build/css/',
      files: [{
        destination: 'tokens.css',
        format: 'css/variables'
      }]
    },
    js: {
      transformGroup: 'js',
      buildPath: 'build/js/',
      files: [{
        destination: 'tokens.js',
        format: 'javascript/module'
      }]
    },
    ios: {
      transformGroup: 'ios',
      buildPath: 'build/ios/',
      files: [{
        destination: 'Tokens.swift',
        format: 'ios-swift/class.swift'
      }]
    },
    android: {
      transformGroup: 'android',
      buildPath: 'build/android/',
      files: [{
        destination: 'tokens.xml',
        format: 'android/resources'
      }]
    }
  }
}
```

### Theme System Implementation

#### React Context Provider
```typescript
import { createContext, useContext, useState } from 'react'

interface ThemeTokens {
  colors: Record<string, string>
  spacing: Record<string, string>
  typography: Record<string, any>
}

const ThemeContext = createContext<{
  tokens: ThemeTokens
  theme: 'light' | 'dark'
  setTheme: (theme: 'light' | 'dark') => void
}>()

export const ThemeProvider = ({ children }) => {
  const [theme, setTheme] = useState<'light' | 'dark'>('light')

  const tokens = useMemo(() => ({
    colors: theme === 'light' ? lightColors : darkColors,
    spacing,
    typography
  }), [theme])

  return (
    <ThemeContext.Provider value={{ tokens, theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export const useTheme = () => useContext(ThemeContext)
```

#### CSS-in-JS Integration
```typescript
import { css } from '@emotion/react'

const useTokens = () => {
  const { tokens } = useTheme()

  return {
    button: css`
      background-color: ${tokens.colors.primary};
      padding: ${tokens.spacing.md};
      font-size: ${tokens.typography.fontSize.base};
      border-radius: ${tokens.borderRadius.md};
    `
  }
}
```

### Token Documentation

#### Storybook Integration
```typescript
// .storybook/preview.js
export const parameters = {
  designToken: {
    styleInjection: true,
    defaultTab: 'Colors'
  }
}

// Token story
export const ColorPalette = () => (
  <div>
    {Object.entries(tokens.colors).map(([name, value]) => (
      <div key={name} style={{ backgroundColor: value }}>
        <span>{name}</span>
        <span>{value}</span>
      </div>
    ))}
  </div>
)
```

### Token Validation

```typescript
// Validate token consistency
const validateTokens = (tokens: TokenConfig) => {
  const errors: string[] = []

  // Check color contrast
  Object.entries(tokens.colors).forEach(([name, value]) => {
    if (name.includes('text')) {
      const contrast = getContrastRatio(value, tokens.colors.background)
      if (contrast < 4.5) {
        errors.push(`Low contrast: ${name} on background`)
      }
    }
  })

  // Check spacing scale
  const spacingValues = Object.values(tokens.spacing)
  const isConsistent = spacingValues.every((val, i) => {
    if (i === 0) return true
    return val > spacingValues[i - 1]
  })

  if (!isConsistent) {
    errors.push('Spacing scale is not consistent')
  }

  return errors
}
```

### Migration Strategy

```typescript
// Migrate from hardcoded values to tokens
const migrateToTokens = (code: string) => {
  const replacements = {
    '#3B82F6': 'var(--color-primary)',
    '16px': 'var(--spacing-md)',
    '14px': 'var(--font-size-sm)'
  }

  let migrated = code
  Object.entries(replacements).forEach(([old, token]) => {
    migrated = migrated.replace(new RegExp(old, 'g'), token)
  })

  return migrated
}
```

## Token Formats

### JSON (W3C Design Tokens Format)
```json
{
  "$schema": "https://design-tokens.github.io/community-group/schemas/v1.json",
  "color": {
    "$type": "color",
    "primary": {
      "$value": "#3B82F6",
      "$description": "Primary brand color"
    }
  }
}
```

### YAML
```yaml
colors:
  primary: '#3B82F6'
  secondary: '#4B5563'

spacing:
  xs: 4px
  sm: 8px
  md: 16px
```

## Build Pipeline

```bash
# Build tokens for all platforms
npm run tokens:build

# Watch mode
npm run tokens:watch

# Validate tokens
npm run tokens:validate

# Generate documentation
npm run tokens:docs
```

## Related Skills
- component-library
- visual-testing
- frontend-platform
- design-system-agent