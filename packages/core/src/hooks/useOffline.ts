/**
 * Offline Hook
 * Detect and handle offline state
 */

import { useEffect, useState, useCallback } from 'react'
import {
  isOnline,
  setupOfflineListeners,
  processQueue,
  queueOperation,
  type QueuedOperation,
} from '../utils/offline'
import { apiService } from '../services/api.service'

export interface UseOfflineOptions {
  onOnline?: () => void
  onOffline?: () => void
  autoSync?: boolean
}

export interface UseOfflineReturn {
  isOnline: boolean
  queueSize: number
  syncQueue: () => Promise<void>
}

/**
 * Hook for detecting and handling offline state
 *
 * @example
 * ```typescript
 * const { isOnline, queueSize, syncQueue } = useOffline({
 *   onOnline: () => console.log('Back online!'),
 *   onOffline: () => console.log('Gone offline'),
 *   autoSync: true,
 * })
 *
 * if (!isOnline) {
 *   return <OfflineBanner />
 * }
 * ```
 */
export function useOffline(options: UseOfflineOptions = {}): UseOfflineReturn {
  const { onOnline, onOffline, autoSync = true } = options

  const [online, setOnline] = useState(isOnline())
  const [queueSize, setQueueSize] = useState(0)

  const syncQueue = useCallback(async () => {
    if (!isOnline()) {
      console.log('Cannot sync while offline')
      return
    }

    await processQueue(async (operation: QueuedOperation) => {
      // Execute the queued operation
      const { endpoint, method, data } = operation

      switch (method.toUpperCase()) {
        case 'GET':
          await apiService.get(endpoint)
          break
        case 'POST':
          await apiService.post(endpoint, data)
          break
        case 'PUT':
          await apiService.put(endpoint, data)
          break
        case 'DELETE':
          await apiService.delete(endpoint)
          break
        default:
          throw new Error(`Unsupported method: ${method}`)
      }
    })

    // Update queue size after sync
    setQueueSize(0)
  }, [])

  useEffect(() => {
    const handleOnline = async () => {
      setOnline(true)
      onOnline?.()

      if (autoSync) {
        await syncQueue()
      }
    }

    const handleOffline = () => {
      setOnline(false)
      onOffline?.()
    }

    const cleanup = setupOfflineListeners(handleOnline, handleOffline)

    return cleanup
  }, [onOnline, onOffline, autoSync, syncQueue])

  return {
    isOnline: online,
    queueSize,
    syncQueue,
  }
}

/**
 * Hook for queueing operations when offline
 */
export function useOfflineQueue() {
  const { isOnline: online } = useOffline()

  const enqueue = useCallback(
    (type: string, endpoint: string, method: string, data: any) => {
      if (!online) {
        queueOperation(type, endpoint, method, data)
        return true
      }
      return false
    },
    [online]
  )

  return {
    isOnline: online,
    enqueue,
  }
}
