import {defineStore} from 'pinia'
import {computed, ref} from 'vue'
import {authService} from '../services/auth'
import {isMockMode} from '../services/mode'

const STORAGE_KEY = 'otc-user'
const ACCESS_TOKEN_KEY = 'otc-access-token'
const REFRESH_TOKEN_KEY = 'otc-refresh-token'
const LAST_ACTIVITY_KEY = 'otc-last-activity'
const MOCK_USER_KEY = 'otc-mock-user'
const MOCK_AUTH_KEY = 'otc-mock-auth'

export const useAuthStore = defineStore(
    'auth',
    () => {
        const user = ref(null)
        const isAuthenticated =
            computed(
                () => Boolean(user.value),
            )
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
                if (isMockMode()) {
                    const mockAuth =
                        JSON.parse(
                            localStorage.getItem(
                                MOCK_AUTH_KEY,
                            ) || 'null',
                        )

                    const mockUser =
                        JSON.parse(
                            localStorage.getItem(
                                MOCK_USER_KEY,
                            ) || 'null',
                        )

                    user.value =
                        mockAuth?.authenticated &&
                        mockUser
                            ? mockUser
                            : null

                    return
                }

                const savedUser =
                    JSON.parse(
                        localStorage.getItem(
                            STORAGE_KEY,
                        ) || 'null',
                    )

                const accessToken =
                    localStorage.getItem(
                        ACCESS_TOKEN_KEY,
                    )

                user.value =
                    savedUser &&
                    accessToken
                        ? savedUser
                        : null
            } catch {
                user.value = null
            }
        }

        function persistAuth(data) {
            user.value = data.user

            if (isMockMode()) {
                localStorage.setItem(
                    MOCK_USER_KEY,
                    JSON.stringify(
                        data.user,
                    ),
                )

                localStorage.setItem(
                    MOCK_AUTH_KEY,
                    JSON.stringify({
                        authenticated: true,
                    }),
                )

                localStorage.setItem(
                    LAST_ACTIVITY_KEY,
                    Date.now().toString(),
                )

                return
            }

            localStorage.setItem(
                STORAGE_KEY,
                JSON.stringify(
                    data.user,
                ),
            )

            localStorage.setItem(
                ACCESS_TOKEN_KEY,
                data.access,
            )

            localStorage.setItem(
                REFRESH_TOKEN_KEY,
                data.refresh,
            )

            localStorage.setItem(
                LAST_ACTIVITY_KEY,
                Date.now().toString(),
            )
        }

        function clearAuth() {
            user.value = null

            localStorage.removeItem(
                STORAGE_KEY,
            )
            localStorage.removeItem(
                ACCESS_TOKEN_KEY,
            )
            localStorage.removeItem(
                REFRESH_TOKEN_KEY,
            )
            localStorage.removeItem(
                LAST_ACTIVITY_KEY,
            )

            if (isMockMode()) {
                localStorage.removeItem(
                    MOCK_USER_KEY,
                )

                localStorage.removeItem(
                    MOCK_AUTH_KEY,
                )
            }
        }

        function resetAuthFlow({
                                   keepPhone = false,
                               } = {}) {
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

        async function requestLoginOtp(
            nextPhone,
        ) {
            loading.value = true
            error.value = ''

            try {
                const result =
                    await authService.requestLoginOtp(
                        nextPhone,
                    )

                if (!result.ok) {
                    error.value =
                        result.message ||
                        'درخواست کد ناموفق بود.'

                    return result
                }

                if (
                    result.needsRegistration
                ) {
                    return result
                }

                phone.value =
                    result.phone

                authMode.value =
                    'login'

                authStep.value =
                    'otp'

                challengeId.value =
                    result.challengeId

                otpExpiresAt.value =
                    result.expiresIn
                        ? Date.now() +
                        result.expiresIn *
                        1000
                        : null

                resendAvailableAt.value =
                    result.resendAvailableIn
                        ? Date.now() +
                        result.resendAvailableIn *
                        1000
                        : null

                return result
            } finally {
                loading.value = false
            }
        }

        async function requestRegistrationOtp(
            nextPhone,
        ) {
            loading.value = true
            error.value = ''

            try {
                const result =
                    await authService.requestRegistrationOtp(
                        nextPhone,
                    )

                if (!result.ok) {
                    error.value =
                        result.message ||
                        'درخواست کد ناموفق بود.'

                    return result
                }

                if (
                    result.alreadyRegistered
                ) {
                    error.value =
                        result.message ||
                        'این شماره قبلاً ثبت شده است.'

                    return result
                }

                phone.value =
                    result.phone

                authMode.value =
                    'register'

                authStep.value =
                    'otp'

                challengeId.value =
                    result.challengeId

                otpExpiresAt.value =
                    result.expiresIn
                        ? Date.now() +
                        result.expiresIn *
                        1000
                        : null

                resendAvailableAt.value =
                    result.resendAvailableIn
                        ? Date.now() +
                        result.resendAvailableIn *
                        1000
                        : null

                return result
            } finally {
                loading.value = false
            }
        }

        async function requestPasswordResetOtp(
            nextPhone,
        ) {
            loading.value = true
            error.value = ''

            try {
                const result =
                    await authService.requestPasswordResetOtp(
                        nextPhone,
                    )

                if (!result.ok) {
                    error.value =
                        result.message ||
                        'درخواست بازیابی ناموفق بود.'

                    return result
                }

                phone.value =
                    result.phone

                challengeId.value =
                    result.challengeId

                authMode.value =
                    'reset'

                authStep.value =
                    'otp'

                otpExpiresAt.value =
                    result.expiresIn
                        ? Date.now() +
                        result.expiresIn *
                        1000
                        : null

                resendAvailableAt.value =
                    result.resendAvailableIn
                        ? Date.now() +
                        result.resendAvailableIn *
                        1000
                        : null

                return result
            } finally {
                loading.value = false
            }
        }

        async function verifyOtp(
            otpValue,
        ) {
            loading.value = true
            error.value = ''

            try {
                const result =
                    await authService.verifyOtp(
                        challengeId.value,
                        otpValue,
                    )

                if (!result.ok) {
                    error.value =
                        result.message ||
                        'کد تأیید نامعتبر است.'

                    return result
                }

                flowToken.value =
                    result.flowToken

                otpExpiresAt.value =
                    null

                if (
                    authMode.value ===
                    'reset'
                ) {
                    sessionStorage.setItem(
                        'otc-reset-flow-token',
                        result.flowToken,
                    )
                } else {
                    authStep.value =
                        'password'
                }

                return result
            } finally {
                loading.value = false
            }
        }

        async function verifyLoginPassword(
            passwordValue,
        ) {
            loading.value = true
            error.value = ''

            try {
                const result =
                    await authService.verifyLoginPassword(
                        flowToken.value,
                        passwordValue,
                    )

                if (!result.ok) {
                    error.value =
                        result.message ||
                        'رمز عبور صحیح نیست.'

                    return result
                }

                persistAuth(result)
                authStep.value =
                    'phone'

                return result
            } finally {
                loading.value = false
            }
        }

        async function registerWithPassword(
            passwordValue,
            confirmPasswordValue,
        ) {
            loading.value = true
            error.value = ''

            try {
                const result =
                    await authService.registerWithPassword(
                        flowToken.value,
                        passwordValue,
                        confirmPasswordValue,
                    )

                if (!result.ok) {
                    error.value =
                        result.message ||
                        'ثبت‌نام ناموفق بود.'

                    return result
                }

                persistAuth(result)
                authStep.value =
                    'phone'

                return result
            } finally {
                loading.value = false
            }
        }

        async function resetPassword(
            passwordValue,
            confirmPasswordValue,
        ) {
            loading.value = true
            error.value = ''

            try {
                const token =
                    sessionStorage.getItem(
                        'otc-reset-flow-token',
                    ) ||
                    flowToken.value

                const result =
                    await authService.resetPassword(
                        token,
                        passwordValue,
                        confirmPasswordValue,
                    )

                if (!result.ok) {
                    error.value =
                        result.message ||
                        'تغییر رمز عبور انجام نشد.'

                    return result
                }

                sessionStorage.removeItem(
                    'otc-reset-flow-token',
                )

                resetAuthFlow()

                return result
            } finally {
                loading.value = false
            }
        }

        async function loadCurrentUser() {
            if (isMockMode()) {
                initialize()
                return Boolean(
                    user.value,
                )
            }

            const accessToken =
                localStorage.getItem(
                    ACCESS_TOKEN_KEY,
                )

            if (!accessToken) {
                user.value = null
                return false
            }

            try {
                const result =
                    await authService.getCurrentUser()

                user.value =
                    result.data.user

                localStorage.setItem(
                    STORAGE_KEY,
                    JSON.stringify(
                        result.data.user,
                    ),
                )

                return true
            } catch {
                return false
            }
        }

        async function logout() {
            if (isMockMode()) {
                clearAuth()
                resetAuthFlow()
                return
            }

            const refreshToken =
                localStorage.getItem(
                    REFRESH_TOKEN_KEY,
                )

            try {
                if (refreshToken) {
                    await authService.logout(
                        refreshToken,
                    )
                }
            } catch {
            } finally {
                clearAuth()
                resetAuthFlow()
            }
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
            requestPasswordResetOtp,
            verifyOtp,
            verifyLoginPassword,
            registerWithPassword,
            resetPassword,
            loadCurrentUser,
            logout,
            clearAuth,
        }
    },
)