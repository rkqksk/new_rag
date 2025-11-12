# Platform Bridge Skill

## Overview
Expert in cross-platform code sharing, platform detection, and conditional rendering across web, mobile, and PWA.

## Trigger Words
- cross platform
- platform bridge
- platform specific
- code sharing
- platform detection
- conditional rendering

## Capabilities

### Platform Detection

#### Universal Platform Detection
```typescript
// platform.ts - Universal platform detection
export enum Platform {
  Web = 'web',
  Mobile = 'mobile',
  PWA = 'pwa',
  Desktop = 'desktop'
}

export const detectPlatform = (): Platform => {
  // React Native detection
  if (typeof navigator !== 'undefined' && navigator.product === 'ReactNative') {
    return Platform.Mobile
  }

  // PWA detection
  if (typeof window !== 'undefined') {
    const isPWA = window.matchMedia('(display-mode: standalone)').matches ||
                  window.navigator.standalone ||
                  document.referrer.includes('android-app://')
    if (isPWA) return Platform.PWA
  }

  // Electron/Desktop detection
  if (typeof process !== 'undefined' && process.versions?.electron) {
    return Platform.Desktop
  }

  // Default to web
  return Platform.Web
}
```

### File Extension Strategy

```
components/
├── Button.tsx          # Shared logic
├── Button.web.tsx      # Web-specific
├── Button.mobile.tsx   # Mobile-specific
└── Button.pwa.tsx      # PWA-specific
```

#### Metro Configuration (React Native)
```javascript
// metro.config.js
module.exports = {
  resolver: {
    sourceExts: ['mobile.tsx', 'tsx', 'mobile.ts', 'ts', 'jsx', 'js', 'json']
  }
}
```

#### Webpack Configuration (Web/PWA)
```javascript
// webpack.config.js
module.exports = {
  resolve: {
    extensions: ['.web.tsx', '.tsx', '.web.ts', '.ts', '.js'],
    alias: {
      'react-native$': 'react-native-web'
    }
  }
}
```

### Conditional Component Loading

```typescript
// Dynamic component loading based on platform
import { lazy, Suspense } from 'react'
import { detectPlatform, Platform } from './platform'

const loadPlatformComponent = (componentName: string) => {
  const platform = detectPlatform()

  switch (platform) {
    case Platform.Mobile:
      return lazy(() => import(`./components/${componentName}.mobile`))
    case Platform.PWA:
      return lazy(() => import(`./components/${componentName}.pwa`))
    default:
      return lazy(() => import(`./components/${componentName}.web`))
  }
}

// Usage
const NavigationComponent = loadPlatformComponent('Navigation')

export const App = () => (
  <Suspense fallback={<div>Loading...</div>}>
    <NavigationComponent />
  </Suspense>
)
```

### Shared Business Logic

```typescript
// hooks/useAuth.ts - Shared authentication logic
import { useState, useEffect } from 'react'
import { detectPlatform, Platform } from '../utils/platform'

export const useAuth = () => {
  const [token, setToken] = useState<string | null>(null)
  const platform = detectPlatform()

  const saveToken = async (newToken: string) => {
    if (platform === Platform.Mobile) {
      // React Native secure storage
      const { setItemAsync } = await import('expo-secure-store')
      await setItemAsync('auth_token', newToken)
    } else if (platform === Platform.Web || platform === Platform.PWA) {
      // Web localStorage with encryption
      const encrypted = await encryptToken(newToken)
      localStorage.setItem('auth_token', encrypted)
    }
    setToken(newToken)
  }

  const loadToken = async () => {
    if (platform === Platform.Mobile) {
      const { getItemAsync } = await import('expo-secure-store')
      const stored = await getItemAsync('auth_token')
      setToken(stored)
    } else {
      const encrypted = localStorage.getItem('auth_token')
      if (encrypted) {
        const decrypted = await decryptToken(encrypted)
        setToken(decrypted)
      }
    }
  }

  return { token, saveToken, loadToken }
}
```

### Navigation Bridge

```typescript
// navigation/Navigator.tsx
import { detectPlatform, Platform } from '../utils/platform'

export interface NavigationProps {
  to: string
  params?: Record<string, any>
}

export class NavigationBridge {
  private platform = detectPlatform()

  async navigate({ to, params }: NavigationProps) {
    switch (this.platform) {
      case Platform.Mobile:
        // React Navigation
        const { navigation } = await import('@react-navigation/native')
        navigation.navigate(to, params)
        break

      case Platform.Web:
      case Platform.PWA:
        // React Router or Next.js
        if (typeof window !== 'undefined') {
          const url = new URL(to, window.location.href)
          Object.entries(params || {}).forEach(([key, value]) => {
            url.searchParams.append(key, value)
          })
          window.history.pushState({}, '', url.toString())
        }
        break
    }
  }

  async goBack() {
    switch (this.platform) {
      case Platform.Mobile:
        const { navigation } = await import('@react-navigation/native')
        navigation.goBack()
        break

      default:
        window.history.back()
    }
  }
}
```

