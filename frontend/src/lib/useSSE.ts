/**
 * React hook for Server-Sent Events (SSE) real-time updates
 */
import { useEffect, useRef, useCallback, useState } from 'react'
import { connectToEventStream } from './api'
import { useChecksStore } from './store'
import { useIncidentsStore } from './store'
import { useNotificationsStore } from './store'
import type { CheckResult, Incident, NotificationLog } from './types'

interface UseSSEOptions {
  enabled?: boolean
  onCheckResult?: (result: CheckResult) => void
  onIncidentOpened?: (incident: Incident) => void
  onIncidentResolved?: (incident: Incident) => void
  onNotificationSent?: (log: NotificationLog) => void
  onError?: (error: Event) => void
  onConnect?: () => void
  onDisconnect?: () => void
}

interface UseSSEReturn {
  isConnected: boolean
  error: Event | null
  reconnect: () => void
  disconnect: () => void
}

/**
 * Hook to connect to SSE stream and handle real-time updates
 */
export function useSSE(options: UseSSEOptions = {}): UseSSEReturn {
  const {
    enabled = true,
    onCheckResult,
    onIncidentOpened,
    onIncidentResolved,
    onNotificationSent,
    onError,
    onConnect,
    onDisconnect,
  } = options

  const eventSourceRef = useRef<EventSource | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<Event | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const maxReconnectAttempts = 5
  const baseReconnectDelay = 1000

  // Get store actions
  const addResult = useChecksStore((state) => state.addResult)
  const addIncident = useIncidentsStore((state) => state.addIncident)
  const updateIncident = useIncidentsStore((state) => state.updateIncident)
  const addLog = useNotificationsStore((state) => state.addLog)

  const connect = useCallback(() => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      console.warn('No access token found, skipping SSE connection')
      return
    }

    // Close existing connection if any
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
    }

    try {
      const eventSource = connectToEventStream({
        onOpen: () => {
          setIsConnected(true)
          setError(null)
          reconnectAttemptsRef.current = 0
          onConnect?.()
        },
        onError: (err) => {
          setIsConnected(false)
          setError(err)
          onError?.(err)
          onDisconnect?.()

          // Attempt to reconnect with exponential backoff
          if (reconnectAttemptsRef.current < maxReconnectAttempts) {
            const delay = baseReconnectDelay * Math.pow(2, reconnectAttemptsRef.current)
            reconnectAttemptsRef.current++
            reconnectTimeoutRef.current = setTimeout(() => {
              connect()
            }, delay)
          }
        },
        onCheckResult: (result) => {
          // Update store
          addResult(result.check_configuration_id, result)
          // Call custom handler
          onCheckResult?.(result)
        },
        onIncidentOpened: (incident) => {
          // Update store
          addIncident(incident)
          // Call custom handler
          onIncidentOpened?.(incident)
        },
        onIncidentResolved: (incident) => {
          // Update store
          updateIncident(incident)
          // Call custom handler
          onIncidentResolved?.(incident)
        },
        onNotificationSent: (log) => {
          // Update store
          addLog(log)
          // Call custom handler
          onNotificationSent?.(log)
        },
      })

      eventSourceRef.current = eventSource
    } catch (err) {
      console.error('Failed to connect to SSE:', err)
    }
  }, [
    addResult,
    addIncident,
    updateIncident,
    addLog,
    onCheckResult,
    onIncidentOpened,
    onIncidentResolved,
    onNotificationSent,
    onError,
    onConnect,
    onDisconnect,
  ])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }

    setIsConnected(false)
    onDisconnect?.()
  }, [onDisconnect])

  const reconnect = useCallback(() => {
    disconnect()
    reconnectAttemptsRef.current = 0
    connect()
  }, [connect, disconnect])

  // Connect on mount if enabled
  useEffect(() => {
    if (enabled) {
      connect()
    }

    return () => {
      disconnect()
    }
  }, [enabled, connect, disconnect])

  return {
    isConnected,
    error,
    reconnect,
    disconnect,
  }
}

/**
 * Hook to use SSE with automatic store updates
 * Simplified version that just connects and updates stores
 */
export function useRealtimeUpdates(enabled: boolean = true): UseSSEReturn {
  return useSSE({ enabled })
}

export default useSSE
