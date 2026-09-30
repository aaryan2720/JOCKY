import { useEffect, useRef, useState, useCallback } from 'react'
import { WS_BASE_URL } from '../api/client'
import { WebSocketMessage } from '../types'

export type ConnectionStatus = 'idle' | 'connecting' | 'connected' | 'disconnected' | 'error'

interface UseJobWebSocketOptions {
  onMessage?: (message: WebSocketMessage) => void
  enabled?: boolean
}

export function useJobWebSocket(jobId?: string, options: UseJobWebSocketOptions = {}) {
  const { onMessage, enabled = true } = options
  const [status, setStatus] = useState<ConnectionStatus>('idle')
  const [events, setEvents] = useState<WebSocketMessage[]>([])
  const wsRef = useRef<WebSocket | null>(null)
  const pingIntervalRef = useRef<number | null>(null)

  const clearPing = () => {
    if (pingIntervalRef.current) {
      window.clearInterval(pingIntervalRef.current)
      pingIntervalRef.current = null
    }
  }

  const connect = useCallback(() => {
    if (!jobId || !enabled) return

    // Clean up any existing connection
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    clearPing()

    setStatus('connecting')
    const wsUrl = `${WS_BASE_URL}/ws/jobs/${encodeURIComponent(jobId)}`

    try {
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        setStatus('connected')
        // Ping every 25 seconds for keep-alive
        pingIntervalRef.current = window.setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send('ping')
          }
        }, 25000)
      }

      ws.onmessage = (event) => {
        if (event.data === 'pong') return

        try {
          const parsed: WebSocketMessage = JSON.parse(event.data)
          setEvents((prev) => [parsed, ...prev.slice(0, 99)])
          if (onMessage) {
            onMessage(parsed)
          }
        } catch {
          // If not JSON, ignore malformed payload
        }
      }

      ws.onerror = () => {
        setStatus('error')
      }

      ws.onclose = () => {
        setStatus('disconnected')
        clearPing()
      }
    } catch {
      setStatus('error')
    }
  }, [jobId, enabled, onMessage])

  useEffect(() => {
    connect()

    return () => {
      clearPing()
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
      setStatus('idle')
    }
  }, [connect])

  const clearEvents = useCallback(() => {
    setEvents([])
  }, [])

  return {
    status,
    events,
    clearEvents,
    reconnect: connect,
  }
}
