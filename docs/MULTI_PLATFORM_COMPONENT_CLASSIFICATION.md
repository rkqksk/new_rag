# Multi-Platform Component Classification

**Version**: 1.0.0
**Date**: 2025-11-12
**Status**: Comprehensive Analysis

## Executive Summary

Analysis of RAG Enterprise frontend architecture across 4 platforms:
- **frontend/** - Legacy HTML/JS (v1.0)
- **frontend-v2/** - Next.js 14 with shadcn/ui (v2.0)
- **mobile/pwa/** - Progressive Web App
- **mobile/react-native/** - React Native mobile app

**Goal**: Create unified component library maximizing code reuse while respecting platform constraints.

---

## 1. Platform Overview

### 1.1 Frontend (Legacy) - HTML/JS
**Tech Stack**: Vanilla HTML5, CSS3, JavaScript ES6+
**Features**:
- Login/Register forms
- Analytics dashboard
- Dark mode support
- i18n (internationalization)
- Offline storage
- Notifications

**Strengths**:
- Zero dependencies
- Fast load time
- Easy deployment

**Weaknesses**:
- No component reuse
- Manual DOM manipulation
- Limited type safety

### 1.2 Frontend-v2 - Next.js 14
**Tech Stack**: Next.js 14 App Router, TypeScript, Tailwind CSS, shadcn/ui
**Components**: 24 components (9 dashboard + 15 UI primitives)
**Features**:
- Role-based routing (super-admin, admin, staff, customer)
- Advanced search with filters
- Notification center
- Real-time updates
- SaaS multi-tenancy

**Strengths**:
- Type-safe components
- Server-side rendering
- Excellent DX (Developer Experience)
- Reusable UI primitives

**Weaknesses**:
- Heavy bundle size
- Desktop-first design
- Limited mobile optimization

### 1.3 Mobile PWA
**Tech Stack**: HTML5, CSS3, JavaScript, Service Workers
**Features**:
- Mobile-optimized login
- Touch-friendly UI
- Offline support
- Add to home screen
- Safe area insets (notch support)

**Strengths**:
- Works on any device
- No app store required
- Instant updates

**Weaknesses**:
- Limited native features
- Performance constraints
- Browser compatibility issues

### 1.4 React Native
**Tech Stack**: React Native, TypeScript, AsyncStorage
**Components**: 2 screens (Login, Register)
**Features**:
- Native mobile experience
- Platform-specific styling
- Touch gestures
- Native navigation

**Strengths**:
- True native performance
- Access to device APIs
- Platform-specific UX

**Weaknesses**:
- Platform-specific code
- Build complexity
- App store distribution

---

## 2. Component Classification

### 2.1 Core Components (Used Everywhere)

These components are essential across all platforms with minimal variation.

#### 2.1.1 Button
**Platforms**: Web, PWA, Mobile
**Variants**: default, destructive, outline, ghost, link
**Sizes**: sm, default, lg, icon
**Props**:
```typescript
interface ButtonProps {
  variant?: 'default' | 'destructive' | 'outline' | 'ghost' | 'link'
  size?: 'sm' | 'default' | 'lg' | 'icon'
  disabled?: boolean
  loading?: boolean
  children: ReactNode
  onClick?: () => void
}
```

**Implementation Strategy**:
- **Web**: shadcn/ui Button (Radix UI + CVA)
- **PWA**: Styled HTML button with touch optimization
- **React Native**: TouchableOpacity with platform styles

#### 2.1.2 Input
**Platforms**: Web, PWA, Mobile
**Types**: text, email, password, number, search
**Props**:
```typescript
interface InputProps {
  type?: 'text' | 'email' | 'password' | 'number' | 'search'
  placeholder?: string
  value: string
  onChange: (value: string) => void
  error?: string
  disabled?: boolean
  autoFocus?: boolean
  icon?: ReactNode
}
```

**Implementation Strategy**:
- **Web**: shadcn/ui Input with label
- **PWA**: HTML input with touch-friendly sizing (min 44px)
- **React Native**: TextInput with platform keyboard types

#### 2.1.3 Card
**Platforms**: Web, PWA, Mobile
**Sections**: Header, Content, Footer
**Props**:
```typescript
interface CardProps {
  title?: string
  description?: string
  children: ReactNode
  footer?: ReactNode
  variant?: 'default' | 'outlined' | 'elevated'
  className?: string
}
```

**Implementation Strategy**:
- **Web**: shadcn/ui Card (CardHeader, CardContent)
- **PWA**: Div with border-radius and shadow
- **React Native**: View with shadowOffset/elevation

#### 2.1.4 Alert/Toast
**Platforms**: Web, PWA, Mobile
**Types**: success, error, warning, info
**Props**:
```typescript
interface AlertProps {
  type: 'success' | 'error' | 'warning' | 'info'
  message: string
  duration?: number
  dismissible?: boolean
  onDismiss?: () => void
}
```

**Implementation Strategy**:
- **Web**: Sonner toast library
- **PWA**: CSS animations with auto-dismiss
- **React Native**: Alert.alert() for critical, custom Toast for non-blocking

#### 2.1.5 Badge
**Platforms**: Web, PWA, Mobile
**Variants**: default, secondary, destructive, success
**Props**:
```typescript
interface BadgeProps {
  variant?: 'default' | 'secondary' | 'destructive' | 'success'
  children: ReactNode
  size?: 'sm' | 'default'
}
```

#### 2.1.6 Loading Spinner
**Platforms**: Web, PWA, Mobile
**Sizes**: sm, default, lg
**Props**:
```typescript
interface SpinnerProps {
  size?: 'sm' | 'default' | 'lg'
  color?: string
  fullScreen?: boolean
}
```

---

### 2.2 Web-Only Components (Desktop Specific)

#### 2.2.1 Sidebar Navigation
**Platform**: Web only
**Reason**: Desktop has horizontal space for persistent navigation
**Features**:
- Fixed left column (256px)
- Collapsible sections
- Role-based menu items
- User profile section

**Props**:
```typescript
interface SidebarProps {
  userRole: string
  userName?: string
  userEmail?: string
  collapsed?: boolean
  onToggle?: () => void
}
```

**Mobile Alternative**: Bottom tab navigation or hamburger menu

#### 2.2.2 Navbar (Top Bar)
**Platform**: Web only
**Reason**: Desktop header pattern with global search
**Features**:
- Page title and breadcrumb
- Global search bar
- Notification bell
- User menu dropdown

**Props**:
```typescript
interface NavbarProps {
  title: string
  subtitle?: string
  showSearch?: boolean
  onSearchChange?: (query: string) => void
}
```

**Mobile Alternative**: Fixed top bar with hamburger + back button

#### 2.2.3 Advanced Search Panel
**Platform**: Web only
**Reason**: Complex multi-filter UI requires desktop space
**Features**:
- Expandable filter panel
- Category/status dropdowns
- Date range picker
- Sort controls
- Export buttons (CSV/JSON)

**Props**: See AdvancedSearch component (367 lines)

**Mobile Alternative**: Bottom sheet with simplified filters

#### 2.2.4 Data Table
**Platform**: Web primarily
**Reason**: Horizontal scrolling on mobile is poor UX
**Features**:
- Sortable columns
- Row selection
- Pagination
- Expandable rows
- Bulk actions

**Mobile Alternative**: Card-based list view

#### 2.2.5 Multi-Column Layout
**Platform**: Web only
**Reason**: Mobile uses single-column stack
**Examples**:
- Dashboard with 3-4 stat cards per row
- Settings with sidebar + content
- Analytics with charts + summary

**Mobile Alternative**: Vertical stack with swipeable sections

---

### 2.3 Mobile-Only Components (Touch/Native Specific)

#### 2.3.1 Pull-to-Refresh
**Platform**: PWA, React Native
**Reason**: Mobile-first gesture interaction
**Props**:
```typescript
interface PullToRefreshProps {
  onRefresh: () => Promise<void>
  children: ReactNode
  threshold?: number
}
```

**Implementation**:
- **PWA**: Touch event listeners + CSS transforms
- **React Native**: RefreshControl component

#### 2.3.2 Bottom Sheet
**Platform**: PWA, React Native
**Reason**: Mobile modal pattern for actions/filters
**Props**:
```typescript
interface BottomSheetProps {
  isOpen: boolean
  onClose: () => void
  snapPoints?: number[]
  children: ReactNode
}
```

**Implementation**:
- **PWA**: Fixed position div with slide-up animation
- **React Native**: react-native-bottom-sheet or Modal

#### 2.3.3 Swipeable List Item
**Platform**: PWA, React Native
**Reason**: Touch gesture for quick actions (delete, archive)
**Props**:
```typescript
interface SwipeableItemProps {
  children: ReactNode
  leftActions?: Action[]
  rightActions?: Action[]
  onSwipe?: (direction: 'left' | 'right') => void
}

interface Action {
  label: string
  icon: ReactNode
  color: string
  onPress: () => void
}
```

#### 2.3.4 Bottom Tab Navigation
**Platform**: React Native
**Reason**: Native mobile navigation pattern
**Props**:
```typescript
interface BottomTabsProps {
  tabs: TabItem[]
  activeTab: string
  onTabChange: (tabId: string) => void
}

interface TabItem {
  id: string
  label: string
  icon: ReactNode
  badge?: number
}
```

**Alternative**: PWA uses fixed bottom nav bar

#### 2.3.5 Native Header
**Platform**: React Native
**Reason**: Platform-specific navigation bar
**Features**:
- iOS: Large title, translucent background
- Android: Material Design app bar
- Back button with gesture
- Action buttons (share, more)

**Props**:
```typescript
interface NativeHeaderProps {
  title: string
  leftButton?: HeaderButton
  rightButtons?: HeaderButton[]
  largeTitle?: boolean // iOS only
}
```

#### 2.3.6 Floating Action Button (FAB)
**Platform**: PWA, React Native
**Reason**: Mobile quick action pattern
**Props**:
```typescript
interface FABProps {
  icon: ReactNode
  onPress: () => void
  position?: 'bottom-right' | 'bottom-center' | 'bottom-left'
  size?: 'sm' | 'default' | 'lg'
  extended?: boolean
  label?: string
}
```

#### 2.3.7 Haptic Feedback Wrapper
**Platform**: React Native only
**Reason**: Native tactile feedback
**Props**:
```typescript
interface HapticButtonProps extends ButtonProps {
  hapticStyle?: 'light' | 'medium' | 'heavy' | 'success' | 'warning' | 'error'
}
```

---

### 2.4 Platform Adaptive Components

These components have different implementations per platform but same interface.

#### 2.4.1 Auth Form (Login/Register)
**All Platforms**: Web, PWA, React Native

**Variations**:
- **Web**: Card-based form with decorative background
- **PWA**: Full-screen mobile-optimized form
- **React Native**: KeyboardAvoidingView with ScrollView

**Common Props**:
```typescript
interface AuthFormProps {
  type: 'login' | 'register'
  onSubmit: (credentials: Credentials) => Promise<void>
  onSocialAuth?: (provider: string) => Promise<void>
  loading?: boolean
  error?: string
}
```

**Implementation Differences**:
- **Web**: 400px max-width card, hover effects
- **PWA**: Full viewport with safe-area-inset
- **React Native**: Platform-specific keyboard handling

#### 2.4.2 Search Bar
**All Platforms**: Web, PWA, React Native

**Variations**:
- **Web**: Inline input with dropdown suggestions
- **PWA**: Full-width bar with cancel button
- **React Native**: Native SearchBar component

**Common Props**:
```typescript
interface SearchBarProps {
  placeholder?: string
  value: string
  onChange: (value: string) => void
  onSubmit?: (value: string) => void
  suggestions?: SearchSuggestion[]
  autoFocus?: boolean
}
```

#### 2.4.3 Dropdown/Select
**All Platforms**: Web, PWA, React Native

**Variations**:
- **Web**: Radix UI Popover with keyboard navigation
- **PWA**: Native select or custom bottom sheet
- **React Native**: Picker component (iOS wheel, Android dropdown)

**Common Props**:
```typescript
interface SelectProps {
  options: SelectOption[]
  value: string | string[]
  onChange: (value: string | string[]) => void
  placeholder?: string
  multiple?: boolean
  searchable?: boolean
}
```

#### 2.4.4 Date Picker
**All Platforms**: Web, PWA, React Native

**Variations**:
- **Web**: Custom calendar popover
- **PWA**: Native input[type="date"] or custom
- **React Native**: DateTimePicker (native modals)

**Common Props**:
```typescript
interface DatePickerProps {
  value: Date | null
  onChange: (date: Date) => void
  mode?: 'date' | 'time' | 'datetime'
  minDate?: Date
  maxDate?: Date
}
```

#### 2.4.5 Image Viewer
**All Platforms**: Web, PWA, React Native

**Variations**:
- **Web**: Lightbox with zoom controls
- **PWA**: Touch gestures for pinch-zoom
- **React Native**: Image.getSize + pan responder

**Common Props**:
```typescript
interface ImageViewerProps {
  images: ImageSource[]
  initialIndex?: number
  onClose: () => void
  enableZoom?: boolean
  enableSwipe?: boolean
}
```

#### 2.4.6 File Upload
**All Platforms**: Web, PWA, React Native

**Variations**:
- **Web**: Drag-and-drop zone + file input
- **PWA**: File input with camera option
- **React Native**: DocumentPicker + ImagePicker

**Common Props**:
```typescript
interface FileUploadProps {
  accept?: string[]
  multiple?: boolean
  maxSize?: number
  onUpload: (files: File[]) => Promise<void>
  onProgress?: (progress: number) => void
}
```

---

## 3. Component Hierarchy

```
RAG Components Library
│
├── Core (Universal)
│   ├── Button
│   ├── Input
│   ├── Card
│   ├── Badge
│   ├── Alert/Toast
│   ├── Spinner
│   ├── Avatar
│   ├── Checkbox
│   ├── Radio
│   ├── Switch
│   ├── Label
│   ├── Separator
│   └── Skeleton
│
├── Web Only
│   ├── Sidebar
│   ├── Navbar
│   ├── AdvancedSearch
│   ├── DataTable
│   ├── MultiColumn
│   └── DropdownMenu
│
├── Mobile Only
│   ├── PullToRefresh
│   ├── BottomSheet
│   ├── SwipeableItem
│   ├── BottomTabNav
│   ├── NativeHeader
│   ├── FAB
│   └── HapticFeedback
│
├── Adaptive (Platform-Specific Implementation)
│   ├── AuthForm (Login/Register)
│   ├── SearchBar
│   ├── Select/Dropdown
│   ├── DatePicker
│   ├── ImageViewer
│   └── FileUpload
│
├── Domain Components (Shared Logic)
│   ├── ProductCard
│   ├── OrderItem
│   ├── UserProfile
│   ├── NotificationItem
│   ├── StatCard
│   └── ChartWrapper
│
└── Layout Components
    ├── Container
    ├── Grid
    ├── Stack (Vertical/Horizontal)
    ├── Center
    └── SafeAreaView
```

---

## 4. Unified Component Interface Strategy

### 4.1 Core Principles

1. **Same Props API**: All platforms expose identical props interface
2. **Platform Detection**: Auto-detect platform and render appropriate component
3. **Style System**: Unified token system (colors, spacing, typography)
4. **Type Safety**: Full TypeScript support across all platforms
5. **Accessibility**: WCAG 2.1 AA compliance on all platforms

### 4.2 Implementation Architecture

```typescript
// packages/ui-core/Button.ts
export interface ButtonProps {
  variant?: 'default' | 'destructive' | 'outline' | 'ghost'
  size?: 'sm' | 'default' | 'lg'
  disabled?: boolean
  loading?: boolean
  children: ReactNode
  onPress: () => void // Universal: onClick on web, onPress on mobile
}

// packages/ui-web/Button.tsx
export const Button: React.FC<ButtonProps> = (props) => {
  return <RadixButton {...mapPropsToWeb(props)} />
}

// packages/ui-mobile/Button.tsx
export const Button: React.FC<ButtonProps> = (props) => {
  return <TouchableOpacity {...mapPropsToMobile(props)} />
}

// packages/ui/index.ts
export { Button } from Platform.OS === 'web'
  ? './ui-web/Button'
  : './ui-mobile/Button'
```

### 4.3 Monorepo Structure

```
packages/
├── ui-core/           # Core types and interfaces
│   ├── types/
│   ├── hooks/
│   └── utils/
│
├── ui-web/            # Web implementations (Next.js)
│   ├── Button/
│   ├── Input/
│   └── index.ts
│
├── ui-mobile/         # React Native implementations
│   ├── Button/
│   ├── Input/
│   └── index.ts
│
├── ui-pwa/            # PWA-specific components
│   ├── PullToRefresh/
│   ├── BottomSheet/
│   └── index.ts
│
├── design-tokens/     # Unified style system
│   ├── colors.ts
│   ├── spacing.ts
│   ├── typography.ts
│   └── shadows.ts
│
└── domain/            # Business components
    ├── ProductCard/
    ├── OrderItem/
    └── index.ts
```

---

## 5. Design Token System

### 5.1 Colors
```typescript
export const colors = {
  // Brand
  primary: '#667eea',
  primaryDark: '#764ba2',

  // Neutrals
  black: '#000000',
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
  white: '#ffffff',

  // Semantic
  success: '#4ade80',
  warning: '#fbbf24',
  error: '#f87171',
  info: '#60a5fa',
}
```

### 5.2 Spacing
```typescript
export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
  xxxl: 64,
}
```

### 5.3 Typography
```typescript
export const typography = {
  fontFamily: {
    sans: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    mono: '"SF Mono", Monaco, Consolas, monospace',
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
  },
  fontWeight: {
    normal: '400',
    medium: '500',
    semibold: '600',
    bold: '700',
  },
}
```

### 5.4 Shadows (Platform Adaptive)
```typescript
// Web (box-shadow)
export const webShadows = {
  sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
  xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
}

// React Native (shadowOffset + elevation)
export const mobileShadows = {
  sm: { shadowOffset: { width: 0, height: 1 }, shadowRadius: 2, elevation: 2 },
  md: { shadowOffset: { width: 0, height: 4 }, shadowRadius: 6, elevation: 4 },
  lg: { shadowOffset: { width: 0, height: 10 }, shadowRadius: 15, elevation: 8 },
  xl: { shadowOffset: { width: 0, height: 20 }, shadowRadius: 25, elevation: 12 },
}
```

---

## 6. Optimization Strategies

### 6.1 Web Optimization

**Code Splitting**:
```typescript
// Load heavy components only when needed
const AdvancedSearch = lazy(() => import('./AdvancedSearch'))
const DataTable = lazy(() => import('./DataTable'))
```

**Tree Shaking**:
```typescript
// Import only needed components
import { Button, Input } from '@rag/ui-web'
// NOT: import * from '@rag/ui-web'
```

**Image Optimization**:
- Next.js Image component with automatic WebP conversion
- Lazy loading with intersection observer
- Responsive srcset for different screen sizes

**Bundle Size**:
- Target: < 150KB initial bundle (gzipped)
- shadcn/ui components are tree-shakeable
- Avoid large libraries (moment.js → date-fns)

### 6.2 PWA Optimization

**Service Worker**:
```javascript
// Cache static assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open('v1').then((cache) => {
      return cache.addAll([
        '/',
        '/styles.css',
        '/app.js',
        '/offline.html',
      ])
    })
  )
})
```

**Offline Support**:
- Cache API responses with stale-while-revalidate
- IndexedDB for structured data
- Background sync for failed requests

**Touch Optimization**:
- Minimum touch target: 44x44px
- Remove 300ms tap delay
- Prevent text selection on UI elements
- Add active states for feedback

**Performance**:
- Target: < 50KB initial load
- Vanilla JS (no framework overhead)
- CSS containment for paint optimization
- requestIdleCallback for non-critical tasks

### 6.3 React Native Optimization

**List Virtualization**:
```typescript
// Use FlatList instead of ScrollView
<FlatList
  data={items}
  renderItem={({ item }) => <Item {...item} />}
  keyExtractor={(item) => item.id}
  windowSize={10} // Render only visible + buffer
  maxToRenderPerBatch={10}
  updateCellsBatchingPeriod={50}
  removeClippedSubviews={true}
/>
```

**Image Optimization**:
```typescript
<Image
  source={{ uri: imageUrl }}
  resizeMode="cover"
  loadingIndicatorSource={placeholder}
  cache="force-cache"
/>
```

**Hermes Engine**:
- Enable Hermes for faster startup
- Ahead-of-time compilation
- Lower memory usage

**Performance Monitoring**:
```typescript
import { InteractionManager } from 'react-native'

InteractionManager.runAfterInteractions(() => {
  // Heavy operations after animations complete
})
```

### 6.4 Shared Optimization

**State Management**:
- Zustand (3KB) instead of Redux (45KB)
- Context API for theme/auth only
- URL state for filters/pagination

**API Calls**:
- React Query for caching and deduplication
- Optimistic updates for better UX
- Pagination/infinite scroll for large datasets

**Accessibility**:
- Semantic HTML on web
- accessibilityLabel on React Native
- Keyboard navigation support
- Screen reader testing

---

## 7. Component Implementation Examples

### 7.1 Universal Button Component

**packages/ui-core/Button.types.ts**:
```typescript
import { ReactNode } from 'react'

export interface ButtonProps {
  variant?: 'default' | 'destructive' | 'outline' | 'ghost' | 'link'
  size?: 'sm' | 'default' | 'lg' | 'icon'
  disabled?: boolean
  loading?: boolean
  children: ReactNode
  onPress: () => void
  className?: string // Web only
  testID?: string
}
```

**packages/ui-web/Button.tsx**:
```typescript
import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { ButtonProps } from "@rag/ui-core"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-md text-sm font-medium transition-colors disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-stone-700 text-white hover:bg-stone-600",
        destructive: "bg-red-600 text-white hover:bg-red-700",
        outline: "border-2 border-stone-700 hover:bg-stone-900",
        ghost: "hover:bg-stone-900",
        link: "text-stone-400 underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 px-3",
        lg: "h-11 px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, disabled, loading, children, onPress, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        disabled={disabled || loading}
        onClick={onPress}
        {...props}
      >
        {loading && <span className="loading-spinner" />}
        {children}
      </button>
    )
  }
)
```

**packages/ui-mobile/Button.tsx**:
```typescript
import React from 'react'
import { TouchableOpacity, Text, StyleSheet, ActivityIndicator } from 'react-native'
import { ButtonProps } from "@rag/ui-core"
import { colors, spacing, typography } from '@rag/design-tokens'

export const Button: React.FC<ButtonProps> = ({
  variant = 'default',
  size = 'default',
  disabled,
  loading,
  children,
  onPress,
  testID,
}) => {
  const buttonStyle = [
    styles.base,
    styles[variant],
    styles[`size_${size}`],
    (disabled || loading) && styles.disabled,
  ]

  const textStyle = [
    styles.text,
    styles[`text_${variant}`],
  ]

  return (
    <TouchableOpacity
      style={buttonStyle}
      onPress={onPress}
      disabled={disabled || loading}
      activeOpacity={0.7}
      testID={testID}
    >
      {loading && <ActivityIndicator size="small" color="white" style={styles.loader} />}
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
    gap: spacing.sm,
  },
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
  size_sm: {
    height: 36,
    paddingHorizontal: spacing.md,
  },
  size_default: {
    height: 44,
    paddingHorizontal: spacing.lg,
  },
  size_lg: {
    height: 52,
    paddingHorizontal: spacing.xl,
  },
  size_icon: {
    height: 44,
    width: 44,
    paddingHorizontal: 0,
  },
  disabled: {
    opacity: 0.5,
  },
  text: {
    fontSize: typography.fontSize.base,
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
  loader: {
    marginRight: spacing.xs,
  },
})
```

### 7.2 Adaptive Search Bar

**packages/ui-core/SearchBar.types.ts**:
```typescript
export interface SearchBarProps {
  placeholder?: string
  value: string
  onChange: (value: string) => void
  onSubmit?: (value: string) => void
  onFocus?: () => void
  onBlur?: () => void
  autoFocus?: boolean
  showCancel?: boolean
}
```

**packages/ui-web/SearchBar.tsx**:
```typescript
import React from 'react'
import { Input } from './Input'
import { Search } from 'lucide-react'

export const SearchBar: React.FC<SearchBarProps> = ({
  placeholder = "Search...",
  value,
  onChange,
  onSubmit,
  autoFocus,
}) => {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && onSubmit) {
      onSubmit(value)
    }
  }

  return (
    <div className="relative">
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-stone-500" />
      <Input
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        autoFocus={autoFocus}
        className="pl-10"
      />
    </div>
  )
}
```

**packages/ui-mobile/SearchBar.tsx**:
```typescript
import React, { useRef } from 'react'
import { View, TextInput, TouchableOpacity, StyleSheet } from 'react-native'
import { colors, spacing } from '@rag/design-tokens'

export const SearchBar: React.FC<SearchBarProps> = ({
  placeholder = "Search...",
  value,
  onChange,
  onSubmit,
  onFocus,
  onBlur,
  autoFocus,
  showCancel = false,
}) => {
  const inputRef = useRef<TextInput>(null)
  const [isFocused, setIsFocused] = React.useState(false)

  const handleFocus = () => {
    setIsFocused(true)
    onFocus?.()
  }

  const handleBlur = () => {
    setIsFocused(false)
    onBlur?.()
  }

  const handleCancel = () => {
    onChange('')
    inputRef.current?.blur()
  }

  return (
    <View style={styles.container}>
      <View style={[styles.inputContainer, isFocused && styles.inputContainerFocused]}>
        <TextInput
          ref={inputRef}
          style={styles.input}
          placeholder={placeholder}
          value={value}
          onChangeText={onChange}
          onSubmitEditing={() => onSubmit?.(value)}
          onFocus={handleFocus}
          onBlur={handleBlur}
          autoFocus={autoFocus}
          returnKeyType="search"
          clearButtonMode="while-editing"
        />
      </View>
      {(showCancel || isFocused) && (
        <TouchableOpacity onPress={handleCancel} style={styles.cancelButton}>
          <Text style={styles.cancelText}>Cancel</Text>
        </TouchableOpacity>
      )}
    </View>
  )
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  inputContainer: {
    flex: 1,
    height: 44,
    backgroundColor: colors.stone900,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  inputContainerFocused: {
    borderColor: colors.primary,
  },
  input: {
    flex: 1,
    paddingHorizontal: spacing.md,
    color: colors.white,
    fontSize: 16,
  },
  cancelButton: {
    paddingHorizontal: spacing.sm,
  },
  cancelText: {
    color: colors.primary,
    fontSize: 16,
  },
})
```

### 7.3 Domain Component: Product Card

**packages/domain/ProductCard/ProductCard.types.ts**:
```typescript
export interface Product {
  id: string
  name: string
  description: string
  imageUrl: string
  price: number
  stock: number
  category: string
}

export interface ProductCardProps {
  product: Product
  onPress: (productId: string) => void
  variant?: 'grid' | 'list'
}
```

**packages/domain/ProductCard/ProductCard.tsx** (Universal):
```typescript
import React from 'react'
import { Platform } from 'react-native'
import { Card, Badge, Button } from '@rag/ui'

export const ProductCard: React.FC<ProductCardProps> = ({
  product,
  onPress,
  variant = 'grid',
}) => {
  const isWeb = Platform.OS === 'web'

  return (
    <Card
      variant="outlined"
      className={variant === 'grid' ? 'max-w-sm' : 'flex-row'}
    >
      <Image
        source={{ uri: product.imageUrl }}
        style={variant === 'grid' ? styles.imageGrid : styles.imageList}
        resizeMode="cover"
      />
      <View style={styles.content}>
        <Text style={styles.name}>{product.name}</Text>
        <Text style={styles.description} numberOfLines={2}>
          {product.description}
        </Text>
        <View style={styles.footer}>
          <Badge variant={product.stock > 0 ? 'success' : 'destructive'}>
            {product.stock > 0 ? 'In Stock' : 'Out of Stock'}
          </Badge>
          <Text style={styles.price}>${product.price.toFixed(2)}</Text>
        </View>
        <Button
          onPress={() => onPress(product.id)}
          disabled={product.stock === 0}
        >
          Add to Cart
        </Button>
      </View>
    </Card>
  )
}
```

---

## 8. Migration Strategy

### 8.1 Phase 1: Foundation (Week 1-2)
- Set up monorepo structure (pnpm workspaces)
- Create design token system
- Implement core types and interfaces
- Set up storybook for component documentation

### 8.2 Phase 2: Core Components (Week 3-4)
- Migrate Button, Input, Card (highest usage)
- Implement platform-specific adaptations
- Write unit tests (Jest + React Testing Library)
- Document usage examples

### 8.3 Phase 3: Domain Components (Week 5-6)
- Migrate ProductCard, OrderItem, UserProfile
- Refactor to use new core components
- Update API integration layer
- End-to-end testing (Playwright/Detox)

### 8.4 Phase 4: Platform-Specific (Week 7-8)
- Implement mobile-only components (BottomSheet, PullToRefresh)
- Optimize web components (DataTable, Sidebar)
- Performance testing and optimization
- Accessibility audit

### 8.5 Phase 5: Production (Week 9-10)
- Gradual rollout with feature flags
- Monitor performance metrics
- Gather user feedback
- Final optimizations

---

## 9. Testing Strategy

### 9.1 Unit Tests
```typescript
// Button.test.tsx
import { render, fireEvent } from '@testing-library/react-native'
import { Button } from './Button'

describe('Button', () => {
  it('renders correctly', () => {
    const { getByText } = render(<Button>Click me</Button>)
    expect(getByText('Click me')).toBeTruthy()
  })

  it('calls onPress when clicked', () => {
    const onPress = jest.fn()
    const { getByText } = render(<Button onPress={onPress}>Click</Button>)
    fireEvent.press(getByText('Click'))
    expect(onPress).toHaveBeenCalledTimes(1)
  })

  it('disables interaction when loading', () => {
    const onPress = jest.fn()
    const { getByText } = render(<Button loading onPress={onPress}>Click</Button>)
    fireEvent.press(getByText('Click'))
    expect(onPress).not.toHaveBeenCalled()
  })
})
```

### 9.2 Visual Regression Tests (Chromatic)
```typescript
// Button.stories.tsx
import type { Meta, StoryObj } from '@storybook/react'
import { Button } from './Button'

const meta: Meta<typeof Button> = {
  title: 'Core/Button',
  component: Button,
  args: {
    children: 'Button',
  },
}

export default meta
type Story = StoryObj<typeof Button>

export const Default: Story = {}
export const Destructive: Story = { args: { variant: 'destructive' } }
export const Loading: Story = { args: { loading: true } }
export const Disabled: Story = { args: { disabled: true } }
```

### 9.3 E2E Tests (Playwright/Detox)
```typescript
// login.e2e.ts
describe('Login Flow', () => {
  it('should login successfully', async () => {
    await element(by.id('email-input')).typeText('admin@example.com')
    await element(by.id('password-input')).typeText('password123')
    await element(by.id('login-button')).tap()

    await expect(element(by.text('Dashboard'))).toBeVisible()
  })
})
```

---

## 10. Performance Benchmarks

### 10.1 Target Metrics

**Web (Next.js)**:
- First Contentful Paint: < 1.5s
- Time to Interactive: < 3.5s
- Lighthouse Score: > 90
- Bundle Size: < 150KB (gzipped)

**PWA**:
- First Contentful Paint: < 1s
- Time to Interactive: < 2s
- Offline Load: < 500ms
- Bundle Size: < 50KB (gzipped)

**React Native**:
- App Launch Time: < 2s (iOS), < 3s (Android)
- JS Bundle Size: < 2MB
- Frame Rate: 60fps during animations
- Memory Usage: < 100MB

### 10.2 Monitoring Tools

- **Web**: Lighthouse CI, WebPageTest, Chrome DevTools
- **PWA**: Lighthouse, Application tab (Service Workers)
- **React Native**: Flipper, React DevTools, Xcode Instruments

---

## 11. Documentation Requirements

### 11.1 Component API Docs
- Props interface with types
- Usage examples (code snippets)
- Accessibility notes
- Platform compatibility matrix
- Performance considerations

### 11.2 Storybook
- Interactive component playground
- All variants and states
- Responsive preview (mobile/tablet/desktop)
- Code snippets with copy button
- Design token reference

### 11.3 Migration Guides
- Legacy component → New component mapping
- Breaking changes
- Codemod scripts for automated migration
- Common pitfalls and solutions

---

## 12. Key Decisions and Trade-offs

### 12.1 Monorepo vs Multi-repo
**Decision**: Monorepo (pnpm workspaces)
**Reason**: Easier to share types, enforce consistency, atomic changes
**Trade-off**: More complex CI/CD, larger repository size

### 12.2 React Native Web vs Separate Web
**Decision**: Separate implementations
**Reason**: Better performance, smaller bundles, platform-optimized UX
**Trade-off**: More code to maintain, potential drift between platforms

### 12.3 Styling: CSS-in-JS vs StyleSheet
**Decision**: Platform-native (Tailwind for web, StyleSheet for mobile)
**Reason**: Best performance, leverages platform strengths
**Trade-off**: No shared styles, design tokens only

### 12.4 State Management: Redux vs Zustand
**Decision**: Zustand
**Reason**: 3KB vs 45KB, simpler API, no boilerplate
**Trade-off**: Less ecosystem, fewer devtools

---

## 13. Success Metrics

### 13.1 Developer Experience
- Component reuse rate: > 70%
- Time to implement new feature: -30%
- Code duplication: < 10%
- Developer satisfaction score: > 8/10

### 13.2 User Experience
- Load time improvement: -40%
- Frame rate: consistent 60fps
- Crash rate: < 0.1%
- User satisfaction: > 4.5/5

### 13.3 Business Metrics
- Development velocity: +50%
- Bug count: -40%
- Maintenance cost: -30%
- Time to market: -25%

---

## 14. Conclusion

This comprehensive component classification provides a roadmap for building a unified component library across web, PWA, and React Native platforms. Key outcomes:

1. **70+ shared components** with consistent APIs
2. **Design token system** ensuring visual consistency
3. **Platform-optimized implementations** for best performance
4. **Developer-friendly architecture** with TypeScript and testing
5. **Migration strategy** for gradual adoption

**Next Steps**:
1. Approve component classification
2. Set up monorepo infrastructure
3. Begin Phase 1: Foundation (design tokens)
4. Weekly progress reviews

**Estimated Timeline**: 10 weeks for complete migration
**Team Size**: 2-3 frontend developers
**Risk Level**: Medium (well-defined scope, proven technologies)

---

**Document Version**: 1.0.0
**Last Updated**: 2025-11-12
**Author**: Claude Code (Frontend Agent)
**Review Status**: Pending Approval
