import type {ApiEnvelope} from '@/types'

export type ApiErrorCode =
    | 'BAD_REQUEST'
    | 'UNAUTHENTICATED'
    | 'FORBIDDEN'
    | 'NOT_FOUND'
    | 'VALIDATION_ERROR'
    | 'NETWORK_ERROR'
    | 'SERVER_ERROR'
    | 'RATE_LIMITED'
    | 'NOT_IMPLEMENTED'
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

const ACCESS_TOKEN_KEY = 'rosha_access_token'
const REFRESH_TOKEN_KEY = 'rosha_refresh_token'

const apiErrorCodes: ApiErrorCode[] = [
    'BAD_REQUEST',
    'UNAUTHENTICATED',
    'FORBIDDEN',
    'NOT_FOUND',
    'VALIDATION_ERROR',
    'NETWORK_ERROR',
    'SERVER_ERROR',
    'RATE_LIMITED',
    'NOT_IMPLEMENTED',
    'QUOTE_EXPIRED',
    'PRICE_CHANGED',
    'INSUFFICIENT_TOMAN_BALANCE',
    'INSUFFICIENT_CRYPTO_BALANCE',
    'BELOW_MINIMUM',
    'ABOVE_MAXIMUM',
    'DAILY_LIMIT_EXCEEDED',
    'KYC_REQUIRED',
    'BANK_ACCOUNT_REQUIRED',
    'ASSET_DISABLED',
    'NETWORK_DISABLED',
]

export const isMockApiEnabled = import.meta.env.DEV
    && import.meta.env.VITE_USE_MOCK_API === 'true'

function sessionStorageAvailable(): boolean {
    return typeof window !== 'undefined' && Boolean(window.sessionStorage)
}

function localStorageAvailable(): boolean {
    return typeof window !== 'undefined' && Boolean(window.localStorage)
}

export function getAccessToken(): string | null {
    if (sessionStorageAvailable()) {
        const token = window.sessionStorage.getItem(ACCESS_TOKEN_KEY)
        if (token) return token
    }

    if (localStorageAvailable()) {
        return window.localStorage.getItem(ACCESS_TOKEN_KEY)
    }

    return null
}

export function getRefreshToken(): string | null {
    if (sessionStorageAvailable()) {
        const token = window.sessionStorage.getItem(REFRESH_TOKEN_KEY)
        if (token) return token
    }

    if (localStorageAvailable()) {
        return window.localStorage.getItem(REFRESH_TOKEN_KEY)
    }

    return null
}

export function setAuthTokens(
    accessToken: string,
    refreshToken: string,
    remember = true,
): void {
    clearAuthTokens()

    if (typeof window === 'undefined') return

    const storage = remember ? window.localStorage : window.sessionStorage
    storage.setItem(ACCESS_TOKEN_KEY, accessToken)
    storage.setItem(REFRESH_TOKEN_KEY, refreshToken)
}

export function clearAuthTokens(): void {
    if (sessionStorageAvailable()) {
        window.sessionStorage.removeItem(ACCESS_TOKEN_KEY)
        window.sessionStorage.removeItem(REFRESH_TOKEN_KEY)
    }

    if (localStorageAvailable()) {
        window.localStorage.removeItem(ACCESS_TOKEN_KEY)
        window.localStorage.removeItem(REFRESH_TOKEN_KEY)
    }
}

function persistRefreshedAccessToken(accessToken: string): void {
    if (typeof window === 'undefined') return

    if (window.sessionStorage.getItem(REFRESH_TOKEN_KEY)) {
        window.sessionStorage.setItem(ACCESS_TOKEN_KEY, accessToken)
        return
    }

    if (window.localStorage.getItem(REFRESH_TOKEN_KEY)) {
        window.localStorage.setItem(ACCESS_TOKEN_KEY, accessToken)
    }
}

function csrfToken(): string {
    if (typeof document === 'undefined') return ''
    const meta = document.querySelector<HTMLMetaElement>('meta[name="csrf-token"]')?.content
    if (meta) return meta

    const cookie = document.cookie
        .split('; ')
        .find((item) => item.startsWith('XSRF-TOKEN='))

    return cookie
        ? decodeURIComponent(cookie.slice('XSRF-TOKEN='.length))
        : ''
}

function announceUnauthorized(path: string): void {
    if (
        typeof window === 'undefined'
        || path.startsWith('/auth/')
        && path !== '/auth/me/'
    ) {
        return
    }

    window.dispatchEvent(
        new CustomEvent('rosha:unauthorized', {
            detail: {path},
        }),
    )
}

