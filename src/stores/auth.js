import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { authService } from '../services/auth'

const STORAGE_KEY = 'otc-user'
const TOKEN_KEY = 'otc-token'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const isAuthenticated = computed(() => Boolean(user.value))
  const loading = ref(false)
  const error = ref('')
  const authMode = ref('login')
  const authStep = ref('phone')
  const phone = ref('')
  const challengeId = ref('')
  const flowToken = ref('')
  const otpExpiresAt = ref(null)
  const resendAvailableAt = ref(null)

  function initialize() {
    try {
      const savedUser = JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null')
      user.value = savedUser
    } catch {
      user.value = null
      localStorage.removeItem(STORAGE_KEY)
    }
  }

  function persistUser(nextUser) {
    user.value = nextUser
    if (nextUser) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(nextUser))
      localStorage.setItem(TOKEN_KEY, `mock-token-${Date.now()}`)
      return
    }

    localStorage.removeItem(STORAGE_KEY)
    localStorage.removeItem(TOKEN_KEY)
  }

  function resetAuthFlow({ keepPhone = false } = {}) {
    authMode.value = 'login'
    authStep.value = 'phone'
    challengeId.value = ''
    flowToken.value = ''
    otpExpiresAt.value = null
    resendAvailableAt.value = null
    if (!keepPhone) {
      phone.value = ''
    }
    error.value = ''
  }

  async function requestLoginOtp(nextPhone) {
    loading.value = true
    error.value = ''
    try {
      const result = await authService.requestLoginOtp(nextPhone)
      if (!result.ok) {
        error.value = result.message || 'درخواست کد ناموفق بود.'
        return result
      }

      phone.value = result.phone
      authMode.value = result.mode
      authStep.value = 'otp'
      challengeId.value = result.challengeId
      otpExpiresAt.value = result.expiresAt || null
      if (result.needsRegistration) {
        authMode.value = 'register'
      }
      return result
    } finally {
      loading.value = false
    }
  }

  async function requestRegistrationOtp(nextPhone) {
    loading.value = true
    error.value = ''
    try {
      const result = await authService.requestRegistrationOtp(nextPhone)
      if (!result.ok) {
        error.value = result.message || 'درخواست کد ناموفق بود.'
        return result
      }

      phone.value = result.phone
      authMode.value = 'register'
      authStep.value = 'otp'
      challengeId.value = result.challengeId || ''
      otpExpiresAt.value = result.expiresAt || null
      return result
    } finally {
      loading.value = false
    }
  }

  async function verifyOtp(otpValue) {
    loading.value = true
    error.value = ''
    try {
      const result = await authService.verifyOtp(challengeId.value, otpValue)
      if (!result.ok) {
        error.value = result.message || 'کد تایید نامعتبر است.'
        return result
      }

      flowToken.value = result.flowToken
      authStep.value = 'password'
      otpExpiresAt.value = null
      return result
    } finally {
      loading.value = false
    }
  }

  async function verifyLoginPassword(passwordValue) {
    loading.value = true
    error.value = ''
    try {
      const result = await authService.verifyLoginPassword(flowToken.value, passwordValue)
      if (!result.ok) {
        error.value = result.message || 'رمز عبور صحیح نیست.'
        return result
      }

      persistUser(result.user)
      authStep.value = 'phone'
      return result
    } finally {
      loading.value = false
    }
  }

  async function registerWithPassword(passwordValue, confirmPasswordValue) {
    loading.value = true
    error.value = ''
    try {
      const result = await authService.registerWithPassword(flowToken.value, passwordValue, confirmPasswordValue)
      if (!result.ok) {
        error.value = result.message || 'ثبت‌نام ناموفق بود.'
        return result
      }

      persistUser(result.user)
      authStep.value = 'phone'
      return result
    } finally {
      loading.value = false
    }
  }

  function logout() {
    persistUser(null)
    resetAuthFlow({ keepPhone: false })
    user.value = null
  }

  return {
    user,
    isAuthenticated,
    loading,
    error,
    authMode,
    authStep,
    phone,
    challengeId,
    flowToken,
    otpExpiresAt,
    resendAvailableAt,
    initialize,
    resetAuthFlow,
    requestLoginOtp,
    requestRegistrationOtp,
    verifyOtp,
    verifyLoginPassword,
    registerWithPassword,
    logout,
  }
})
