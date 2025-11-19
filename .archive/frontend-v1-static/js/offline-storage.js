/**
 * Offline Storage with IndexedDB
 * Complete offline data management for PWA
 * Version: v8.3.0
 */

const DB_NAME = 'RAGOfflineDB';
const DB_VERSION = 1;

// Store names
const STORES = {
    PRODUCTS: 'products',
    SEARCHES: 'searches',
    WORK_ORDERS: 'work_orders',
    PENDING_SYNC: 'pending_sync',
    CACHE_META: 'cache_meta',
};

class OfflineStorage {
    constructor() {
        this.db = null;
        this.isInitialized = false;
    }

    /**
     * Initialize IndexedDB
     */
    async init() {
        if (this.isInitialized) return;

        return new Promise((resolve, reject) => {
            const request = indexedDB.open(DB_NAME, DB_VERSION);

            request.onerror = () => {
                console.error('IndexedDB failed to open');
                reject(request.error);
            };

            request.onsuccess = () => {
                this.db = request.result;
                this.isInitialized = true;
                console.log('IndexedDB initialized');
                resolve();
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;

                // Products store
                if (!db.objectStoreNames.contains(STORES.PRODUCTS)) {
                    const productStore = db.createObjectStore(STORES.PRODUCTS, {keyPath: 'id'});
                    productStore.createIndex('product_code', 'product_code', {unique: false});
                    productStore.createIndex('category', 'category', {unique: false});
                    productStore.createIndex('cached_at', 'cached_at', {unique: false});
                }

                // Searches store
                if (!db.objectStoreNames.contains(STORES.SEARCHES)) {
                    const searchStore = db.createObjectStore(STORES.SEARCHES, {keyPath: 'id', autoIncrement: true});
                    searchStore.createIndex('query', 'query', {unique: false});
                    searchStore.createIndex('timestamp', 'timestamp', {unique: false});
                }

                // Work orders store
                if (!db.objectStoreNames.contains(STORES.WORK_ORDERS)) {
                    const woStore = db.createObjectStore(STORES.WORK_ORDERS, {keyPath: 'wo_id'});
                    woStore.createIndex('status', 'status', {unique: false});
                    woStore.createIndex('due_date', 'due_date', {unique: false});
                }

                // Pending sync store
                if (!db.objectStoreNames.contains(STORES.PENDING_SYNC)) {
                    const syncStore = db.createObjectStore(STORES.PENDING_SYNC, {keyPath: 'id', autoIncrement: true});
                    syncStore.createIndex('type', 'type', {unique: false});
                    syncStore.createIndex('created_at', 'created_at', {unique: false});
                }

                // Cache metadata store
                if (!db.objectStoreNames.contains(STORES.CACHE_META)) {
                    db.createObjectStore(STORES.CACHE_META, {keyPath: 'key'});
                }

                console.log('IndexedDB stores created');
            };
        });
    }

    /**
     * Save products to offline storage
     */
    async saveProducts(products) {
        await this.init();

        const transaction = this.db.transaction([STORES.PRODUCTS], 'readwrite');
        const store = transaction.objectStore(STORES.PRODUCTS);

        const cached_at = new Date().toISOString();

        for (const product of products) {
            await store.put({
                ...product,
                cached_at,
            });
        }

        return transaction.complete;
    }

