import {
    ApiError,
    type ApiErrorCode,
    type ApiErrorDetails,
} from '@/services/api'

const configuredBaseUrl =
    String(
        import.meta.env.VITE_API_BASE_URL ?? '',
    ).replace(/\/$/, '')

const ADMIN_ACCESS_TOKEN_KEY =
    'rosha_admin_access_token'

const ADMIN_REFRESH_TOKEN_KEY =
    'rosha_admin_refresh_token'

interface AdminRequestOptions
    extends Omit<RequestInit, 'body'> {
    body?: unknown
}

function buildUrl(path: string): string {
    const normalizedPath = path.startsWith('/')
        ? path
        : `/${path}`

    return `${configuredBaseUrl}${normalizedPath}`
}

function getAdminAccessToken(): string | null {
    if (
        typeof window === 'undefined'
        || !window.sessionStorage
    ) {
        return null
    }

    return window.sessionStorage.getItem(
        ADMIN_ACCESS_TOKEN_KEY,
    )
}

function getAdminRefreshToken(): string | null {
    if (
        typeof window === 'undefined'
        || !window.sessionStorage
    ) {
        return null
    }

    return window.sessionStorage.getItem(
        ADMIN_REFRESH_TOKEN_KEY,
    )
}

function setAdminTokens(
    accessToken: string,
    refreshToken: string,
): void {
    if (typeof window === 'undefined') return

    window.sessionStorage.setItem(
        ADMIN_ACCESS_TOKEN_KEY,
        accessToken,
    )

    window.sessionStorage.setItem(
        ADMIN_REFRESH_TOKEN_KEY,
        refreshToken,
    )
}

function setAdminAccessToken(
    accessToken: string,
): void {
    if (typeof window === 'undefined') return

    window.sessionStorage.setItem(
        ADMIN_ACCESS_TOKEN_KEY,
        accessToken,
    )
}

function clearAdminTokens(): void {
    if (typeof window === 'undefined') return

    window.sessionStorage.removeItem(
        ADMIN_ACCESS_TOKEN_KEY,
    )

    window.sessionStorage.removeItem(
        ADMIN_REFRESH_TOKEN_KEY,
    )
}

export function getAdminRefreshTokenValue():
    string | null {
    return getAdminRefreshToken()
}

export function clearAdminAuthTokens(): void {
    clearAdminTokens()
}

function errorCodeFromStatus(
    status: number,
): ApiErrorCode {
    if (status === 400 || status === 422) {
        return 'VALIDATION_ERROR'
    }

    if (status === 401) {
        return 'UNAUTHENTICATED'
    }

    if (status === 403) {
        return 'FORBIDDEN'
    }

    if (status === 404) {
        return 'NOT_FOUND'
    }

    if (status === 429) {
        return 'RATE_LIMITED'
    }

    if (status === 501) {
        return 'NOT_IMPLEMENTED'
    }

    if (status >= 500) {
        return 'SERVER_ERROR'
    }

    return 'BAD_REQUEST'
}