### Storage Bridge

```typescript
// storage/StorageBridge.ts
export interface StorageAdapter {
  getItem(key: string): Promise<string | null>
  setItem(key: string, value: string): Promise<void>
  removeItem(key: string): Promise<void>
  clear(): Promise<void>
}

// Web implementation
class WebStorage implements StorageAdapter {
  async getItem(key: string) {
    return localStorage.getItem(key)
  }

  async setItem(key: string, value: string) {
    localStorage.setItem(key, value)
  }

  async removeItem(key: string) {
    localStorage.removeItem(key)
  }

  async clear() {
    localStorage.clear()
  }
}

// React Native implementation
class MobileStorage implements StorageAdapter {
  private AsyncStorage: any

  constructor() {
    import('@react-native-async-storage/async-storage').then(module => {
      this.AsyncStorage = module.default
    })
  }

  async getItem(key: string) {
    return this.AsyncStorage.getItem(key)
  }

  async setItem(key: string, value: string) {
    return this.AsyncStorage.setItem(key, value)
  }

  async removeItem(key: string) {
    return this.AsyncStorage.removeItem(key)
  }

  async clear() {
    return this.AsyncStorage.clear()
  }
}

// Factory
export const createStorage = (): StorageAdapter => {
  const platform = detectPlatform()
  return platform === Platform.Mobile ? new MobileStorage() : new WebStorage()
}
```

### API Bridge

```typescript
// api/ApiBridge.ts
export class ApiBridge {
  private platform = detectPlatform()
  private baseURL: string

  constructor() {
    // Platform-specific API endpoints
    this.baseURL = this.getBaseURL()
  }

  private getBaseURL(): string {
    switch (this.platform) {
      case Platform.Mobile:
        // Use production API for mobile
        return 'https://api.example.com'
      case Platform.Web:
      case Platform.PWA:
        // Use relative URL for web
        return '/api'
      default:
        return 'http://localhost:8001'
    }
  }

  async fetch(endpoint: string, options?: RequestInit) {
    const url = `${this.baseURL}${endpoint}`

    // Platform-specific headers
    const headers = {
      'Content-Type': 'application/json',
      'X-Platform': this.platform,
      ...options?.headers
    }

    return fetch(url, { ...options, headers })
  }
}
```

### Style Bridge

```typescript
// styles/StyleBridge.ts
import { Platform as RNPlatform, StyleSheet } from 'react-native'

export const createStyles = (styles: any) => {
  const platform = detectPlatform()

  if (platform === Platform.Mobile) {
    // React Native StyleSheet
    return StyleSheet.create(styles)
  }

  // Web CSS-in-JS
  return Object.entries(styles).reduce((acc, [key, value]) => {
    acc[key] = convertToCSS(value)
    return acc
  }, {} as any)
}

const convertToCSS = (style: any): string => {
  return Object.entries(style)
    .map(([prop, value]) => {
      const cssProp = prop.replace(/([A-Z])/g, '-$1').toLowerCase()
      return `${cssProp}: ${value}`
    })
    .join('; ')
}
```

### Feature Flags

```typescript
// features/FeatureFlags.ts
export interface FeatureConfig {
  web: boolean
  mobile: boolean
  pwa: boolean
}

export const features: Record<string, FeatureConfig> = {
  biometricAuth: {
    web: false,
    mobile: true,
    pwa: false
  },
  offlineMode: {
    web: false,
    mobile: true,
    pwa: true
  },
  pushNotifications: {
    web: true,
    mobile: true,
    pwa: true
  },
  camera: {
    web: true,
    mobile: true,
    pwa: true
  }
}

export const isFeatureEnabled = (featureName: string): boolean => {
  const platform = detectPlatform()
  const feature = features[featureName]

  if (!feature) return false

  switch (platform) {
    case Platform.Web:
      return feature.web
    case Platform.Mobile:
      return feature.mobile
    case Platform.PWA:
      return feature.pwa
    default:
      return false
  }
}
```

### Build Configuration

#### Monorepo Package.json
```json
{
  "scripts": {
    "dev:web": "next dev",
    "dev:mobile": "expo start",
    "dev:pwa": "vite",
    "build:web": "next build",
    "build:mobile": "eas build",
    "build:pwa": "vite build",
    "build:all": "turbo run build"
  }
}
```

#### Turbo Configuration
```json
{
  "pipeline": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": [".next/**", "dist/**", "build/**"]
    }
  }
}
```

## Testing Across Platforms

```typescript
// __tests__/platform.test.ts
describe('Platform Bridge', () => {
  it('should detect correct platform', () => {
    // Mock for web
    global.window = { matchMedia: jest.fn() }
    expect(detectPlatform()).toBe(Platform.Web)

    // Mock for React Native
    global.navigator = { product: 'ReactNative' }
    expect(detectPlatform()).toBe(Platform.Mobile)
  })
})
```

## Related Skills
- component-library
- mobile-ui
- pwa-optimization
- frontend-platform