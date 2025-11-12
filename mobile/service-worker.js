/**
 * Service Worker with Background Sync
 * Complete offline functionality for PWA
 * Version: v8.3.0
 */

const CACHE_VERSION = 'v8.3.0';
const CACHE_STATIC = `static-${CACHE_VERSION}`;
const CACHE_DYNAMIC = `dynamic-${CACHE_VERSION}`;
const CACHE_IMAGES = `images-${CACHE_VERSION}`;

// Files to cache immediately
const STATIC_ASSETS = [
    '/mobile/pwa/index.html',
    '/mobile/pwa/login.html',
    '/mobile/pwa/qr-scan.html',
    '/mobile/pwa/upload.html',
    '/mobile/pwa/quality-inspection.html',
    '/mobile/pwa/work-orders.html',
    '/js/auth.js',
    '/js/navbar.js',
    '/js/offline-storage.js',
    '/mobile/manifest.json',
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
    console.log('[SW] Installing service worker...', CACHE_VERSION);

    event.waitUntil(
        caches.open(CACHE_STATIC).then((cache) => {
            console.log('[SW] Caching static assets');
            return cache.addAll(STATIC_ASSETS);
        })
    );

    self.skipWaiting(); // Activate immediately
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('[SW] Activating service worker...', CACHE_VERSION);

    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames
                    .filter((name) => name.startsWith('static-') || name.startsWith('dynamic-') || name.startsWith('images-'))
                    .filter((name) => name !== CACHE_STATIC && name !== CACHE_DYNAMIC && name !== CACHE_IMAGES)
                    .map((name) => {
                        console.log('[SW] Deleting old cache:', name);
                        return caches.delete(name);
                    })
            );
        })
    );

    return self.clients.claim(); // Take control immediately
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
    const {request} = event;
    const url = new URL(request.url);

    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }

    // Skip chrome-extension and other non-http(s) requests
    if (!url.protocol.startsWith('http')) {
        return;
    }

    // API requests - Network First strategy
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(networkFirstStrategy(request));
        return;
    }

    // Images - Cache First strategy
    if (request.destination === 'image' || url.pathname.match(/\.(jpg|jpeg|png|gif|webp|svg)$/i)) {
        event.respondWith(cacheFirstStrategy(request, CACHE_IMAGES));
        return;
    }

    // Static assets - Cache First strategy
    if (STATIC_ASSETS.includes(url.pathname)) {
        event.respondWith(cacheFirstStrategy(request, CACHE_STATIC));
        return;
    }

    // Everything else - Network First with cache fallback
    event.respondWith(networkFirstStrategy(request));
});

/**
 * Cache First Strategy
 * Try cache first, fallback to network
 */
async function cacheFirstStrategy(request, cacheName = CACHE_DYNAMIC) {
    const cache = await caches.open(cacheName);
    const cached = await cache.match(request);

    if (cached) {
        console.log('[SW] Cache hit:', request.url);
        return cached;
    }

    try {
        const response = await fetch(request);
        if (response && response.status === 200) {
            cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        console.error('[SW] Fetch failed:', request.url, error);
        return new Response('Offline', {status: 503, statusText: 'Service Unavailable'});
    }
}

/**
 * Network First Strategy
 * Try network first, fallback to cache
 */
async function networkFirstStrategy(request) {
    try {
        const response = await fetch(request);

        if (response && response.status === 200) {
            const cache = await caches.open(CACHE_DYNAMIC);
            cache.put(request, response.clone());
        }

        return response;
    } catch (error) {
        console.log('[SW] Network failed, trying cache:', request.url);

        const cached = await caches.match(request);
        if (cached) {
            return cached;
        }

        // Return offline page for navigation requests
        if (request.mode === 'navigate') {
            const offlineCache = await caches.open(CACHE_STATIC);
            const offlinePage = await offlineCache.match('/mobile/pwa/index.html');
            if (offlinePage) {
                return offlinePage;
            }
        }

        return new Response('Offline', {status: 503, statusText: 'Service Unavailable'});
    }
}

// Background Sync - sync pending data when online
self.addEventListener('sync', (event) => {
    console.log('[SW] Background sync triggered:', event.tag);

    if (event.tag === 'sync-data') {
        event.waitUntil(syncPendingData());
    } else if (event.tag.startsWith('sync-work-order-')) {
        const woId = event.tag.replace('sync-work-order-', '');
        event.waitUntil(syncWorkOrder(woId));
    } else if (event.tag === 'sync-analytics') {
        event.waitUntil(syncAnalytics());
    }
});

/**
 * Sync all pending data
 */
async function syncPendingData() {
    console.log('[SW] Syncing pending data...');

    try {
        // Open IndexedDB
        const db = await openIndexedDB();
        const pendingItems = await getPendingSync(db);

        if (pendingItems.length === 0) {
            console.log('[SW] No pending items to sync');
            return;
        }

        console.log(`[SW] Syncing ${pendingItems.length} pending items`);

        const results = await Promise.allSettled(
            pendingItems.map(item => syncItem(item, db))
        );

        const succeeded = results.filter(r => r.status === 'fulfilled').length;
        const failed = results.filter(r => r.status === 'rejected').length;

        console.log(`[SW] Sync complete: ${succeeded} succeeded, ${failed} failed`);

        // Notify clients
        await notifyClients('sync-complete', {succeeded, failed});

    } catch (error) {
        console.error('[SW] Sync error:', error);
    }
}

/**
 * Sync single item
 */
async function syncItem(item, db) {
    const {type, data} = item;

    try {
        let response;

        if (type === 'work_order_update') {
            response = await fetch(`/api/v1/mobile-api/work-orders/${data.wo_id}/update`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data),
            });
        } else if (type === 'analytics_event') {
            response = await fetch('/api/v1/mobile-api/analytics/event', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data),
            });
        }

        if (response && response.ok) {
            // Remove from pending sync
            await removePendingSync(db, item.id);
            console.log('[SW] Synced item:', item.id);
        } else {
            throw new Error(`HTTP ${response?.status}`);
        }
    } catch (error) {
        console.error('[SW] Failed to sync item:', item.id, error);

        // Increment retry count
        await incrementRetryCount(db, item.id);

        throw error;
    }
}

