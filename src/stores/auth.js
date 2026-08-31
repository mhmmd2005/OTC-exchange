import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { authService } from '../services/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(JSON.parse(localStorage.getItem('otc-user') || 'null'))
  const isAuthenticated = computed(() => Boolean(user.value))
  const loading = ref(false)
  const error = ref('')

  async function login(credentials) {
    loading.value = true
    error.value = ''
    try {
      const response = await authService.login(credentials)
      const result = response.data
      if (result.user) {
        user.value = result.user
        localStorage.setItem('otc-user', JSON.stringify(result.user))
        localStorage.setItem('otc-token', result.token)
        return true
      }
      error.value = result.message || 'ورود ناموفق بود.'
      return false
    } finally {
      loading.value = false
    }
  }

  function logout() {
    user.value = null
    localStorage.removeItem('otc-user')
    localStorage.removeItem('otc-token')
  }

  return { user, isAuthenticated, loading, error, login, logout }
})