function buildUrl(
    path: string,
    query?: ApiRequestOptions['query'],
): string {
    const normalizedPath = path.startsWith('/')
        ? path
        : `/${path}`

    const url = `${configuredBaseUrl}${normalizedPath}`

    if (!query) return url

    const search = new URLSearchParams()

    Object.entries(query).forEach(([key, rawValue]) => {
        const values = Array.isArray(rawValue)
            ? rawValue
            : [rawValue]

        values.forEach((value) => {
            if (
                value !== null
                && value !== undefined
                && value !== ''
            ) {
                search.append(key, String(value))
            }
        })
    })

    const queryString = search.toString()

    return queryString
        ? `${url}?${queryString}`
        : url
}

function errorCodeFromStatus(status: number): ApiErrorCode {
    if (status === 400 || status === 422) return 'VALIDATION_ERROR'
    if (status === 401) return 'UNAUTHENTICATED'
    if (status === 403) return 'FORBIDDEN'
    if (status === 404) return 'NOT_FOUND'
    if (status === 429) return 'RATE_LIMITED'
    if (status === 501) return 'NOT_IMPLEMENTED'
    if (status >= 500) return 'SERVER_ERROR'
    return 'BAD_REQUEST'
}

function isApiErrorCode(value: unknown): value is ApiErrorCode {
    return typeof value === 'string'
        && apiErrorCodes.includes(value as ApiErrorCode)
}

function extractErrorMessage(payload: unknown): string {
    if (!payload || typeof payload !== 'object') {
        return 'در ارتباط با سرور مشکلی پیش آمد. دوباره تلاش کنید.'
    }

    const data = payload as Record<string, unknown>

    if (typeof data.message === 'string' && data.message.trim()) {
        return data.message
    }

    if (typeof data.detail === 'string' && data.detail.trim()) {
        return data.detail
    }

    for (const [key, value] of Object.entries(data)) {
        if (key === 'code' || key === 'details') continue

        if (typeof value === 'string' && value.trim()) {
            return value
        }

        if (
            Array.isArray(value)
            && typeof value[0] === 'string'
            && value[0].trim()
        ) {
            return value[0]
        }
    }

    return 'در ارتباط با سرور مشکلی پیش آمد. دوباره تلاش کنید.'
}

function extractErrorDetails(payload: unknown): ApiErrorDetails | undefined {
    if (!payload || typeof payload !== 'object') return undefined

    const data = payload as Record<string, unknown>

    if (
        data.details
        && typeof data.details === 'object'
        && !Array.isArray(data.details)
    ) {
        return data.details as ApiErrorDetails
    }

    const fields: Record<string, string> = {}

    Object.entries(data).forEach(([key, value]) => {
        if (key === 'message' || key === 'detail' || key === 'code') return

        if (typeof value === 'string') {
            fields[key] = value
            return
        }

        if (
            Array.isArray(value)
            && typeof value[0] === 'string'
        ) {
            fields[key] = value[0]
        }
    })

    return Object.keys(fields).length
        ? {fields}
        : undefined
}

async function parseResponse<T>(response: Response): Promise<T> {
    const contentType = response.headers.get('content-type') ?? ''
    const isJson = contentType.includes('application/json')

    const payload: unknown = isJson
        ? await response.json()
        : await response.text()

    if (!response.ok) {
        const backendCode =
            payload
            && typeof payload === 'object'
            && !Array.isArray(payload)
                ? (payload as Record<string, unknown>).code
                : undefined

        throw new ApiError(
            extractErrorMessage(payload),
            isApiErrorCode(backendCode)
                ? backendCode
                : errorCodeFromStatus(response.status),
            response.status,
            extractErrorDetails(payload),
        )
    }

    if (!isJson) {
        if (response.status === 204 || payload === '') {
            return undefined as T
        }

        throw new ApiError(
            'پاسخ نامعتبر از سرور دریافت شد. تنظیمات اتصال API را بررسی کنید.',
            'SERVER_ERROR',
            502,
        )
    }

    if (
        payload
        && typeof payload === 'object'
        && 'data' in payload
    ) {
        return (payload as ApiEnvelope<T>).data
    }

    return payload as T
}

