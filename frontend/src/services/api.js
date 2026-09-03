import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 12000,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('otc-token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
}, (error) => Promise.reject(error))

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status
    const message = error?.response?.data?.detail || error?.response?.data?.message || 'خطایی رخ داد.'

    if (status === 401) {
      localStorage.removeItem('otc-token')
      localStorage.removeItem('otc-user')
      window.location.href = '/login'
    }

    return Promise.reject(new Error(message))
  },
)

export default api
