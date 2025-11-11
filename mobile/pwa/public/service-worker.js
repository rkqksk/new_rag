/**
 * Service Worker - v7.4.0 Mobile PWA
 *
 * Features:
 * - Offline caching
 * - Background sync
 * - Push notifications
 * - Cache strategies
 */

const CACHE_NAME = 'rag-mobile-v7.4.0';
const API_CACHE = 'rag-api-cache-v1';
const IMAGE_CACHE = 'rag-image-cache-v1';

// Assets to cache on install
const STATIC_ASSETS = [
  '/mobile/',
  '/mobile/index.html',
  '/mobile/css/app.css',
  '/mobile/js/app.js',
  '/mobile/manifest.json',
  '/assets/icon-192x192.png',
  '/assets/icon-512x512.png',
  '/assets/offline.html'
];

// API endpoints to cache
const API_URLS = [
  '/api/v1/products',
  '/api/v1/categories',
  '/api/v1/work-orders'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('[ServiceWorker] Install event');

  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[ServiceWorker] Caching static assets');
      return cache.addAll(STATIC_ASSETS);
    }).then(() => {
      return self.skipWaiting();
    })
  );
});

// Activate event - clean old caches
self.addEventListener('activate', (event) => {
  console.log('[ServiceWorker] Activate event');

  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME &&
              cacheName !== API_CACHE &&
              cacheName !== IMAGE_CACHE) {
            console.log('[ServiceWorker] Removing old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      return self.clients.claim();
    })
  );
});

// Fetch event - network first, fall back to cache
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // API requests - Network first, cache fallback
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      networkFirstStrategy(request, API_CACHE)
    );
    return;
  }

  // Image requests - Cache first, network fallback
  if (request.destination === 'image') {
    event.respondWith(
      cacheFirstStrategy(request, IMAGE_CACHE)
    );
    return;
  }

  // Other requests - Cache first for static assets
  event.respondWith(
    cacheFirstStrategy(request, CACHE_NAME)
  );
});

// Network first strategy
async function networkFirstStrategy(request, cacheName) {
  try {
    const networkResponse = await fetch(request);

    // Clone response and cache it
    const cache = await caches.open(cacheName);
    cache.put(request, networkResponse.clone());

    return networkResponse;
  } catch (error) {
    console.log('[ServiceWorker] Network failed, trying cache:', error);

    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }

    // Return offline page for HTML requests
    if (request.headers.get('accept').includes('text/html')) {
      return caches.match('/assets/offline.html');
    }

    // Return offline JSON for API requests
    return new Response(
      JSON.stringify({
        error: 'Offline',
        message: 'No network connection',
        offline: true
      }),
      {
        status: 503,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
}

// Cache first strategy
async function cacheFirstStrategy(request, cacheName) {
  const cachedResponse = await caches.match(request);

  if (cachedResponse) {
    // Update cache in background
    fetch(request).then((networkResponse) => {
      caches.open(cacheName).then((cache) => {
        cache.put(request, networkResponse);
      });
    }).catch(() => {
      // Network failed, but we have cache
    });

    return cachedResponse;
  }

  try {
    const networkResponse = await fetch(request);

    // Cache the response
    const cache = await caches.open(cacheName);
    cache.put(request, networkResponse.clone());

    return networkResponse;
  } catch (error) {
    console.log('[ServiceWorker] Fetch failed:', error);

    // Return offline placeholder
    return new Response('Offline', { status: 503 });
  }
}

// Background Sync - sync data when online
self.addEventListener('sync', (event) => {
  console.log('[ServiceWorker] Sync event:', event.tag);

  if (event.tag === 'sync-uploads') {
    event.waitUntil(syncUploads());
  }

  if (event.tag === 'sync-work-orders') {
    event.waitUntil(syncWorkOrders());
  }
});

async function syncUploads() {
  console.log('[ServiceWorker] Syncing uploads...');

  try {
    // Get pending uploads from IndexedDB
    const pendingUploads = await getPendingUploads();

    for (const upload of pendingUploads) {
      try {
        await fetch('/api/v1/uploads/sync', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(upload)
        });

        // Remove from pending
        await removePendingUpload(upload.id);
      } catch (error) {
        console.error('[ServiceWorker] Upload sync failed:', error);
      }
    }

    // Notify clients
    self.clients.matchAll().then((clients) => {
      clients.forEach((client) => {
        client.postMessage({
          type: 'SYNC_COMPLETE',
          tag: 'sync-uploads'
        });
      });
    });
  } catch (error) {
    console.error('[ServiceWorker] Sync uploads error:', error);
    throw error;
  }
}

async function syncWorkOrders() {
  console.log('[ServiceWorker] Syncing work orders...');

  try {
    const response = await fetch('/api/v1/work-orders');
    const workOrders = await response.json();

    // Update IndexedDB
    await updateWorkOrders(workOrders);

    // Notify clients
    self.clients.matchAll().then((clients) => {
      clients.forEach((client) => {
        client.postMessage({
          type: 'WORK_ORDERS_UPDATED',
          data: workOrders
        });
      });
    });
  } catch (error) {
    console.error('[ServiceWorker] Sync work orders error:', error);
  }
}

// Push Notifications
self.addEventListener('push', (event) => {
  console.log('[ServiceWorker] Push received:', event);

  let notification = {
    title: 'RAG Enterprise',
    body: 'You have a new notification',
    icon: '/assets/icon-192x192.png',
    badge: '/assets/badge-72x72.png',
    vibrate: [200, 100, 200],
    data: {}
  };

  if (event.data) {
    try {
      const data = event.data.json();
      notification = {
        ...notification,
        ...data,
        data: data
      };
    } catch (error) {
      notification.body = event.data.text();
    }
  }

  event.waitUntil(
    self.registration.showNotification(notification.title, {
      body: notification.body,
      icon: notification.icon,
      badge: notification.badge,
      vibrate: notification.vibrate,
      data: notification.data,
      actions: [
        { action: 'open', title: '열기' },
        { action: 'close', title: '닫기' }
      ],
      tag: notification.data.tag || 'default',
      renotify: true,
      requireInteraction: notification.data.requireInteraction || false
    })
  );
});

// Notification click
self.addEventListener('notificationclick', (event) => {
  console.log('[ServiceWorker] Notification click:', event);

  event.notification.close();

  if (event.action === 'close') {
    return;
  }

  const urlToOpen = event.notification.data.url || '/mobile/';

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        // Check if app is already open
        for (const client of clientList) {
          if (client.url === urlToOpen && 'focus' in client) {
            return client.focus();
          }
        }

        // Open new window
        if (clients.openWindow) {
          return clients.openWindow(urlToOpen);
        }
      })
  );
});

// Message from clients
self.addEventListener('message', (event) => {
  console.log('[ServiceWorker] Message received:', event.data);

  if (event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }

  if (event.data.type === 'CACHE_URLS') {
    event.waitUntil(
      caches.open(API_CACHE).then((cache) => {
        return cache.addAll(event.data.urls);
      })
    );
  }

  if (event.data.type === 'CLEAR_CACHE') {
    event.waitUntil(
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => caches.delete(cacheName))
        );
      })
    );
  }
});

// IndexedDB helpers
async function getPendingUploads() {
  // TODO: Implement IndexedDB access
  return [];
}

async function removePendingUpload(id) {
  // TODO: Implement IndexedDB removal
}

async function updateWorkOrders(workOrders) {
  // TODO: Implement IndexedDB update
}

console.log('[ServiceWorker] Loaded successfully');
