# Component Implementation Guide

**Version**: 1.0.0
**Date**: 2025-11-12

Practical guide for implementing shared components across web, PWA, and React Native.

---

## Table of Contents
1. [Monorepo Setup](#1-monorepo-setup)
2. [Design Token System](#2-design-token-system)
3. [Universal Button Component](#3-universal-button-component)
4. [Adaptive Search Component](#4-adaptive-search-component)
5. [Domain Component Example](#5-domain-component-example)
6. [Testing Strategy](#6-testing-strategy)
7. [Publishing & Deployment](#7-publishing--deployment)

---

## 1. Monorepo Setup

### 1.1 Project Structure
```
rag-components/
├── packages/
│   ├── design-tokens/          # Shared design system
│   ├── ui-core/                # Core types and interfaces
│   ├── ui-web/                 # Web implementations
│   ├── ui-mobile/              # React Native implementations
│   ├── ui-pwa/                 # PWA-specific components
│   └── domain/                 # Business components
├── apps/
│   ├── web/                    # Next.js app (testing)
│   ├── mobile/                 # React Native app (testing)
│   └── storybook/              # Component documentation
├── pnpm-workspace.yaml
├── turbo.json
└── package.json
```

### 1.2 pnpm-workspace.yaml
```yaml
packages:
  - 'packages/*'
  - 'apps/*'
```

### 1.3 turbo.json (Build Pipeline)
```json
{
  "$schema": "https://turbo.build/schema.json",
  "pipeline": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**"]
    },
    "test": {
      "dependsOn": ["build"],
      "outputs": []
    },
    "lint": {
      "outputs": []
    },
    "dev": {
      "cache": false
    }
  }
}
```

### 1.4 Root package.json
```json
{
  "name": "rag-components",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "turbo run dev",
    "build": "turbo run build",
    "test": "turbo run test",
    "lint": "turbo run lint",
    "format": "prettier --write \"**/*.{ts,tsx,md}\""
  },
  "devDependencies": {
    "turbo": "^1.10.0",
    "prettier": "^3.0.0",
    "typescript": "^5.2.0"
  }
}
```

---

## 2. Design Token System

### 2.1 packages/design-tokens/src/colors.ts
```typescript
/**
 * Color palette for RAG Enterprise
 * All platforms use the same color values
 */

export const colors = {
  // Brand Colors
  primary: '#667eea',
  primaryDark: '#764ba2',
  primaryLight: '#8b9ef9',

  // Neutral Colors (Stone palette)
  black: '#000000',
  white: '#ffffff',
  stone950: '#0c0a09',
  stone900: '#1c1917',
  stone800: '#292524',
  stone700: '#44403c',
  stone600: '#57534e',
  stone500: '#78716c',
  stone400: '#a8a29e',
  stone300: '#d6d3d1',
  stone200: '#e7e5e4',
  stone100: '#f5f5f4',
  stone50: '#fafaf9',

  // Semantic Colors
  success: '#4ade80',
  successDark: '#22c55e',
  warning: '#fbbf24',
  warningDark: '#f59e0b',
  error: '#f87171',
  errorDark: '#ef4444',
  info: '#60a5fa',
  infoDark: '#3b82f6',

  // UI States
  focus: '#667eea',
  disabled: '#a8a29e',
  border: '#292524',
  background: '#000000',
  foreground: '#ffffff',
} as const

export type ColorKey = keyof typeof colors
```

### 2.2 packages/design-tokens/src/spacing.ts
```typescript
/**
 * Spacing scale (8px base)
 * Compatible with both web (px) and React Native (number)
 */

export const spacing = {
  0: 0,
  1: 4,    // 0.25rem
  2: 8,    // 0.5rem
  3: 12,   // 0.75rem
  4: 16,   // 1rem
  5: 20,   // 1.25rem
  6: 24,   // 1.5rem
  8: 32,   // 2rem
  10: 40,  // 2.5rem
  12: 48,  // 3rem
  16: 64,  // 4rem
  20: 80,  // 5rem
  24: 96,  // 6rem
} as const

// Aliases for common use cases
export const spacingAliases = {
  xs: spacing[1],
  sm: spacing[2],
  md: spacing[4],
  lg: spacing[6],
  xl: spacing[8],
  xxl: spacing[12],
  xxxl: spacing[16],
} as const

export type SpacingKey = keyof typeof spacing
```

### 2.3 packages/design-tokens/src/typography.ts
```typescript
/**
 * Typography scale
 */

export const typography = {
  fontFamily: {
    sans: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif',
    mono: '"SF Mono", Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
  },

  fontSize: {
    xs: 12,
    sm: 14,
    base: 16,
    lg: 18,
    xl: 20,
    '2xl': 24,
    '3xl': 30,
    '4xl': 36,
    '5xl': 48,
  },

  fontWeight: {
    normal: '400',
    medium: '500',
    semibold: '600',
    bold: '700',
    extrabold: '800',
  },

  lineHeight: {
    tight: 1.25,
    normal: 1.5,
    relaxed: 1.75,
  },

  letterSpacing: {
    tight: -0.5,
    normal: 0,
    wide: 0.5,
  },
} as const

export type FontSize = keyof typeof typography.fontSize
export type FontWeight = keyof typeof typography.fontWeight
```

### 2.4 packages/design-tokens/src/shadows.ts
```typescript
/**
 * Shadow system
 * Platform-specific implementations
 */

// Web: CSS box-shadow
export const webShadows = {
  none: 'none',
  sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
  xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
  '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
} as const

// React Native: shadowOffset + shadowRadius + elevation
export const mobileShadows = {
  none: {
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0,
    shadowRadius: 0,
    elevation: 0,
  },
  sm: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.18,
    shadowRadius: 1.0,
    elevation: 1,
  },
  md: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.23,
    shadowRadius: 2.62,
    elevation: 4,
  },
  lg: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.30,
    shadowRadius: 4.65,
    elevation: 8,
  },
  xl: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.37,
    shadowRadius: 7.49,
    elevation: 12,
  },
  '2xl': {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 12 },
    shadowOpacity: 0.58,
    shadowRadius: 16.00,
    elevation: 24,
  },
} as const

export type ShadowSize = keyof typeof webShadows
```

### 2.5 packages/design-tokens/src/index.ts
```typescript
export * from './colors'
export * from './spacing'
export * from './typography'
export * from './shadows'

// Re-export for convenience
export { colors } from './colors'
export { spacing, spacingAliases } from './spacing'
export { typography } from './typography'
export { webShadows, mobileShadows } from './shadows'
```

### 2.6 packages/design-tokens/package.json
```json
{
  "name": "@rag/design-tokens",
  "version": "1.0.0",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "scripts": {
    "build": "tsc",
    "dev": "tsc --watch"
  },
  "devDependencies": {
    "typescript": "^5.2.0"
  }
}
```

---

## 3. Universal Button Component

### 3.1 packages/ui-core/src/Button.types.ts
```typescript
import { ReactNode } from 'react'

/**
 * Universal Button Props
 * Same interface for all platforms
 */
export interface ButtonProps {
  /**
   * Button variant
   * @default 'default'
   */
  variant?: 'default' | 'destructive' | 'outline' | 'ghost' | 'link'

  /**
   * Button size
   * @default 'default'
   */
  size?: 'sm' | 'default' | 'lg' | 'icon'

  /**
   * Disable button interaction
   */
  disabled?: boolean

  /**
   * Show loading spinner
   */
  loading?: boolean

  /**
   * Button content
   */
  children: ReactNode

  /**
   * Click handler (universal: onClick on web, onPress on mobile)
   */
  onPress: () => void

  /**
   * CSS class name (web only)
   */
  className?: string

  /**
   * Test ID for E2E tests
   */
  testID?: string

  /**
   * Custom icon to show before text
   */
  icon?: ReactNode

  /**
   * Make button full width
   */
  fullWidth?: boolean
}
```

### 3.2 packages/ui-web/src/Button/Button.tsx
```typescript
import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import type { ButtonProps } from '@rag/ui-core'
import { cn } from '../utils'

/**
 * Button variants using CVA (class-variance-authority)
 */
const buttonVariants = cva(
  // Base styles
  'inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default: 'bg-stone-700 text-white hover:bg-stone-600 focus-visible:ring-stone-700',
        destructive: 'bg-red-600 text-white hover:bg-red-700 focus-visible:ring-red-600',
        outline: 'border-2 border-stone-700 bg-transparent hover:bg-stone-900 focus-visible:ring-stone-700',
        ghost: 'hover:bg-stone-900 hover:text-stone-100 focus-visible:ring-stone-700',
        link: 'text-stone-400 underline-offset-4 hover:underline hover:text-stone-300',
      },
      size: {
        sm: 'h-9 px-3 text-sm',
        default: 'h-10 px-4 text-base',
        lg: 'h-11 px-6 text-lg',
        icon: 'h-10 w-10',
      },
      fullWidth: {
        true: 'w-full',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
)

/**
 * Web Button Component
 * Uses native HTML button with Tailwind CSS
 */
export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant,
      size,
      disabled,
      loading,
      children,
      onPress,
      testID,
      icon,
      fullWidth,
      ...props
    },
    ref
  ) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, fullWidth }), className)}
        ref={ref}
        disabled={disabled || loading}
        onClick={onPress}
        data-testid={testID}
        {...props}
      >
        {loading && (
          <svg
            className="animate-spin h-4 w-4"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        )}
        {!loading && icon && icon}
        {children}
      </button>
    )
  }
)

Button.displayName = 'Button'
```

### 3.3 packages/ui-mobile/src/Button/Button.tsx
```typescript
import React from 'react'
import {
  TouchableOpacity,
  Text,
  View,
  StyleSheet,
  ActivityIndicator,
  Platform,
} from 'react-native'
import type { ButtonProps } from '@rag/ui-core'
import { colors, spacing, typography } from '@rag/design-tokens'

/**
 * React Native Button Component
 * Platform-optimized for iOS and Android
 */
export const Button: React.FC<ButtonProps> = ({
  variant = 'default',
  size = 'default',
  disabled,
  loading,
  children,
  onPress,
  testID,
  icon,
  fullWidth,
}) => {
  // Combine styles based on props
  const buttonStyle = [
    styles.base,
    styles[variant],
    styles[`size_${size}`],
    fullWidth && styles.fullWidth,
    (disabled || loading) && styles.disabled,
  ]

  const textStyle = [
    styles.text,
    styles[`text_${variant}`],
    styles[`textSize_${size}`],
  ]

  // Spinner color based on variant
  const spinnerColor = variant === 'outline' || variant === 'ghost'
    ? colors.stone100
    : colors.white

  return (
    <TouchableOpacity
      style={buttonStyle}
      onPress={onPress}
      disabled={disabled || loading}
      activeOpacity={0.7}
      testID={testID}
    >
      {loading && (
        <ActivityIndicator
          size="small"
          color={spinnerColor}
          style={styles.loader}
        />
      )}
      {!loading && icon && <View style={styles.icon}>{icon}</View>}
      <Text style={textStyle}>{children}</Text>
    </TouchableOpacity>
  )
}

const styles = StyleSheet.create({
  base: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 12,
    gap: spacing[2],
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
      },
      android: {
        elevation: 2,
      },
    }),
  },

  // Variants
  default: {
    backgroundColor: colors.stone700,
  },
  destructive: {
    backgroundColor: colors.error,
  },
  outline: {
    backgroundColor: 'transparent',
    borderWidth: 2,
    borderColor: colors.stone700,
  },
  ghost: {
    backgroundColor: 'transparent',
  },
  link: {
    backgroundColor: 'transparent',
  },

  // Sizes
  size_sm: {
    height: 36,
    paddingHorizontal: spacing[3],
  },
  size_default: {
    height: 44, // iOS minimum touch target
    paddingHorizontal: spacing[4],
  },
  size_lg: {
    height: 52,
    paddingHorizontal: spacing[6],
  },
  size_icon: {
    height: 44,
    width: 44,
    paddingHorizontal: 0,
  },

  fullWidth: {
    width: '100%',
  },

  disabled: {
    opacity: 0.5,
  },

  // Text styles
  text: {
    fontFamily: typography.fontFamily.sans,
    fontWeight: typography.fontWeight.semibold,
  },
  text_default: {
    color: colors.white,
  },
  text_destructive: {
    color: colors.white,
  },
  text_outline: {
    color: colors.stone700,
  },
  text_ghost: {
    color: colors.stone100,
  },
  text_link: {
    color: colors.stone400,
    textDecorationLine: 'underline',
  },

  textSize_sm: {
    fontSize: typography.fontSize.sm,
  },
  textSize_default: {
    fontSize: typography.fontSize.base,
  },
  textSize_lg: {
    fontSize: typography.fontSize.lg,
  },
  textSize_icon: {
    fontSize: 0, // Hide text in icon-only mode
  },

  loader: {
    marginRight: spacing[1],
  },
  icon: {
    marginRight: spacing[1],
  },
})
```

### 3.4 Usage Example
```typescript
// Web (Next.js)
import { Button } from '@rag/ui-web'

function LoginPage() {
  return (
    <Button onPress={() => console.log('Login')}>
      Login
    </Button>
  )
}

// React Native
import { Button } from '@rag/ui-mobile'

function LoginScreen() {
  return (
    <Button onPress={() => console.log('Login')}>
      Login
    </Button>
  )
}

// Both platforms use the same props interface!
```

---

## 4. Adaptive Search Component

### 4.1 packages/ui-core/src/SearchBar.types.ts
```typescript
import { ReactNode } from 'react'

export interface SearchSuggestion {
  id: string
  label: string
  value: string
  icon?: ReactNode
}

export interface SearchBarProps {
  /**
   * Placeholder text
   */
  placeholder?: string

  /**
   * Current search value
   */
  value: string

  /**
   * Change handler
   */
  onChange: (value: string) => void

  /**
   * Submit handler (Enter key or search button)
   */
  onSubmit?: (value: string) => void

  /**
   * Focus handler
   */
  onFocus?: () => void

  /**
   * Blur handler
   */
  onBlur?: () => void

  /**
   * Auto-focus on mount
   */
  autoFocus?: boolean

  /**
   * Show cancel button (mobile)
   */
  showCancel?: boolean

  /**
   * Search suggestions
   */
  suggestions?: SearchSuggestion[]

  /**
   * Loading state
   */
  loading?: boolean

  /**
   * Test ID
   */
  testID?: string
}
```

### 4.2 packages/ui-web/src/SearchBar/SearchBar.tsx
```typescript
import React, { useState, useRef, useEffect } from 'react'
import { Search, X, Loader2 } from 'lucide-react'
import type { SearchBarProps } from '@rag/ui-core'
import { Input } from '../Input'
import { cn } from '../utils'

/**
 * Web Search Bar with Dropdown Suggestions
 */
export const SearchBar: React.FC<SearchBarProps> = ({
  placeholder = 'Search...',
  value,
  onChange,
  onSubmit,
  onFocus,
  onBlur,
  autoFocus,
  suggestions = [],
  loading,
  testID,
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const wrapperRef = useRef<HTMLDivElement>(null)

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      if (selectedIndex >= 0 && suggestions[selectedIndex]) {
        onChange(suggestions[selectedIndex].value)
        onSubmit?.(suggestions[selectedIndex].value)
      } else {
        onSubmit?.(value)
      }
      setIsOpen(false)
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      setSelectedIndex((prev) => Math.min(prev + 1, suggestions.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setSelectedIndex((prev) => Math.max(prev - 1, -1))
    } else if (e.key === 'Escape') {
      setIsOpen(false)
    }
  }

  const handleFocus = () => {
    setIsOpen(suggestions.length > 0)
    onFocus?.()
  }

  const handleBlur = () => {
    // Delay to allow suggestion click
    setTimeout(() => {
      setIsOpen(false)
      onBlur?.()
    }, 200)
  }

  const handleClear = () => {
    onChange('')
    setIsOpen(false)
  }

  return (
    <div ref={wrapperRef} className="relative w-full" data-testid={testID}>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-stone-500" />
        <Input
          placeholder={placeholder}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={handleFocus}
          onBlur={handleBlur}
          autoFocus={autoFocus}
          className="pl-10 pr-20"
        />
        <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2">
          {loading && <Loader2 className="h-4 w-4 animate-spin text-stone-500" />}
          {value && !loading && (
            <button
              onClick={handleClear}
              className="text-stone-500 hover:text-stone-300"
              type="button"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      {/* Suggestions Dropdown */}
      {isOpen && suggestions.length > 0 && (
        <div className="absolute z-50 mt-2 w-full rounded-lg border-2 border-stone-800 bg-stone-950 shadow-lg">
          {suggestions.map((suggestion, index) => (
            <button
              key={suggestion.id}
              onClick={() => {
                onChange(suggestion.value)
                onSubmit?.(suggestion.value)
                setIsOpen(false)
              }}
              className={cn(
                'flex w-full items-center gap-3 px-4 py-3 text-left transition-colors',
                'hover:bg-stone-900',
                index === selectedIndex && 'bg-stone-900',
                index === 0 && 'rounded-t-lg',
                index === suggestions.length - 1 && 'rounded-b-lg'
              )}
            >
              {suggestion.icon && <span className="text-stone-400">{suggestion.icon}</span>}
              <span className="text-stone-100">{suggestion.label}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
```

### 4.3 packages/ui-mobile/src/SearchBar/SearchBar.tsx
```typescript
import React, { useRef, useState } from 'react'
import {
  View,
  TextInput,
  TouchableOpacity,
  Text,
  StyleSheet,
  Animated,
  ActivityIndicator,
} from 'react-native'
import type { SearchBarProps } from '@rag/ui-core'
import { colors, spacing, typography } from '@rag/design-tokens'

/**
 * React Native Search Bar
 * Mobile-optimized with cancel button animation
 */
export const SearchBar: React.FC<SearchBarProps> = ({
  placeholder = 'Search...',
  value,
  onChange,
  onSubmit,
  onFocus,
  onBlur,
  autoFocus,
  showCancel = false,
  loading,
  testID,
}) => {
  const [isFocused, setIsFocused] = useState(false)
  const cancelWidth = useRef(new Animated.Value(0)).current
  const inputRef = useRef<TextInput>(null)

  const handleFocus = () => {
    setIsFocused(true)
    onFocus?.()

    // Animate cancel button in
    Animated.spring(cancelWidth, {
      toValue: 80,
      useNativeDriver: false,
      friction: 8,
    }).start()
  }

  const handleBlur = () => {
    setIsFocused(false)
    onBlur?.()

    // Animate cancel button out if no value
    if (!value && !showCancel) {
      Animated.spring(cancelWidth, {
        toValue: 0,
        useNativeDriver: false,
        friction: 8,
      }).start()
    }
  }

  const handleCancel = () => {
    onChange('')
    inputRef.current?.blur()

    Animated.spring(cancelWidth, {
      toValue: 0,
      useNativeDriver: false,
      friction: 8,
    }).start()
  }

  const handleClear = () => {
    onChange('')
    inputRef.current?.focus()
  }

  return (
    <View style={styles.container} testID={testID}>
      <View style={[styles.inputContainer, isFocused && styles.inputContainerFocused]}>
        {/* Search Icon */}
        <Text style={styles.searchIcon}>🔍</Text>

        {/* Text Input */}
        <TextInput
          ref={inputRef}
          style={styles.input}
          placeholder={placeholder}
          placeholderTextColor={colors.stone500}
          value={value}
          onChangeText={onChange}
          onSubmitEditing={() => onSubmit?.(value)}
          onFocus={handleFocus}
          onBlur={handleBlur}
          autoFocus={autoFocus}
          returnKeyType="search"
          autoCapitalize="none"
          autoCorrect={false}
        />

        {/* Loading or Clear Button */}
        {loading ? (
          <ActivityIndicator size="small" color={colors.stone500} />
        ) : value ? (
          <TouchableOpacity onPress={handleClear} style={styles.clearButton}>
            <Text style={styles.clearIcon}>✕</Text>
          </TouchableOpacity>
        ) : null}
      </View>

      {/* Cancel Button (iOS style) */}
      <Animated.View style={[styles.cancelContainer, { width: cancelWidth }]}>
        <TouchableOpacity onPress={handleCancel} style={styles.cancelButton}>
          <Text style={styles.cancelText}>Cancel</Text>
        </TouchableOpacity>
      </Animated.View>
    </View>
  )
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  inputContainer: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    height: 44,
    backgroundColor: colors.stone900,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: 'transparent',
    paddingHorizontal: spacing[3],
    gap: spacing[2],
  },
  inputContainerFocused: {
    borderColor: colors.primary,
    backgroundColor: colors.stone950,
  },
  searchIcon: {
    fontSize: 18,
    color: colors.stone500,
  },
  input: {
    flex: 1,
    fontSize: typography.fontSize.base,
    color: colors.white,
    fontFamily: typography.fontFamily.sans,
    padding: 0,
  },
  clearButton: {
    padding: spacing[1],
  },
  clearIcon: {
    fontSize: 16,
    color: colors.stone500,
  },
  cancelContainer: {
    overflow: 'hidden',
  },
  cancelButton: {
    paddingHorizontal: spacing[3],
    justifyContent: 'center',
    alignItems: 'center',
    height: 44,
  },
  cancelText: {
    fontSize: typography.fontSize.base,
    color: colors.primary,
    fontWeight: typography.fontWeight.medium,
  },
})
```

---

## 5. Domain Component Example

### 5.1 packages/domain/src/ProductCard/ProductCard.types.ts
```typescript
export interface Product {
  id: string
  name: string
  description: string
  imageUrl: string
  price: number
  currency: string
  stock: number
  category: string
  rating?: number
  reviewCount?: number
}

export interface ProductCardProps {
  product: Product
  onPress: (productId: string) => void
  onAddToCart?: (productId: string) => void
  variant?: 'grid' | 'list'
  showAddToCart?: boolean
}
```

### 5.2 packages/domain/src/ProductCard/ProductCard.tsx
```typescript
import React from 'react'
import { Platform, View, Text, Image, StyleSheet } from 'react-native'
import type { ProductCardProps } from './ProductCard.types'
import { Button, Card, Badge } from '@rag/ui-mobile'
import { colors, spacing, typography } from '@rag/design-tokens'

/**
 * Universal Product Card
 * Works on both web and mobile
 */
export const ProductCard: React.FC<ProductCardProps> = ({
  product,
  onPress,
  onAddToCart,
  variant = 'grid',
  showAddToCart = true,
}) => {
  const isWeb = Platform.OS === 'web'
  const isGrid = variant === 'grid'

  return (
    <Card
      onPress={() => onPress(product.id)}
      style={isGrid ? styles.cardGrid : styles.cardList}
      testID={`product-card-${product.id}`}
    >
      {/* Product Image */}
      <Image
        source={{ uri: product.imageUrl }}
        style={isGrid ? styles.imageGrid : styles.imageList}
        resizeMode="cover"
      />

      {/* Content */}
      <View style={styles.content}>
        {/* Category Badge */}
        <Badge variant="secondary" size="sm">
          {product.category}
        </Badge>

        {/* Product Name */}
        <Text style={styles.name} numberOfLines={2}>
          {product.name}
        </Text>

        {/* Description */}
        <Text style={styles.description} numberOfLines={isGrid ? 2 : 3}>
          {product.description}
        </Text>

        {/* Rating (if available) */}
        {product.rating && (
          <View style={styles.rating}>
            <Text style={styles.ratingStars}>
              {'⭐'.repeat(Math.round(product.rating))}
            </Text>
            <Text style={styles.ratingText}>
              {product.rating.toFixed(1)} ({product.reviewCount || 0})
            </Text>
          </View>
        )}

        {/* Footer: Price + Stock */}
        <View style={styles.footer}>
          <View style={styles.priceContainer}>
            <Text style={styles.price}>
              {product.currency}{product.price.toFixed(2)}
            </Text>
            <Badge
              variant={product.stock > 0 ? 'success' : 'destructive'}
              size="sm"
            >
              {product.stock > 0 ? `${product.stock} in stock` : 'Out of stock'}
            </Badge>
          </View>
        </View>

        {/* Add to Cart Button */}
        {showAddToCart && (
          <Button
            onPress={() => onAddToCart?.(product.id)}
            disabled={product.stock === 0}
            fullWidth
            size="sm"
          >
            {product.stock > 0 ? 'Add to Cart' : 'Sold Out'}
          </Button>
        )}
      </View>
    </Card>
  )
}

const styles = StyleSheet.create({
  cardGrid: {
    width: '100%',
    maxWidth: 320,
  },
  cardList: {
    flexDirection: 'row',
    width: '100%',
  },
  imageGrid: {
    width: '100%',
    height: 200,
    borderTopLeftRadius: 12,
    borderTopRightRadius: 12,
  },
  imageList: {
    width: 120,
    height: 120,
    borderTopLeftRadius: 12,
    borderBottomLeftRadius: 12,
  },
  content: {
    padding: spacing[4],
    gap: spacing[2],
    flex: 1,
  },
  name: {
    fontSize: typography.fontSize.lg,
    fontWeight: typography.fontWeight.semibold,
    color: colors.stone100,
    lineHeight: typography.lineHeight.tight,
  },
  description: {
    fontSize: typography.fontSize.sm,
    color: colors.stone400,
    lineHeight: typography.lineHeight.normal,
  },
  rating: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing[1],
  },
  ratingStars: {
    fontSize: typography.fontSize.sm,
  },
  ratingText: {
    fontSize: typography.fontSize.xs,
    color: colors.stone400,
  },
  footer: {
    marginTop: spacing[2],
  },
  priceContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  price: {
    fontSize: typography.fontSize.xl,
    fontWeight: typography.fontWeight.bold,
    color: colors.primary,
  },
})
```

---

## 6. Testing Strategy

### 6.1 Unit Test Example (Jest + React Testing Library)
```typescript
// packages/ui-mobile/src/Button/__tests__/Button.test.tsx
import React from 'react'
import { render, fireEvent } from '@testing-library/react-native'
import { Button } from '../Button'

describe('Button', () => {
  it('renders correctly with text', () => {
    const { getByText } = render(<Button onPress={() => {}}>Click me</Button>)
    expect(getByText('Click me')).toBeTruthy()
  })

  it('calls onPress when pressed', () => {
    const onPress = jest.fn()
    const { getByText } = render(<Button onPress={onPress}>Click me</Button>)

    fireEvent.press(getByText('Click me'))
    expect(onPress).toHaveBeenCalledTimes(1)
  })

  it('disables interaction when disabled', () => {
    const onPress = jest.fn()
    const { getByText } = render(
      <Button disabled onPress={onPress}>
        Click me
      </Button>
    )

    fireEvent.press(getByText('Click me'))
    expect(onPress).not.toHaveBeenCalled()
  })

  it('disables interaction when loading', () => {
    const onPress = jest.fn()
    const { getByText } = render(
      <Button loading onPress={onPress}>
        Click me
      </Button>
    )

    fireEvent.press(getByText('Click me'))
    expect(onPress).not.toHaveBeenCalled()
  })

  it('shows loading spinner when loading', () => {
    const { getByTestId } = render(
      <Button loading onPress={() => {}} testID="button">
        Click me
      </Button>
    )

    // ActivityIndicator is rendered
    expect(getByTestId('button')).toBeTruthy()
  })

  it('applies correct styles for variant', () => {
    const { getByTestId } = render(
      <Button variant="destructive" onPress={() => {}} testID="button">
        Delete
      </Button>
    )

    const button = getByTestId('button')
    // Check if destructive styles are applied
    expect(button).toHaveStyle({ backgroundColor: '#f87171' })
  })
})
```

### 6.2 Storybook Example
```typescript
// packages/ui-mobile/src/Button/Button.stories.tsx
import type { Meta, StoryObj } from '@storybook/react-native'
import { Button } from './Button'

const meta: Meta<typeof Button> = {
  title: 'Core/Button',
  component: Button,
  argTypes: {
    variant: {
      options: ['default', 'destructive', 'outline', 'ghost', 'link'],
      control: { type: 'select' },
    },
    size: {
      options: ['sm', 'default', 'lg', 'icon'],
      control: { type: 'select' },
    },
    disabled: {
      control: { type: 'boolean' },
    },
    loading: {
      control: { type: 'boolean' },
    },
    fullWidth: {
      control: { type: 'boolean' },
    },
  },
  args: {
    children: 'Button',
    onPress: () => console.log('Button pressed'),
  },
}

export default meta
type Story = StoryObj<typeof Button>

export const Default: Story = {}

export const Destructive: Story = {
  args: {
    variant: 'destructive',
    children: 'Delete',
  },
}

export const Outline: Story = {
  args: {
    variant: 'outline',
  },
}

export const Loading: Story = {
  args: {
    loading: true,
  },
}

export const Disabled: Story = {
  args: {
    disabled: true,
  },
}

export const WithIcon: Story = {
  args: {
    icon: '🚀',
    children: 'Launch',
  },
}

export const FullWidth: Story = {
  args: {
    fullWidth: true,
  },
}

export const Sizes: Story = {
  render: () => (
    <>
      <Button size="sm" onPress={() => {}}>
        Small
      </Button>
      <Button size="default" onPress={() => {}}>
        Default
      </Button>
      <Button size="lg" onPress={() => {}}>
        Large
      </Button>
    </>
  ),
}
```

---

## 7. Publishing & Deployment

### 7.1 Package Publishing
```json
// packages/ui-mobile/package.json
{
  "name": "@rag/ui-mobile",
  "version": "1.0.0",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "files": ["dist"],
  "scripts": {
    "build": "tsc",
    "test": "jest",
    "lint": "eslint src --ext .ts,.tsx"
  },
  "peerDependencies": {
    "react": "^18.0.0",
    "react-native": "^0.72.0"
  },
  "dependencies": {
    "@rag/design-tokens": "workspace:*",
    "@rag/ui-core": "workspace:*"
  }
}
```

### 7.2 CI/CD Workflow (GitHub Actions)
```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: pnpm/action-setup@v2
        with:
          version: 8
      - uses: actions/setup-node@v3
        with:
          node-version: 18
          cache: 'pnpm'

      - run: pnpm install
      - run: pnpm run build
      - run: pnpm run test
      - run: pnpm run lint

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/lcov.info
```

---

**Last Updated**: 2025-11-12
**Author**: Frontend Team
**Status**: Implementation Ready
