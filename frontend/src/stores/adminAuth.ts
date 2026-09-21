import {computed, ref} from 'vue'
import {defineStore} from 'pinia'
import {
    adminAuthService,
    type AdminIdentity,
} from '@/services/admin/adminAuth.service'

import {
    clearAdminAuthTokens,
} from '@/services/admin/adminApi'

const ADMIN_ACCESS_TOKEN_KEY =
    'rosha_admin_access_token'

const ADMIN_REFRESH_TOKEN_KEY =
    'rosha_admin_refresh_token'

function setAdminTokens(
    accessToken: string,
    refreshToken: string,
): void {
    if (typeof window === 'undefined') {
        return
    }

    window.sessionStorage.setItem(
        ADMIN_ACCESS_TOKEN_KEY,
        accessToken,
    )

    window.sessionStorage.setItem(
        ADMIN_REFRESH_TOKEN_KEY,
        refreshToken,
    )
}

export const useAdminAuthStore = defineStore(
    'admin-auth',
    () => {
        const user =
            ref<AdminIdentity | null>(null)

        const initialized =
            ref(false)

        const loading =
            ref(false)

        const isAuthenticated =
            computed(
                () => Boolean(user.value),
            )

        async function hydrate(): Promise<void> {
            if (initialized.value) return

            try {
                user.value =
                    await adminAuthService.me()
            } catch {
                user.value = null
                clearAdminAuthTokens()
            } finally {
                initialized.value = true
            }
        }

        async function login(
            email: string,
            password: string,
        ): Promise<void> {
            if (loading.value) return

            loading.value = true

            try {
                const result =
                    await adminAuthService.login(
                        email,
                        password,
                    )

                setAdminTokens(
                    result.access,
                    result.refresh,
                )

                user.value = result.user
                initialized.value = true
            } finally {
                loading.value = false
            }
        }

        async function logout(): Promise<void> {
            try {
                await adminAuthService.logout()
            } catch {
                // حتی در صورت خطای سرور،
                // توکن محلی باید پاک شود.
            } finally {
                clearAdminAuthTokens()

                user.value = null
                initialized.value = true
            }
        }

        return {
            user,
            initialized,
            loading,
            isAuthenticated,
            hydrate,
            login,
            logout,
        }
    },
)