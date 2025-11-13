/**
 * Real-time Updates Hook
 * WebSocket connection for live data updates
 */

import { useEffect, useRef, useState, useCallback } from 'react'
import { API_CONFIG } from '../config/api.config'

export interface RealtimeMessage<T = any> {
  type: string
  data: T
  timestamp: string
}

export interface UseRealtimeOptions {
  url?: string
  autoConnect?: boolean
  reconnectInterval?: number
  maxReconnectAttempts?: number
  onMessage?: (message: RealtimeMessage) => void
  onConnect?: () => void
  onDisconnect?: () => void
  onError?: (error: Event) => void
}

export interface UseRealtimeReturn {
  isConnected: boolean
  send: (type: string, data: any) => void
  subscribe: (type: string, callback: (data: any) => void) => () => void
  connect: () => void
  disconnect: () => void
}

/**
 * Hook for real-time WebSocket connections
 *
 * @example
 * ```typescript
 * const { isConnected, subscribe } = useRealtime({
 *   onConnect: () => console.log('Connected'),
 *   onDisconnect: () => console.log('Disconnected'),
 * })
 *
 * useEffect(() => {
 *   const unsubscribe = subscribe('search:update', (data) => {
 *     console.log('New search result:', data)
 *   })
 *   return unsubscribe
 * }, [subscribe])
 * ```
 */
export function useRealtime(options: UseRealtimeOptions = {}): UseRealtimeReturn {
  const {
    url = `${API_CONFIG.BASE_URL.replace('http', 'ws')}/ws`,
    autoConnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
    onMessage,
    onConnect,
    onDisconnect,
    onError,
  } = options

  const [isConnected, setIsConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>()
  const subscribersRef = useRef<Map<string, Set<(data: any) => void>>>(new Map())

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    try {
      const token = localStorage.getItem(API_CONFIG.AUTH.TOKEN_KEY)
      const wsUrl = token ? `${url}?token=${token}` : url

      wsRef.current = new WebSocket(wsUrl)

      wsRef.current.onopen = () => {
        setIsConnected(true)
        reconnectAttemptsRef.current = 0
        onConnect?.()
      }

      wsRef.current.onclose = () => {
        setIsConnected(false)
        onDisconnect?.()

        // Auto-reconnect
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++
          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, reconnectInterval)
        }
      }

      wsRef.current.onerror = (error) => {
        onError?.(error)
      }

      wsRef.current.onmessage = (event) => {
        try {
          const message: RealtimeMessage = JSON.parse(event.data)
          onMessage?.(message)

          // Notify subscribers
          const subscribers = subscribersRef.current.get(message.type)
          if (subscribers) {
            subscribers.forEach((callback) => callback(message.data))
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
    }
  }, [url, maxReconnectAttempts, reconnectInterval, onConnect, onDisconnect, onError, onMessage])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    wsRef.current?.close()
    wsRef.current = null
    setIsConnected(false)
  }, [])

  const send = useCallback((type: string, data: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type,
          data,
          timestamp: new Date().toISOString(),
        })
      )
    } else {
      console.warn('WebSocket is not connected')
    }
  }, [])

  const subscribe = useCallback((type: string, callback: (data: any) => void) => {
    if (!subscribersRef.current.has(type)) {
      subscribersRef.current.set(type, new Set())
    }
    subscribersRef.current.get(type)!.add(callback)

    // Return unsubscribe function
    return () => {
      subscribersRef.current.get(type)?.delete(callback)
    }
  }, [])

  useEffect(() => {
    if (autoConnect) {
      connect()
    }

    return () => {
      disconnect()
    }
  }, [autoConnect, connect, disconnect])

  return {
    isConnected,
    send,
    subscribe,
    connect,
    disconnect,
  }
}
