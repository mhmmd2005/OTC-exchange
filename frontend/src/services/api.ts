import type { ApiEnvelope } from '@/types'

export type ApiErrorCode =
  | 'BAD_REQUEST'
  | 'UNAUTHENTICATED'
  | 'FORBIDDEN'
  | 'NOT_FOUND'
  | 'VALIDATION_ERROR'
  | 'NETWORK_ERROR'
  | 'SERVER_ERROR'
  | 'RATE_LIMITED'
  | 'QUOTE_EXPIRED'
  | 'PRICE_CHANGED'
  | 'INSUFFICIENT_TOMAN_BALANCE'
  | 'INSUFFICIENT_CRYPTO_BALANCE'
  | 'BELOW_MINIMUM'
  | 'ABOVE_MAXIMUM'
  | 'DAILY_LIMIT_EXCEEDED'
  | 'KYC_REQUIRED'
  | 'BANK_ACCOUNT_REQUIRED'
  | 'ASSET_DISABLED'
  | 'NETWORK_DISABLED'

export interface ApiErrorDetails {
  fields?: Record<string, string>
  actionLabel?: string
  actionRoute?: string
  [key: string]: unknown
}

export class ApiError extends Error {
  readonly code: ApiErrorCode
  readonly status: number
  readonly details?: ApiErrorDetails

  constructor(
    message: string,
    code: ApiErrorCode = 'SERVER_ERROR',
    status = 500,
    details?: ApiErrorDetails,
  ) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.status = status
    this.details = details
  }
}

export type QueryValue = string | number | boolean | null | undefined

export interface ApiRequestOptions extends Omit<RequestInit, 'body'> {
  body?: unknown
  query?: Record<string, QueryValue | QueryValue[]>
}

const configuredBaseUrl = String(import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')

// Demo data must be an explicit development-only choice. A missing or mistyped
// flag therefore fails closed and can never turn a production build into a
// fake, authentication-bypassing customer panel.
export const isMockApiEnabled = import.meta.env.DEV
  && import.meta.env.VITE_USE_MOCK_API === 'true'

function csrfToken(): string {
  if (typeof document === 'undefined') return ''
  const meta = document.querySelector<HTMLMetaElement>('meta[name="csrf-token"]')?.content
  if (meta) return meta
  const cookie = document.cookie.split('; ').find((item) => item.startsWith('XSRF-TOKEN='))
  return cookie ? decodeURIComponent(cookie.slice('XSRF-TOKEN='.length)) : ''
}

function announceUnauthorized(path: string): void {
  if (typeof window === 'undefined' || path.startsWith('/auth/') || path === '/users/me') return
  window.dispatchEvent(new CustomEvent('rosha:unauthorized', { detail: { path } }))
}

function buildUrl(path: string, query?: ApiRequestOptions['query']): string {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  const url = `${configuredBaseUrl}${normalizedPath}`
  if (!query) return url

  const search = new URLSearchParams()
  Object.entries(query).forEach(([key, rawValue]) => {
    const values = Array.isArray(rawValue) ? rawValue : [rawValue]
    values.forEach((value) => {
      if (value !== null && value !== undefined && value !== '') search.append(key, String(value))
    })
  })

  const queryString = search.toString()
  return queryString ? `${url}?${queryString}` : url
}

async function parseResponse<T>(response: Response): Promise<T> {
  const contentType = response.headers.get('content-type') ?? ''
  const isJson = contentType.includes('application/json')
  const payload: unknown = isJson
    ? await response.json()
    : await response.text()

  if (!response.ok) {
    const errorPayload = payload && typeof payload === 'object'
      ? payload as { message?: string; code?: ApiErrorCode; details?: ApiErrorDetails }
      : undefined
    throw new ApiError(
      errorPayload?.message ?? 'در ارتباط با سرور مشکلی پیش آمد. دوباره تلاش کنید.',
      errorPayload?.code ?? (response.status === 401 ? 'UNAUTHENTICATED' : 'SERVER_ERROR'),
      response.status,
      errorPayload?.details,
    )
  }

  // A misconfigured SPA host may answer unknown API paths with index.html and
  // status 200. Never type-cast that document into authenticated/financial
  // state: successful API responses must be JSON, except a genuinely empty
  // response such as HTTP 204.
  if (!isJson) {
    if (response.status === 204 || payload === '') return undefined as T
    throw new ApiError(
      'پاسخ نامعتبر از سرور دریافت شد. تنظیمات اتصال API را بررسی کنید.',
      'SERVER_ERROR',
      502,
    )
  }

  if (payload && typeof payload === 'object' && 'data' in payload) {
    return (payload as ApiEnvelope<T>).data
  }
  return payload as T
}

export async function request<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const headers = new Headers(options.headers)
  headers.set('Accept', 'application/json')
  if (options.body !== undefined && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }
  const method = String(options.method || 'GET').toUpperCase()
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) {
    const token = csrfToken()
    if (token) headers.set('X-CSRF-Token', token)
  }

  try {
    const response = await fetch(buildUrl(path, options.query), {
      ...options,
      // Authentication is intentionally delegated to Secure, HttpOnly,
      // SameSite cookies. Tokens are never read from browser storage.
      credentials: 'include',
      headers,
      body: options.body instanceof FormData
        ? options.body
        : options.body === undefined
          ? undefined
          : JSON.stringify(options.body),
    })
    return await parseResponse<T>(response)
  } catch (error) {
    if (error instanceof ApiError) {
      if (error.status === 401) announceUnauthorized(path)
      throw error
    }
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw error
    }
    throw new ApiError(
      'ارتباط اینترنت برقرار نیست. اتصال خود را بررسی و دوباره تلاش کنید.',
      'NETWORK_ERROR',
      0,
    )
  }
}

