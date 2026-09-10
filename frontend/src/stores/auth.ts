import {computed, ref} from 'vue'
import {defineStore} from 'pinia'
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
import {authService} from '@/services/auth.service'
import {ApiError, clearAuthTokens, getAccessToken, getRefreshToken, setAuthTokens,} from '@/services/api'

function errorMessage(error: unknown): string {
    return error instanceof Error
        ? error.message
        : 'خطای پیش‌بینی‌نشده‌ای رخ داد.'
}

export const useAuthStore = defineStore(
    'auth',
    () => {
        const user =
            ref<UserProfile | null>(null)

        const loading = ref(false)
        const initialized = ref(false)
        const error = ref<string | null>(null)

        const passwordResetProof =
            ref<PasswordResetProof | null>(
                null,
            )

        const otpChallenge =
            ref<OtpChallenge | null>(null)

        const pendingLoginPassword =
            ref<string | null>(null)

        const pendingLoginRemember =
            ref(true)

        const pendingRegistrationPassword =
            ref<string | null>(null)

        const pendingRegistrationConfirmation =
            ref<string | null>(null)

        const isAuthenticated =
            computed(() => Boolean(user.value))

        const displayName =
            computed(
                () =>
                    user.value?.firstName
                    || 'کاربر روشا',
            )

        function applyAuth(
            result: AuthResult,
            remember = true,
        ): void {
            setAuthTokens(
                result.access,
                result.refresh,
                remember,
            )

            user.value = result.user
        }

        function clearPendingFlow(): void {
            pendingLoginPassword.value =
                null

            pendingLoginRemember.value = true

            pendingRegistrationPassword.value =
                null

            pendingRegistrationConfirmation.value =
                null
        }

        function clearAuth(): void {
            user.value = null
            otpChallenge.value = null
            passwordResetProof.value = null
            clearPendingFlow()
            clearAuthTokens()
        }

        function clearPasswordResetProof(): void {
            passwordResetProof.value = null
        }

        function expireSession(): void {
            clearAuth()
            initialized.value = true
            error.value =
                'نشست شما منقضی شده است؛ دوباره وارد شوید.'
        }

        async function hydrate(): Promise<void> {
            if (initialized.value) return

            error.value = null
            loading.value = true

            try {
                if (
                    !getAccessToken()
                    && !getRefreshToken()
                ) {
                    return
                }

                user.value =
                    await authService.getCurrentUser()
            } catch (caught) {
                clearAuth()
                error.value =
                    errorMessage(caught)
            } finally {
                loading.value = false
                initialized.value = true
            }
        }

        async function login(
            input: LoginInput,
        ): Promise<OtpChallenge> {
            loading.value = true
            error.value = null

            clearPendingFlow()
            otpChallenge.value = null

            try {
                const challenge =
                    await authService.login(
                        input,
                    )

                pendingLoginPassword.value =
                    input.password

                pendingLoginRemember.value =
                    input.remember !== false

                otpChallenge.value =
                    challenge

                return challenge
            } catch (caught) {
                error.value =
                    errorMessage(caught)

                throw caught
            } finally {
                loading.value = false
            }
        }

        async function register(
            input: RegisterInput,
        ): Promise<OtpChallenge> {
            loading.value = true
            error.value = null

            clearPendingFlow()
            otpChallenge.value = null

            try {
                const challenge =
                    await authService.register(
                        input,
                    )

                pendingRegistrationPassword.value =
                    input.password

                pendingRegistrationConfirmation.value =
                    input.passwordConfirmation

                otpChallenge.value =
                    challenge

                return challenge
            } catch (caught) {
                error.value =
                    errorMessage(caught)

                throw caught
            } finally {
                loading.value = false
            }
        }

        async function requestOtp(
            input: RequestOtpInput,
        ): Promise<OtpChallenge> {
            loading.value = true
            error.value = null

            try {
                if (
                    input.purpose
                    === 'reset_password'
                ) {
                    passwordResetProof.value =
                        null
                    clearPendingFlow()
                }

                const challenge =
                    await authService.requestOtp(
                        input,
                    )

                otpChallenge.value =
                    challenge

                return challenge
            } catch (caught) {
                error.value =
                    errorMessage(caught)

                throw caught
            } finally {
                loading.value = false
            }
        }

        async function verifyPasswordResetOtp(
            input: VerifyOtpInput,
        ): Promise<PasswordResetProof> {
            loading.value = true
            error.value = null

            try {
                const proof =
                    await authService
                        .verifyPasswordResetOtp(
                            input,
                        )

                otpChallenge.value = null
                passwordResetProof.value =
                    proof

                return proof
            } catch (caught) {
                error.value =
                    errorMessage(caught)

                throw caught
            } finally {
                loading.value = false
            }
        }

        async function verifyOtp(
            input: VerifyOtpInput,
        ): Promise<UserProfile> {
            loading.value = true
            error.value = null

            try {
                const flow =
                    await authService.verifyOtp(
                        input,
                    )

                if (
                    input.purpose === 'login'
                ) {
                    if (
                        !pendingLoginPassword.value
                    ) {
                        throw new ApiError(
                            'اطلاعات ورود در این مرورگر در دسترس نیست؛ دوباره وارد شوید.',
                            'BAD_REQUEST',
                            400,
                        )
                    }

                    const result =
                        await authService.completeLogin(
                            flow.flowToken,
                            pendingLoginPassword.value,
                        )

                    applyAuth(
                        result,
                        pendingLoginRemember.value,
                    )

                    otpChallenge.value = null
                    clearPendingFlow()
                    initialized.value = true

                    return result.user
                }

                if (
                    input.purpose === 'register'
                ) {
                    if (
                        !pendingRegistrationPassword.value
                        || !pendingRegistrationConfirmation.value
                    ) {
                        throw new ApiError(
                            'اطلاعات ثبت‌نام در این مرورگر در دسترس نیست؛ ثبت‌نام را دوباره شروع کنید.',
                            'BAD_REQUEST',
                            400,
                        )
                    }

                    const result =
                        await authService
                            .completeRegistration(
                                flow.flowToken,
                                pendingRegistrationPassword.value,
                                pendingRegistrationConfirmation.value,
                            )

                    applyAuth(
                        result,
                        true,
                    )

                    otpChallenge.value = null
                    clearPendingFlow()
                    initialized.value = true

                    return result.user
                }

                throw new ApiError(
                    'این نوع فرآیند OTP برای احراز هویت حساب پشتیبانی نمی‌شود.',
                    'BAD_REQUEST',
                    400,
                )
            } catch (caught) {
                error.value =
                    errorMessage(caught)

                throw caught
            } finally {
                loading.value = false
            }
        }

        async function refreshUser(): Promise<UserProfile> {
            const refreshed =
                await authService
                    .getCurrentUser()

            user.value = refreshed
            initialized.value = true

            return refreshed
        }

        async function resetPassword(
            input: Pick<
                ResetPasswordInput,
                'password'
                | 'passwordConfirmation'
            >,
        ): Promise<void> {
            loading.value = true
            error.value = null

            try {
                if (
                    !passwordResetProof.value
                ) {
                    throw new Error(
                        'مجوز بازیابی در دسترس نیست؛ دوباره کد بگیرید.',
                    )
                }

                await authService.resetPassword({
                    ...input,
                    flowToken:
                    passwordResetProof.value
                        .flowToken,
                })

                passwordResetProof.value =
                    null
            } catch (caught) {
                if (
                    caught instanceof ApiError
                    && (
                        caught.status === 401
                        || caught.code
                        === 'UNAUTHENTICATED'
                    )
                ) {
                    passwordResetProof.value =
                        null
                }

                error.value =
                    errorMessage(caught)

                throw caught
            } finally {
                loading.value = false
            }
        }

        async function logout(): Promise<void> {
            loading.value = true
            error.value = null

            const refreshToken =
                getRefreshToken()

            try {
                if (!refreshToken) {
                    clearAuth()
                    initialized.value = true
                    return
                }

                await authService.logout(
                    refreshToken,
                )

                clearAuth()
                initialized.value = true
            } catch (caught) {
                if (
                    caught instanceof ApiError
                    && (
                        caught.status === 400
                        || caught.status === 401
                        || caught.code
                        === 'UNAUTHENTICATED'
                    )
                ) {
                    clearAuth()
                    initialized.value = true
                    return
                }

                error.value =
                    errorMessage(caught)

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
            clearError: () => {
                error.value = null
            },
        }
    },
)