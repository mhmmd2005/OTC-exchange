import {
    adminApi,
    clearAdminAuthTokens,
    getAdminRefreshTokenValue,
} from '@/services/admin/adminApi'

export interface AdminIdentity {
    id: number
    email: string
    fullName: string
    role: 'super_admin' | 'admin'
    accountType: 'admin'
}

export interface AdminAuthResponse {
    access: string
    refresh: string
    user: AdminIdentity
}

export const adminAuthService = {
    async login(
        email: string,
        password: string,
    ): Promise<AdminAuthResponse> {
        return adminApi.post<AdminAuthResponse>(
            '/admin/auth/login/',
            {
                email,
                password,
            },
        )
    },

    async me(): Promise<AdminIdentity> {
        return adminApi.get<AdminIdentity>(
            '/admin/auth/me/',
        )
    },

    async logout(): Promise<void> {
        const refresh =
            getAdminRefreshTokenValue()

        if (!refresh) return

        await adminApi.post(
            '/admin/auth/logout/',
            {
                refresh,
            },
        )
    },

    clearTokens(): void {
        clearAdminAuthTokens()
    },
}

export default adminAuthService