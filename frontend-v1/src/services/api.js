import axios from 'axios'

const api = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1',
    timeout: 12000,
    headers: {
        'Content-Type': 'application/json',
    },
})

let isRefreshing = false
let refreshSubscribers = []

function subscribeTokenRefresh(resolve, reject) {
    refreshSubscribers.push({resolve, reject})
}

function notifyRefreshSuccess(token) {
    refreshSubscribers.forEach(({resolve}) => resolve(token))
    refreshSubscribers = []
}

function notifyRefreshFailure(error) {
    refreshSubscribers.forEach(({reject}) => reject(error))
    refreshSubscribers = []
}

function clearStoredAuth() {
    localStorage.removeItem('otc-access-token')
    localStorage.removeItem('otc-refresh-token')
    localStorage.removeItem('otc-user')
    localStorage.removeItem('otc-last-activity')
}

function emitAuthExpired() {
    window.dispatchEvent(
        new CustomEvent('otc-auth-expired'),
    )
}

api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem(
            'otc-access-token',
        )

        if (token) {
            config.headers = config.headers || {}
            config.headers.Authorization = `Bearer ${token}`
        }

        if (config.data instanceof FormData) {
            delete config.headers['Content-Type']
        }

        return config
    },
    (error) => Promise.reject(error),
)

api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config
        const status = error?.response?.status

        if (
            status !== 401 ||
            !originalRequest ||
            originalRequest._retry ||
            originalRequest.url?.includes(
                '/auth/refresh/',
            )
        ) {
            return Promise.reject(error)
        }

        const refreshToken =
            localStorage.getItem(
                'otc-refresh-token',
            )

        if (!refreshToken) {
            clearStoredAuth()
            emitAuthExpired()
            return Promise.reject(error)
        }

        if (isRefreshing) {
            return new Promise(
                (resolve, reject) => {
                    subscribeTokenRefresh(
                        resolve,
                        reject,
                    )
                },
            ).then((newAccessToken) => {
                originalRequest._retry = true
                originalRequest.headers =
                    originalRequest.headers || {}

                originalRequest.headers.Authorization =
                    `Bearer ${newAccessToken}`

                return api(originalRequest)
            })
        }

        originalRequest._retry = true
        isRefreshing = true

        try {
            const refreshResponse =
                await axios.post(
                    `${api.defaults.baseURL}/auth/refresh/`,
                    {
                        refresh: refreshToken,
                    },
                    {
                        headers: {
                            'Content-Type':
                                'application/json',
                        },
                    },
                )

            const newAccessToken =
                refreshResponse?.data?.access

            const newRefreshToken =
                refreshResponse?.data?.refresh ||
                refreshToken

            if (!newAccessToken) {
                throw new Error(
                    'Refresh token response did not contain an access token.',
                )
            }

            localStorage.setItem(
                'otc-access-token',
                newAccessToken,
            )

            localStorage.setItem(
                'otc-refresh-token',
                newRefreshToken,
            )

            notifyRefreshSuccess(
                newAccessToken,
            )

            originalRequest.headers =
                originalRequest.headers || {}

            originalRequest.headers.Authorization =
                `Bearer ${newAccessToken}`

            return api(originalRequest)
        } catch (refreshError) {
            notifyRefreshFailure(
                refreshError,
            )

            clearStoredAuth()
            emitAuthExpired()

            return Promise.reject(
                refreshError,
            )
        } finally {
            isRefreshing = false
        }
    },
)

export default api