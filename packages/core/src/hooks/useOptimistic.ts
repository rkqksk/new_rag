/**
 * Optimistic Updates Hook
 * Provides optimistic UI updates with automatic rollback on error
 */

import { useState, useCallback, useRef } from 'react'

export interface OptimisticUpdate<T> {
  id: string
  data: T
  timestamp: number
}

export interface UseOptimisticOptions<T> {
  onError?: (error: Error, rollbackData: T) => void
}

export interface UseOptimisticReturn<T> {
  data: T
  isPending: boolean
  mutate: (updateFn: (current: T) => T, asyncFn: () => Promise<T>) => Promise<T>
  rollback: () => void
}

/**
 * Hook for optimistic UI updates
 *
 * Immediately updates the UI with expected result, then applies actual result
 * when async operation completes. Automatically rolls back on error.
 *
 * @example
 * ```typescript
 * const { data, mutate } = useOptimistic(initialData)
 *
 * const handleUpdate = async () => {
 *   await mutate(
 *     (current) => ({ ...current, name: 'New Name' }),
 *     () => apiService.put('/user', { name: 'New Name' })
 *   )
 * }
 * ```
 */
export function useOptimistic<T>(
  initialData: T,
  options: UseOptimisticOptions<T> = {}
): UseOptimisticReturn<T> {
  const { onError } = options

  const [data, setData] = useState<T>(initialData)
  const [isPending, setIsPending] = useState(false)
  const previousDataRef = useRef<T>(initialData)
  const pendingUpdatesRef = useRef<Set<string>>(new Set())

  const rollback = useCallback(() => {
    setData(previousDataRef.current)
    pendingUpdatesRef.current.clear()
    setIsPending(false)
  }, [])

  const mutate = useCallback(
    async (updateFn: (current: T) => T, asyncFn: () => Promise<T>): Promise<T> => {
      // Save current state for potential rollback
      previousDataRef.current = data

      // Generate unique update ID
      const updateId = `${Date.now()}_${Math.random()}`
      pendingUpdatesRef.current.add(updateId)
      setIsPending(true)

      // Apply optimistic update immediately
      const optimisticData = updateFn(data)
      setData(optimisticData)

      try {
        // Execute async operation
        const result = await asyncFn()

        // Apply actual result
        pendingUpdatesRef.current.delete(updateId)
        if (pendingUpdatesRef.current.size === 0) {
          setIsPending(false)
        }
        setData(result)
        previousDataRef.current = result

        return result
      } catch (error) {
        // Rollback on error
        pendingUpdatesRef.current.delete(updateId)
        if (pendingUpdatesRef.current.size === 0) {
          setIsPending(false)
        }
        setData(previousDataRef.current)
        onError?.(error as Error, previousDataRef.current)
        throw error
      }
    },
    [data, onError]
  )

  return {
    data,
    isPending,
    mutate,
    rollback,
  }
}

/**
 * Hook for optimistic list updates (add, remove, update items)
 */
export function useOptimisticList<T extends { id: string }>(
  initialData: T[],
  options: UseOptimisticOptions<T[]> = {}
) {
  const { data, mutate, isPending, rollback } = useOptimistic(initialData, options)

  const addItem = useCallback(
    async (item: T, asyncFn: () => Promise<T>) => {
      return mutate(
        (current) => [...current, item],
        async () => {
          const result = await asyncFn()
          return data.map((i) => (i.id === item.id ? result : i)).concat(result)
        }
      )
    },
    [mutate, data]
  )

  const removeItem = useCallback(
    async (id: string, asyncFn: () => Promise<void>) => {
      return mutate(
        (current) => current.filter((item) => item.id !== id),
        async () => {
          await asyncFn()
          return data.filter((item) => item.id !== id)
        }
      )
    },
    [mutate, data]
  )

  const updateItem = useCallback(
    async (id: string, updates: Partial<T>, asyncFn: () => Promise<T>) => {
      return mutate(
        (current) =>
          current.map((item) => (item.id === id ? { ...item, ...updates } : item)),
        async () => {
          const result = await asyncFn()
          return data.map((item) => (item.id === id ? result : item))
        }
      )
    },
    [mutate, data]
  )

  return {
    data,
    isPending,
    rollback,
    addItem,
    removeItem,
    updateItem,
  }
}