export const api = Object.freeze({
  get: <T>(path: string, options: Omit<ApiRequestOptions, 'method' | 'body'> = {}) =>
    request<T>(path, { ...options, method: 'GET' }),
  post: <T>(path: string, body?: unknown, options: Omit<ApiRequestOptions, 'method' | 'body'> = {}) =>
    request<T>(path, { ...options, method: 'POST', body }),
  put: <T>(path: string, body?: unknown, options: Omit<ApiRequestOptions, 'method' | 'body'> = {}) =>
    request<T>(path, { ...options, method: 'PUT', body }),
  patch: <T>(path: string, body?: unknown, options: Omit<ApiRequestOptions, 'method' | 'body'> = {}) =>
    request<T>(path, { ...options, method: 'PATCH', body }),
  delete: <T>(path: string, options: Omit<ApiRequestOptions, 'method' | 'body'> = {}) =>
    request<T>(path, { ...options, method: 'DELETE' }),
})

export interface MockResponseOptions {
  delay?: number
  signal?: AbortSignal
}

export function cloneMock<T>(value: T): T {
  if (value === undefined || value === null || typeof value !== 'object') return value
  return JSON.parse(JSON.stringify(value)) as T
}

export function mockResponse<T>(
  factory: (() => T | Promise<T>) | T,
  options: MockResponseOptions = {},
): Promise<T> {
  const delay = Math.max(0, options.delay ?? 180)

  return new Promise<T>((resolve, reject) => {
    if (options.signal?.aborted) {
      reject(new DOMException('The operation was aborted.', 'AbortError'))
      return
    }

    const timer = globalThis.setTimeout(async () => {
      try {
        const result = typeof factory === 'function'
          ? await (factory as () => T | Promise<T>)()
          : factory
        resolve(cloneMock(result))
      } catch (error) {
        reject(error)
      }
    }, delay)

    options.signal?.addEventListener('abort', () => {
      globalThis.clearTimeout(timer)
      reject(new DOMException('The operation was aborted.', 'AbortError'))
    }, { once: true })
  })
}

export function resolveApi<T>(mockFactory: () => T | Promise<T>, liveFactory: () => Promise<T>): Promise<T> {
  return isMockApiEnabled ? mockResponse(mockFactory) : liveFactory()
}