function extractErrorMessage(
    payload: unknown,
): string {
    if (
        !payload
        || typeof payload !== 'object'
    ) {
        return 'در ارتباط با سرور مشکلی پیش آمد. دوباره تلاش کنید.'
    }

    const data =
        payload as Record<string, unknown>

    if (
        typeof data.message === 'string'
        && data.message.trim()
    ) {
        return data.message
    }

    if (
        typeof data.detail === 'string'
        && data.detail.trim()
    ) {
        return data.detail
    }

    for (
        const [key, value]
        of Object.entries(data)
    ) {
        if (
            key === 'code'
            || key === 'details'
        ) {
            continue
        }

        if (
            typeof value === 'string'
            && value.trim()
        ) {
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

function extractErrorDetails(
    payload: unknown,
): ApiErrorDetails | undefined {
    if (
        !payload
        || typeof payload !== 'object'
        || Array.isArray(payload)
    ) {
        return undefined
    }

    const data =
        payload as Record<string, unknown>

    if (
        data.details
        && typeof data.details === 'object'
        && !Array.isArray(data.details)
    ) {
        return data.details as ApiErrorDetails
    }

    return undefined
}

async function parseResponse<T>(
    response: Response,
): Promise<T> {
    const contentType =
        response.headers.get(
            'content-type',
        ) ?? ''

    const isJson =
        contentType.includes(
            'application/json',
        )

    const payload: unknown = isJson
        ? await response.json()
        : await response.text()

    if (!response.ok) {
        const backendCode =
            payload
            && typeof payload === 'object'
            && !Array.isArray(payload)
                ? (
                    payload as Record<
                        string,
                        unknown
                    >
                ).code
                : undefined

        throw new ApiError(
            extractErrorMessage(
                payload,
            ),
            typeof backendCode === 'string'
                ? backendCode as ApiErrorCode
                : errorCodeFromStatus(
                    response.status,
                ),
            response.status,
            extractErrorDetails(
                payload,
            ),
        )
    }

    if (!isJson) {
        if (
            response.status === 204
            || payload === ''
        ) {
            return undefined as T
        }

        throw new ApiError(
            'پاسخ نامعتبر از سرور دریافت شد.',
            'SERVER_ERROR',
            502,
        )
    }

    return payload as T
}

async function refreshAdminAccessToken():
    Promise<boolean> {
    const refreshToken =
        getAdminRefreshToken()

    if (!refreshToken) {
        return false
    }

    try {
        const response = await fetch(
            buildUrl(
                '/admin/auth/refresh/',
            ),
            {
                method: 'POST',

                headers: {
                    Accept:
                        'application/json',
                    'Content-Type':
                        'application/json',
                },

                credentials: 'include',

                body: JSON.stringify({
                    refresh: refreshToken,
                }),
            },
        )

        const result =
            await parseResponse<{
                access: string
                refresh?: string
            }>(response)

        if (!result.access) {
            throw new ApiError(
                'توکن دسترسی جدید دریافت نشد.',
                'UNAUTHENTICATED',
                401,
            )
        }

        setAdminAccessToken(
            result.access,
        )

        if (result.refresh) {
            if (
                typeof window !== 'undefined'
            ) {
                window.sessionStorage.setItem(
                    ADMIN_REFRESH_TOKEN_KEY,
                    result.refresh,
                )
            }
        }

        return true
    } catch {
        clearAdminTokens()
        return false
    }
}

export async function adminRequest<T>(
    path: string,
    options: AdminRequestOptions = {},
    allowRefresh = true,
): Promise<T> {
    const headers =
        new Headers(options.headers)

    headers.set(
        'Accept',
        'application/json',
    )

    if (
        options.body !== undefined
        && !(options.body instanceof FormData)
    ) {
        headers.set(
            'Content-Type',
            'application/json',
        )
    }

    const accessToken =
        getAdminAccessToken()

    if (accessToken) {
        headers.set(
            'Authorization',
            `Bearer ${accessToken}`,
        )
    }

    const requestBody =
        options.body instanceof FormData
            ? options.body
            : options.body === undefined
                ? undefined
                : JSON.stringify(
                    options.body,
                )

    const {
        body: _body,
        ...requestOptions
    } = options

    const response = await fetch(
        buildUrl(path),
        {
            ...requestOptions,

            credentials: 'include',

            headers,

            body: requestBody,
        },
    )

    if (
        response.status === 401
        && allowRefresh
        && !path.includes(
            '/admin/auth/login/',
        )
        && !path.includes(
            '/admin/auth/refresh/',
        )
        && getAdminRefreshToken()
    ) {
        const refreshed =
            await refreshAdminAccessToken()

        if (refreshed) {
            return adminRequest<T>(
                path,
                options,
                false,
            )
        }
    }

    return parseResponse<T>(
        response,
    )
}

export const adminApi = Object.freeze({
    get: <T>(
        path: string,
        options: Omit<
            AdminRequestOptions,
            'method' | 'body'
        > = {},
    ) =>
        adminRequest<T>(
            path,
            {
                ...options,
                method: 'GET',
            },
        ),

    post: <T>(
        path: string,
        body?: unknown,
        options: Omit<
            AdminRequestOptions,
            'method' | 'body'
        > = {},
    ) =>
        adminRequest<T>(
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
        options: Omit<
            AdminRequestOptions,
            'method' | 'body'
        > = {},
    ) =>
        adminRequest<T>(
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
        options: Omit<
            AdminRequestOptions,
            'method' | 'body'
        > = {},
    ) =>
        adminRequest<T>(
            path,
            {
                ...options,
                method: 'PATCH',
                body,
            },
        ),

    delete: <T>(
        path: string,
        options: Omit<
            AdminRequestOptions,
            'method' | 'body'
        > = {},
    ) =>
        adminRequest<T>(
            path,
            {
                ...options,
                method: 'DELETE',
            },
        ),
})

export default adminApi