    /**
     * Get product by ID
     */
    async getProduct(productId) {
        await this.init();

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([STORES.PRODUCTS], 'readonly');
            const store = transaction.objectStore(STORES.PRODUCTS);
            const request = store.get(productId);

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Search products offline
     */
    async searchProducts(query, options = {}) {
        await this.init();

        const {
            category = null,
            limit = 20,
        } = options;

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([STORES.PRODUCTS], 'readonly');
            const store = transaction.objectStore(STORES.PRODUCTS);

            let request;
            if (category) {
                const index = store.index('category');
                request = index.getAll(category);
            } else {
                request = store.getAll();
            }

            request.onsuccess = () => {
                let results = request.result || [];

                // Text search filter
                if (query) {
                    const queryLower = query.toLowerCase();
                    results = results.filter(p =>
                        p.product_name?.toLowerCase().includes(queryLower) ||
                        p.product_code?.toLowerCase().includes(queryLower) ||
                        p.category?.toLowerCase().includes(queryLower)
                    );
                }

                // Limit results
                results = results.slice(0, limit);

                resolve(results);
            };

            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Save search history
     */
    async saveSearch(query, results) {
        await this.init();

        const transaction = this.db.transaction([STORES.SEARCHES], 'readwrite');
        const store = transaction.objectStore(STORES.SEARCHES);

        await store.add({
            query,
            results: results.slice(0, 10), // Store only top 10
            timestamp: new Date().toISOString(),
        });

        return transaction.complete;
    }

    /**
     * Get recent searches
     */
    async getRecentSearches(limit = 10) {
        await this.init();

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([STORES.SEARCHES], 'readonly');
            const store = transaction.objectStore(STORES.SEARCHES);
            const index = store.index('timestamp');
            const request = index.openCursor(null, 'prev'); // Descending order

            const results = [];
            request.onsuccess = (event) => {
                const cursor = event.target.result;
                if (cursor && results.length < limit) {
                    results.push(cursor.value);
                    cursor.continue();
                } else {
                    resolve(results);
                }
            };

            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Save work orders
     */
    async saveWorkOrders(workOrders) {
        await this.init();

        const transaction = this.db.transaction([STORES.WORK_ORDERS], 'readwrite');
        const store = transaction.objectStore(STORES.WORK_ORDERS);

        for (const wo of workOrders) {
            await store.put(wo);
        }

        return transaction.complete;
    }

    /**
     * Get work orders
     */
    async getWorkOrders(status = null) {
        await this.init();

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([STORES.WORK_ORDERS], 'readonly');
            const store = transaction.objectStore(STORES.WORK_ORDERS);

            let request;
            if (status) {
                const index = store.index('status');
                request = index.getAll(status);
            } else {
                request = store.getAll();
            }

            request.onsuccess = () => resolve(request.result || []);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Add pending sync item
     */
    async addPendingSync(type, data) {
        await this.init();

        const transaction = this.db.transaction([STORES.PENDING_SYNC], 'readwrite');
        const store = transaction.objectStore(STORES.PENDING_SYNC);

        const item = {
            type,
            data,
            created_at: new Date().toISOString(),
            retries: 0,
        };

        const request = store.add(item);

        return new Promise((resolve, reject) => {
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Get all pending sync items
     */
    async getPendingSync() {
        await this.init();

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([STORES.PENDING_SYNC], 'readonly');
            const store = transaction.objectStore(STORES.PENDING_SYNC);
            const request = store.getAll();

            request.onsuccess = () => resolve(request.result || []);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Remove synced item
     */
    async removePendingSync(id) {
        await this.init();

        const transaction = this.db.transaction([STORES.PENDING_SYNC], 'readwrite');
        const store = transaction.objectStore(STORES.PENDING_SYNC);

        return store.delete(id);
    }

    /**
     * Clear all data
     */
    async clearAll() {
        await this.init();

        const storeNames = Object.values(STORES);
        const transaction = this.db.transaction(storeNames, 'readwrite');

        for (const storeName of storeNames) {
            transaction.objectStore(storeName).clear();
        }

        return transaction.complete;
    }

    /**
     * Get cache metadata
     */
    async getCacheMeta(key) {
        await this.init();

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([STORES.CACHE_META], 'readonly');
            const store = transaction.objectStore(STORES.CACHE_META);
            const request = store.get(key);

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Set cache metadata
     */
    async setCacheMeta(key, value) {
        await this.init();

        const transaction = this.db.transaction([STORES.CACHE_META], 'readwrite');
        const store = transaction.objectStore(STORES.CACHE_META);

        await store.put({
            key,
            value,
            updated_at: new Date().toISOString(),
        });

        return transaction.complete;
    }

    /**
     * Get database statistics
     */
    async getStats() {
        await this.init();

        const stats = {};

        for (const storeName of Object.values(STORES)) {
            const count = await new Promise((resolve, reject) => {
                const transaction = this.db.transaction([storeName], 'readonly');
                const store = transaction.objectStore(storeName);
                const request = store.count();

                request.onsuccess = () => resolve(request.result);
                request.onerror = () => reject(request.error);
            });

            stats[storeName] = count;
        }

        return stats;
    }
}

// Singleton instance
const offlineStorage = new OfflineStorage();

// Export
window.offlineStorage = offlineStorage;
