# PWA Optimization Skill

## Overview
Expert in Progressive Web App development with service workers, offline capabilities, and performance optimization.

## Trigger Words
- pwa
- progressive web app
- service worker
- offline first
- web app manifest
- workbox

## Capabilities

### Service Worker Implementation

#### Basic Registration
```javascript
// Register service worker
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then(reg => console.log('SW registered'))
      .catch(err => console.error('SW registration failed'))
  })
}
```

#### Advanced Caching Strategies
```javascript
// sw.js with Workbox
import { precacheAndRoute } from 'workbox-precaching'
import { registerRoute } from 'workbox-routing'
import { StaleWhileRevalidate, NetworkFirst, CacheFirst } from 'workbox-strategies'
import { ExpirationPlugin } from 'workbox-expiration'

// Precache static assets
precacheAndRoute(self.__WB_MANIFEST)

// Cache API responses
registerRoute(
  ({ url }) => url.pathname.startsWith('/api/'),
  new NetworkFirst({
    cacheName: 'api-cache',
    plugins: [
      new ExpirationPlugin({
        maxEntries: 50,
        maxAgeSeconds: 5 * 60 // 5 minutes
      })
    ]
  })
)

// Cache images
registerRoute(
  ({ request }) => request.destination === 'image',
  new CacheFirst({
    cacheName: 'image-cache',
    plugins: [
      new ExpirationPlugin({
        maxEntries: 100,
        maxAgeSeconds: 30 * 24 * 60 * 60 // 30 days
      })
    ]
  })
)
```

### Offline Support

#### Offline Page Fallback
```javascript
import { offlineFallback } from 'workbox-recipes'
import { setDefaultHandler } from 'workbox-routing'
import { NetworkOnly } from 'workbox-strategies'

setDefaultHandler(new NetworkOnly())

offlineFallback({
  pageFallback: '/offline.html',
  imageFallback: '/static/offline-image.png',
  fontFallback: '/static/offline-font.woff2'
})
```

#### Background Sync
```javascript
import { BackgroundSyncPlugin } from 'workbox-background-sync'

const bgSyncPlugin = new BackgroundSyncPlugin('api-queue', {
  maxRetentionTime: 24 * 60 // Retry for 24 hours
})

registerRoute(
  ({ url }) => url.pathname.startsWith('/api/submit'),
  new NetworkOnly({
    plugins: [bgSyncPlugin]
  }),
  'POST'
)
```

### Web App Manifest

```json
{
  "name": "RAG Enterprise PWA",
  "short_name": "RAG PWA",
  "description": "AI-powered enterprise search PWA",
  "start_url": "/",
  "display": "standalone",
  "orientation": "portrait",
  "theme_color": "#3B82F6",
  "background_color": "#ffffff",
  "icons": [
    {
      "src": "/icon-192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ],
  "screenshots": [
    {
      "src": "/screenshot1.png",
      "sizes": "1280x720",
      "type": "image/png"
    }
  ],
  "categories": ["productivity", "business"],
  "shortcuts": [
    {
      "name": "Search",
      "url": "/search",
      "icons": [{ "src": "/search-icon.png", "sizes": "96x96" }]
    }
  ]
}
```

### Install Prompts

```javascript
let deferredPrompt

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault()
  deferredPrompt = e
  showInstallButton()
})

const installPWA = async () => {
  if (!deferredPrompt) return

  deferredPrompt.prompt()
  const { outcome } = await deferredPrompt.userChoice

  if (outcome === 'accepted') {
    console.log('PWA installed')
  }
  deferredPrompt = null
}
```

### Push Notifications

```javascript
// Request permission
const requestNotificationPermission = async () => {
  const permission = await Notification.requestPermission()
  if (permission === 'granted') {
    const registration = await navigator.serviceWorker.ready
    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlB64ToUint8Array(publicVapidKey)
    })
    // Send subscription to server
  }
}

// In service worker
self.addEventListener('push', (event) => {
  const data = event.data.json()
  const options = {
    body: data.body,
    icon: '/icon-192.png',
    badge: '/badge-72.png',
    vibrate: [100, 50, 100],
    data: { url: data.url },
    actions: [
      { action: 'explore', title: 'View' },
      { action: 'close', title: 'Dismiss' }
    ]
  }

  event.waitUntil(
    self.registration.showNotification(data.title, options)
  )
})
```

### Performance Optimization

#### App Shell Architecture
```javascript
// Precache app shell
const APP_SHELL = [
  '/',
  '/index.html',
  '/styles.css',
  '/app.js',
  '/manifest.json'
]

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open('app-shell-v1')
      .then(cache => cache.addAll(APP_SHELL))
  )
})
```

#### Resource Hints
```html
<!-- Preconnect to external domains -->
<link rel="preconnect" href="https://api.example.com">
<link rel="dns-prefetch" href="https://cdn.example.com">

<!-- Preload critical resources -->
<link rel="preload" href="/fonts/main.woff2" as="font" crossorigin>
<link rel="preload" href="/css/critical.css" as="style">

<!-- Prefetch future navigation resources -->
<link rel="prefetch" href="/js/page2.js">
```

### Lighthouse Optimization

```javascript
// Optimize for Core Web Vitals
// LCP - Largest Contentful Paint
const optimizeLCP = () => {
  // Preload hero image
  const link = document.createElement('link')
  link.rel = 'preload'
  link.as = 'image'
  link.href = '/hero.webp'
  document.head.appendChild(link)
}

// CLS - Cumulative Layout Shift
// Reserve space for dynamic content
.image-container {
  aspect-ratio: 16 / 9;
  background: #f0f0f0;
}

// FID - First Input Delay
// Defer non-critical JS
<script defer src="/non-critical.js"></script>
```

### Update Management

```javascript
// Handle service worker updates
let refreshing
navigator.serviceWorker.addEventListener('controllerchange', () => {
  if (refreshing) return
  window.location.reload()
  refreshing = true
})

// Skip waiting and activate immediately
self.addEventListener('message', (event) => {
  if (event.data === 'skipWaiting') {
    self.skipWaiting()
  }
})
```

## Vite PWA Plugin Configuration

```javascript
import { VitePWA } from 'vite-plugin-pwa'

export default {
  plugins: [
    VitePWA({
      registerType: 'autoUpdate',
      manifest: { /* manifest config */ },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg}'],
        runtimeCaching: [ /* caching strategies */ ]
      },
      devOptions: {
        enabled: true
      }
    })
  ]
}
```

## Testing

```javascript
// Test service worker
describe('Service Worker', () => {
  it('should cache responses', async () => {
    const cache = await caches.open('test-cache')
    await cache.add('/test-resource')
    const response = await cache.match('/test-resource')
    expect(response).toBeDefined()
  })
})
```

## Common Commands

```bash
# Build PWA
pnpm build:pwa

# Analyze bundle
pnpm analyze

# Run Lighthouse
lighthouse https://localhost:5173 --view

# Test service worker
workbox wizard
```

## Related Skills
- offline-first
- app-shell
- service-worker-mcp
- workbox-mcp
- lighthouse-mcp