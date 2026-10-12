import { api, isMockApiEnabled } from '@/services/api'
import { adminApi } from '@/services/admin/adminApi'

export type SupportRealtimeState = 'connecting' | 'connected' | 'disconnected'

export interface SupportRealtimeMessage {
  id: number | string
  sender: 'user' | 'support'
  senderName: string
  body: string
  createdAt: string
}

export interface SupportRealtimeEvent {
  type: 'message.created'
  ticketId: number
  message: SupportRealtimeMessage
  ticket: {
    adminStatus: string
    userStatus: string
    updatedAt: string
    messageCount: number
  }
}

interface WsTicketResponse {
  ticket: string
  expiresIn: number
}

interface RealtimeOptions {
  ticketId: number | string
  getTicket: () => Promise<string>
  onMessage: (event: SupportRealtimeEvent) => void
  onState?: (state: SupportRealtimeState) => void
}

function buildWebSocketUrl(ticketId: number | string, ticket: string): string {
  const configuredBaseUrl = String(import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')
  const pageOrigin = typeof window !== 'undefined' ? window.location.origin : 'http://localhost'
  const apiBase = new URL(configuredBaseUrl || pageOrigin, pageOrigin)
  const protocol = apiBase.protocol === 'https:' ? 'wss:' : 'ws:'
  const url = new URL(
    `/ws/support/tickets/${encodeURIComponent(String(ticketId))}/`,
    `${protocol}//${apiBase.host}`,
  )
  // This is a short-lived, one-time ticket, not the primary JWT.
  url.searchParams.set('ticket', ticket)
  return url.toString()
}

function connectRealtime(options: RealtimeOptions): () => void {
  let stopped = false
  let socket: WebSocket | null = null
  let reconnectTimer: number | undefined
  let heartbeatTimer: number | undefined
  let reconnectAttempts = 0

  const setState = (state: SupportRealtimeState) => options.onState?.(state)

  function clearHeartbeat(): void {
    if (heartbeatTimer !== undefined) {
      window.clearInterval(heartbeatTimer)
      heartbeatTimer = undefined
    }
  }

  function scheduleReconnect(): void {
    if (stopped || reconnectTimer !== undefined) return
    const delay = Math.min(1000 * 2 ** Math.min(reconnectAttempts, 5), 30000)
    reconnectAttempts += 1
    reconnectTimer = window.setTimeout(() => {
      reconnectTimer = undefined
      void connect()
    }, delay)
  }

  async function connect(): Promise<void> {
    if (stopped) return
    setState('connecting')

    let ticket: string
    try {
      ticket = await options.getTicket()
      if (!ticket || stopped) return
    } catch {
      if (stopped) return
      setState('disconnected')
      scheduleReconnect()
      return
    }

    if (stopped) return

    let candidate: WebSocket
    try {
      candidate = new WebSocket(buildWebSocketUrl(options.ticketId, ticket))
    } catch {
      setState('disconnected')
      scheduleReconnect()
      return
    }

    socket = candidate

    candidate.addEventListener('open', () => {
      if (stopped || socket !== candidate) {
        candidate.close()
        return
      }
      reconnectAttempts = 0
      setState('connected')
      clearHeartbeat()
      heartbeatTimer = window.setInterval(() => {
        if (socket === candidate && candidate.readyState === WebSocket.OPEN) {
          candidate.send(JSON.stringify({ type: 'ping' }))
        }
      }, 25000)
    })

    candidate.addEventListener('message', (rawEvent: MessageEvent) => {
      if (stopped || socket !== candidate) return
      let payload: unknown
      try {
        payload = JSON.parse(String(rawEvent.data))
      } catch {
        return
      }
      if (!payload || typeof payload !== 'object') return
      const data = payload as Record<string, unknown>
      if (
        data.type !== 'message.created'
        || Number(data.ticketId) !== Number(options.ticketId)
        || !data.message || typeof data.message !== 'object'
        || !data.ticket || typeof data.ticket !== 'object'
      ) return
      options.onMessage(data as unknown as SupportRealtimeEvent)
    })

    candidate.addEventListener('error', () => {
      if (candidate.readyState !== WebSocket.CLOSED) candidate.close()
    })

    candidate.addEventListener('close', () => {
      if (socket === candidate) socket = null
      clearHeartbeat()
      if (stopped) return
      setState('disconnected')
      scheduleReconnect()
    })
  }

  void connect()

  return () => {
    stopped = true
    if (reconnectTimer !== undefined) {
      window.clearTimeout(reconnectTimer)
      reconnectTimer = undefined
    }
    clearHeartbeat()
    const current = socket
    socket = null
    if (
      current
      && (current.readyState === WebSocket.OPEN || current.readyState === WebSocket.CONNECTING)
    ) {
      current.close(1000, 'Client disposed')
    }
    setState('disconnected')
  }
}

export function connectUserSupportTicketRealtime(
  ticketId: string | number,
  handlers: {
    onMessage: (event: SupportRealtimeEvent) => void
    onState?: (state: SupportRealtimeState) => void
  },
): () => void {
  if (isMockApiEnabled) {
    handlers.onState?.('disconnected')
    return () => undefined
  }

  return connectRealtime({
    ticketId,
    onMessage: handlers.onMessage,
    onState: handlers.onState,
    getTicket: async () => {
      const result = await api.post<WsTicketResponse>(
        `/support/tickets/${encodeURIComponent(String(ticketId))}/ws-ticket`,
      )
      return result.ticket
    },
  })
}

export function connectAdminSupportTicketRealtime(
  ticketId: number,
  handlers: {
    onMessage: (event: SupportRealtimeEvent) => void
    onState?: (state: SupportRealtimeState) => void
  },
): () => void {
  return connectRealtime({
    ticketId,
    onMessage: handlers.onMessage,
    onState: handlers.onState,
    getTicket: async () => {
      const result = await adminApi.post<WsTicketResponse>(
        `/admin/support/tickets/${ticketId}/ws-ticket/`,
      )
      return result.ticket
    },
  })
}
