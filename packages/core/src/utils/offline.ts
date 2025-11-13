/**
 * Offline Support Utilities
 * Handle offline state and queue operations
 */

export interface QueuedOperation {
  id: string
  type: string
  endpoint: string
  method: string
  data: any
  timestamp: number
  retryCount: number
}

const QUEUE_STORAGE_KEY = 'rag_offline_queue'
const MAX_RETRIES = 3

/**
 * Check if browser is online
 */
export function isOnline(): boolean {
  return typeof navigator !== 'undefined' ? navigator.onLine : true
}

/**
 * Get queued offline operations
 */
export function getQueuedOperations(): QueuedOperation[] {
  if (typeof window === 'undefined') return []

  try {
    const queue = localStorage.getItem(QUEUE_STORAGE_KEY)
    return queue ? JSON.parse(queue) : []
  } catch (error) {
    console.error('Failed to get queued operations:', error)
    return []
  }
}

/**
 * Add operation to offline queue
 */
export function queueOperation(
  type: string,
  endpoint: string,
  method: string,
  data: any
): void {
  if (typeof window === 'undefined') return

  const operation: QueuedOperation = {
    id: `${Date.now()}_${Math.random()}`,
    type,
    endpoint,
    method,
    data,
    timestamp: Date.now(),
    retryCount: 0,
  }

  const queue = getQueuedOperations()
  queue.push(operation)

  try {
    localStorage.setItem(QUEUE_STORAGE_KEY, JSON.stringify(queue))
  } catch (error) {
    console.error('Failed to queue operation:', error)
  }
}

/**
 * Remove operation from queue
 */
export function removeQueuedOperation(id: string): void {
  if (typeof window === 'undefined') return

  const queue = getQueuedOperations().filter((op) => op.id !== id)

  try {
    localStorage.setItem(QUEUE_STORAGE_KEY, JSON.stringify(queue))
  } catch (error) {
    console.error('Failed to remove queued operation:', error)
  }
}

/**
 * Update operation retry count
 */
export function incrementRetryCount(id: string): void {
  if (typeof window === 'undefined') return

  const queue = getQueuedOperations().map((op) =>
    op.id === id ? { ...op, retryCount: op.retryCount + 1 } : op
  )

  try {
    localStorage.setItem(QUEUE_STORAGE_KEY, JSON.stringify(queue))
  } catch (error) {
    console.error('Failed to update retry count:', error)
  }
}

/**
 * Clear all queued operations
 */
export function clearQueue(): void {
  if (typeof window === 'undefined') return

  try {
    localStorage.removeItem(QUEUE_STORAGE_KEY)
  } catch (error) {
    console.error('Failed to clear queue:', error)
  }
}

/**
 * Process queued operations when online
 */
export async function processQueue(
  executor: (operation: QueuedOperation) => Promise<void>
): Promise<void> {
  if (!isOnline()) {
    console.log('Still offline, skipping queue processing')
    return
  }

  const queue = getQueuedOperations()

  for (const operation of queue) {
    if (operation.retryCount >= MAX_RETRIES) {
      console.warn('Max retries reached for operation:', operation.id)
      removeQueuedOperation(operation.id)
      continue
    }

    try {
      await executor(operation)
      removeQueuedOperation(operation.id)
    } catch (error) {
      console.error('Failed to process queued operation:', error)
      incrementRetryCount(operation.id)
    }
  }
}

/**
 * Setup online/offline event listeners
 */
export function setupOfflineListeners(
  onOnline: () => void,
  onOffline: () => void
): () => void {
  if (typeof window === 'undefined') {
    return () => {}
  }

  window.addEventListener('online', onOnline)
  window.addEventListener('offline', onOffline)

  return () => {
    window.removeEventListener('online', onOnline)
    window.removeEventListener('offline', onOffline)
  }
}

/**
 * Cache data for offline use
 */
export function cacheData<T>(key: string, data: T, ttl: number = 3600000): void {
  if (typeof window === 'undefined') return

  const cacheEntry = {
    data,
    timestamp: Date.now(),
    ttl,
  }

  try {
    localStorage.setItem(`cache_${key}`, JSON.stringify(cacheEntry))
  } catch (error) {
    console.error('Failed to cache data:', error)
  }
}

/**
 * Get cached data
 */
export function getCachedData<T>(key: string): T | null {
  if (typeof window === 'undefined') return null

  try {
    const cached = localStorage.getItem(`cache_${key}`)
    if (!cached) return null

    const { data, timestamp, ttl } = JSON.parse(cached)

    // Check if cache is still valid
    if (Date.now() - timestamp > ttl) {
      localStorage.removeItem(`cache_${key}`)
      return null
    }

    return data as T
  } catch (error) {
    console.error('Failed to get cached data:', error)
    return null
  }
}

/**
 * Clear cached data
 */
export function clearCache(key?: string): void {
  if (typeof window === 'undefined') return

  try {
    if (key) {
      localStorage.removeItem(`cache_${key}`)
    } else {
      // Clear all cache entries
      Object.keys(localStorage).forEach((k) => {
        if (k.startsWith('cache_')) {
          localStorage.removeItem(k)
        }
      })
    }
  } catch (error) {
    console.error('Failed to clear cache:', error)
  }
}
