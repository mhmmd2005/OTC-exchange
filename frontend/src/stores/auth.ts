import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import type {
  AuthResult,
  LoginInput,
  OtpChallenge,
  PasswordResetProof,
  RegisterInput,
  RequestOtpInput,
  ResetPasswordInput,
  UserProfile,
  VerifyOtpInput,
} from '@/types'
import { authService } from '@/services/auth.service'
import { ApiError } from '@/services/api'

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'خطای پیش‌بینی‌نشده‌ای رخ داد.'
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<UserProfile | null>(null)
  const loading = ref(false)
  const initialized = ref(false)
  const error = ref<string | null>(null)
  const passwordResetProof = ref<PasswordResetProof | null>(null)
  const otpChallenge = ref<OtpChallenge | null>(null)

  const isAuthenticated = computed(() => Boolean(user.value))
  const displayName = computed(() => user.value?.firstName || 'کاربر روشا')

  function applyAuth(result: AuthResult): void {
    user.value = result.user
  }

  function clearAuth(): void {
    user.value = null
    otpChallenge.value = null
    passwordResetProof.value = null
  }

  function clearPasswordResetProof(): void {
    passwordResetProof.value = null
  }

  function expireSession(): void {
    clearAuth()
    initialized.value = true
    error.value = 'نشست شما منقضی شده است؛ دوباره وارد شوید.'
  }

  async function hydrate(): Promise<void> {
    if (initialized.value) return
    error.value = null
    loading.value = true
    try {
      user.value = await authService.getCurrentUser()
    } catch (caught) {
      clearAuth()
      error.value = errorMessage(caught)
    } finally {
      loading.value = false
      initialized.value = true
    }
  }

  async function login(input: LoginInput): Promise<UserProfile> {
    loading.value = true
    error.value = null
    try {
      const result = await authService.login(input)
      applyAuth(result)
      initialized.value = true
      return result.user
    } catch (caught) {
      error.value = errorMessage(caught)
      throw caught
    } finally {
      loading.value = false
    }
  }

  async function register(input: RegisterInput): Promise<OtpChallenge> {
    loading.value = true
    error.value = null
    try {
      const challenge = await authService.register(input)
      otpChallenge.value = challenge
      return challenge
    } catch (caught) {
      error.value = errorMessage(caught)
      throw caught
    } finally {
      loading.value = false
    }
  }

  async function requestOtp(input: RequestOtpInput): Promise<OtpChallenge> {
    loading.value = true
    error.value = null
    try {
      if (input.purpose === 'reset_password') passwordResetProof.value = null
      const challenge = await authService.requestOtp(input)
      otpChallenge.value = challenge
      return challenge
    } catch (caught) {
      error.value = errorMessage(caught)
      throw caught
    } finally {
      loading.value = false
    }
  }

  async function verifyPasswordResetOtp(input: VerifyOtpInput): Promise<PasswordResetProof> {
    loading.value = true
    error.value = null
    try {
      const proof = await authService.verifyPasswordResetOtp(input)
      otpChallenge.value = null
      passwordResetProof.value = proof
      return proof
    } catch (caught) {
      error.value = errorMessage(caught)
      throw caught
    } finally {
      loading.value = false
    }
  }

  async function verifyOtp(input: VerifyOtpInput): Promise<UserProfile> {
    loading.value = true
    error.value = null
    try {
      const result = await authService.verifyOtp(input)
      otpChallenge.value = null
      applyAuth(result)
      initialized.value = true
      return result.user
    } catch (caught) {
      error.value = errorMessage(caught)
      throw caught
    } finally {
      loading.value = false
    }
  }

  async function refreshUser(): Promise<UserProfile> {
    const refreshed = await authService.getCurrentUser()
    user.value = refreshed
    initialized.value = true
    return refreshed
  }

  async function resetPassword(input: Pick<ResetPasswordInput, 'password' | 'passwordConfirmation'>): Promise<void> {
    loading.value = true
    error.value = null
    try {
      if (!passwordResetProof.value) throw new Error('مجوز بازیابی در دسترس نیست؛ دوباره کد بگیرید.')
      await authService.resetPassword({ ...input, resetToken: passwordResetProof.value.resetToken })
      passwordResetProof.value = null
    } catch (caught) {
      if (caught instanceof ApiError && (caught.status === 401 || caught.code === 'UNAUTHENTICATED')) {
        passwordResetProof.value = null
      }
      error.value = errorMessage(caught)
      throw caught
    } finally {
      loading.value = false
    }
  }

  async function logout(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      await authService.logout()
      clearAuth()
      initialized.value = true
    } catch (caught) {
      // A 401 confirms that no server-side session remains. Other failures may
      // leave the HttpOnly session cookie valid, so do not pretend logout has
      // completed or navigate away from the authenticated shell.
      if (caught instanceof ApiError && (caught.status === 401 || caught.code === 'UNAUTHENTICATED')) {
        clearAuth()
        initialized.value = true
        return
      }
      error.value = errorMessage(caught)
      throw caught
    } finally {
      loading.value = false
    }
  }

  return {
    user,
    loading,
    initialized,
    error,
    passwordResetProof,
    otpChallenge,
    isAuthenticated,
    displayName,
    hydrate,
    initialize: hydrate,
    login,
    register,
    requestOtp,
    verifyOtp,
    verifyPasswordResetOtp,
    refreshUser,
    resetPassword,
    expireSession,
    logout,
    clearPasswordResetProof,
    clearError: () => { error.value = null },
  }
})