async function refreshAccessToken(): Promise<boolean> {
    const refreshToken = getRefreshToken()

    if (!refreshToken) return false

    try {
        const response = await fetch(
            buildUrl('/auth/refresh/'),
            {
                method: 'POST',
                headers: {
                    Accept: 'application/json',
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify({
                    refresh: refreshToken,
                }),
            },
        )

        const result = await parseResponse<{ access?: string }>(response)

        if (!result?.access) {
            throw new ApiError(
                'توکن دسترسی جدید دریافت نشد.',
                'UNAUTHENTICATED',
                401,
            )
        }

        persistRefreshedAccessToken(result.access)

        return true
    } catch {
        clearAuthTokens()
        return false
    }
}

function shouldRefreshOn401(path: string): boolean {
    return path === '/auth/me/' || !path.startsWith('/auth/')
}

export async function request<T>(
    path: string,
    options: ApiRequestOptions = {},
    allowRefresh = true,
): Promise<T> {
    const headers = new Headers(options.headers)

    headers.set('Accept', 'application/json')

    if (
        options.body !== undefined
        && !(options.body instanceof FormData)
    ) {
        headers.set('Content-Type', 'application/json')
    }

    const accessToken = getAccessToken()

    if (accessToken) {
        headers.set(
            'Authorization',
            `Bearer ${accessToken}`,
        )
    }

    const method = String(
        options.method || 'GET',
    ).toUpperCase()

    if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) {
        const token = csrfToken()

        if (token) {
            headers.set('X-CSRF-Token', token)
        }
    }

    try {
        const response = await fetch(
            buildUrl(path, options.query),
            {
                ...options,
                credentials: 'include',
                headers,
                body: options.body instanceof FormData
                    ? options.body
                    : options.body === undefined
                        ? undefined
                        : JSON.stringify(options.body),
            },
        )

        if (
            response.status === 401
            && allowRefresh
            && shouldRefreshOn401(path)
            && getRefreshToken()
        ) {
            const refreshed = await refreshAccessToken()

            if (refreshed) {
                return request<T>(
                    path,
                    options,
                    false,
                )
            }
        }

        return await parseResponse<T>(response)
    } catch (error) {
        if (error instanceof ApiError) {
            if (error.status === 401) {
                announceUnauthorized(path)
            }

            throw error
        }

        if (
            error instanceof DOMException
            && error.name === 'AbortError'
        ) {
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
    get: <T>(
        path: string,
        options: Omit<ApiRequestOptions, 'method' | 'body'> = {},
    ) =>
        request<T>(
            path,
            {
                ...options,
                method: 'GET',
            },
        ),

    post: <T>(
        path: string,
        body?: unknown,
        options: Omit<ApiRequestOptions, 'method' | 'body'> = {},
    ) =>
        request<T>(
            path,
            {
                ...options,
                method: 'POST',
                body,
            },
        ),

    put: <T>(
        path: string,
        body?: unknown,
        options: Omit<ApiRequestOptions, 'method' | 'body'> = {},
    ) =>
        request<T>(
            path,
            {
                ...options,
                method: 'PUT',
                body,
            },
        ),

    patch: <T>(
        path: string,
        body?: unknown,
        options: Omit<ApiRequestOptions, 'method' | 'body'> = {},
    ) =>
        request<T>(
            path,
            {
                ...options,
                method: 'PATCH',
                body,
            },
        ),

    delete: <T>(
        path: string,
        options: Omit<ApiRequestOptions, 'method' | 'body'> = {},
    ) =>
        request<T>(
            path,
            {
                ...options,
                method: 'DELETE',
            },
        ),
})

export interface MockResponseOptions {
    delay?: number
    signal?: AbortSignal
}

export function cloneMock<T>(value: T): T {
    if (
        value === undefined
        || value === null
        || typeof value !== 'object'
    ) {
        return value
    }

    return JSON.parse(JSON.stringify(value)) as T
}

export function mockResponse<T>(
    factory: (() => T | Promise<T>) | T,
    options: MockResponseOptions = {},
): Promise<T> {
    const delay = Math.max(
        0,
        options.delay ?? 180,
    )

    return new Promise<T>((resolve, reject) => {
        if (options.signal?.aborted) {
            reject(
                new DOMException(
                    'The operation was aborted.',
                    'AbortError',
                ),
            )
            return
        }

        const timer = globalThis.setTimeout(
            async () => {
                try {
                    const result =
                        typeof factory === 'function'
                            ? await (
                                factory as
                                    () => T | Promise<T>
                            )()
                            : factory

                    resolve(cloneMock(result))
                } catch (error) {
                    reject(error)
                }
            },
            delay,
        )

        options.signal?.addEventListener(
            'abort',
            () => {
                globalThis.clearTimeout(timer)
                reject(
                    new DOMException(
                        'The operation was aborted.',
                        'AbortError',
                    ),
                )
            },
            {once: true},
        )
    })
}

export function resolveApi<T>(
    mockFactory: () => T | Promise<T>,
    liveFactory: () => Promise<T>,
): Promise<T> {
    return isMockApiEnabled
        ? mockResponse(mockFactory)
        : liveFactory()
}