/**
 * Sync specific work order
 */
async function syncWorkOrder(woId) {
    console.log('[SW] Syncing work order:', woId);

    try {
        const db = await openIndexedDB();
        const wo = await getWorkOrder(db, woId);

        if (!wo) {
            console.log('[SW] Work order not found:', woId);
            return;
        }

        const response = await fetch(`/api/v1/mobile-api/work-orders/${woId}/update`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(wo),
        });

        if (response.ok) {
            console.log('[SW] Work order synced:', woId);
            await notifyClients('work-order-synced', {wo_id: woId});
        }
    } catch (error) {
        console.error('[SW] Work order sync failed:', woId, error);
    }
}

/**
 * Sync analytics events
 */
async function syncAnalytics() {
    console.log('[SW] Syncing analytics...');

    try {
        const db = await openIndexedDB();
        const events = await getAnalyticsEvents(db);

        if (events.length === 0) {
            return;
        }

        const response = await fetch('/api/v1/mobile-api/analytics/batch', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({events}),
        });

        if (response.ok) {
            console.log(`[SW] Synced ${events.length} analytics events`);
            await clearAnalyticsEvents(db);
        }
    } catch (error) {
        console.error('[SW] Analytics sync failed:', error);
    }
}

// Push Notification event
self.addEventListener('push', (event) => {
    console.log('[SW] Push received:', event);

    let data = {title: 'RAG Enterprise', body: 'New notification'};

    if (event.data) {
        data = event.data.json();
    }

    const options = {
        body: data.body,
        icon: '/assets/icon-192x192.png',
        badge: '/assets/badge-72x72.png',
        tag: data.tag || 'default',
        data: data.data || {},
        actions: data.actions || [],
        vibrate: [200, 100, 200],
    };

    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

// Notification click event
self.addEventListener('notificationclick', (event) => {
    console.log('[SW] Notification clicked:', event.notification.tag);

    event.notification.close();

    const urlToOpen = event.notification.data?.url || '/mobile/pwa/index.html';

    event.waitUntil(
        clients.matchAll({type: 'window', includeUncontrolled: true}).then((clientList) => {
            // Check if any client is already open
            for (const client of clientList) {
                if (client.url.includes(urlToOpen) && 'focus' in client) {
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

// Message event - communicate with clients
self.addEventListener('message', (event) => {
    console.log('[SW] Message received:', event.data);

    if (event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    } else if (event.data.type === 'CLEAR_CACHE') {
        event.waitUntil(clearAllCaches());
    } else if (event.data.type === 'SYNC_NOW') {
        event.waitUntil(syncPendingData());
    }
});

/**
 * Helper: Open IndexedDB
 */
function openIndexedDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('RAGOfflineDB', 1);
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
}

/**
 * Helper: Get pending sync items
 */
function getPendingSync(db) {
    return new Promise((resolve, reject) => {
        const transaction = db.transaction(['pending_sync'], 'readonly');
        const store = transaction.objectStore('pending_sync');
        const request = store.getAll();
        request.onsuccess = () => resolve(request.result || []);
        request.onerror = () => reject(request.error);
    });
}

/**
 * Helper: Remove synced item
 */
function removePendingSync(db, id) {
    return new Promise((resolve, reject) => {
        const transaction = db.transaction(['pending_sync'], 'readwrite');
        const store = transaction.objectStore('pending_sync');
        const request = store.delete(id);
        request.onsuccess = () => resolve();
        request.onerror = () => reject(request.error);
    });
}

/**
 * Helper: Increment retry count
 */
function incrementRetryCount(db, id) {
    return new Promise((resolve, reject) => {
        const transaction = db.transaction(['pending_sync'], 'readwrite');
        const store = transaction.objectStore('pending_sync');
        const getRequest = store.get(id);

        getRequest.onsuccess = () => {
            const item = getRequest.result;
            if (item) {
                item.retries = (item.retries || 0) + 1;
                store.put(item);
            }
            resolve();
        };

        getRequest.onerror = () => reject(getRequest.error);
    });
}

/**
 * Helper: Get work order
 */
function getWorkOrder(db, woId) {
    return new Promise((resolve, reject) => {
        const transaction = db.transaction(['work_orders'], 'readonly');
        const store = transaction.objectStore('work_orders');
        const request = store.get(woId);
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
}

/**
 * Helper: Get analytics events
 */
function getAnalyticsEvents(db) {
    // TODO: Implement analytics events storage
    return Promise.resolve([]);
}

/**
 * Helper: Clear analytics events
 */
function clearAnalyticsEvents(db) {
    // TODO: Implement
    return Promise.resolve();
}

/**
 * Helper: Notify all clients
 */
async function notifyClients(type, data) {
    const clients = await self.clients.matchAll({includeUncontrolled: true});
    clients.forEach(client => {
        client.postMessage({type, data});
    });
}

/**
 * Helper: Clear all caches
 */
async function clearAllCaches() {
    const cacheNames = await caches.keys();
    await Promise.all(cacheNames.map(name => caches.delete(name)));
    console.log('[SW] All caches cleared');
}

console.log('[SW] Service Worker script loaded', CACHE_VERSION);
