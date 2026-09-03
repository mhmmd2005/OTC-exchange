import axios from 'axios'

const api = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1',
    timeout: 12000,
    headers: {
        'Content-Type': 'application/json',
    },
})

api.interceptors.request.use((config) => {
    const token = localStorage.getItem('otc-access-token')
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
}, (error) => Promise.reject(error))

api.interceptors.response.use(
    (response) => response,
    (error) => {
        const status = error?.response?.status
        const data = error?.response?.data
        const message = data?.detail || data?.message || 'خطایی رخ داد.'
        const normalizedError = new Error(message)

        normalizedError.status = status
        normalizedError.response = error?.response
        normalizedError.data = data

        if (status === 401) {
            localStorage.removeItem('otc-access-token')
            localStorage.removeItem('otc-refresh-token')
            localStorage.removeItem('otc-user')
        }

        return Promise.reject(normalizedError)
    },
)

export default api