import type {ActiveSession, SecurityEvent, SecurityOverview, TwoFactorSetup,} from '@/types'
import {api} from './api'
import {mockDb} from './mock/state'

export interface ChangePasswordInput {
    currentPassword: string
    newPassword: string
    newPasswordConfirmation: string
}

export interface SecurityService {
    getOverview(): Promise<SecurityOverview>

    listSessions(): Promise<ActiveSession[]>

    revokeSession(id: string): Promise<void>

    revokeOtherSessions(): Promise<void>

    listEvents(): Promise<SecurityEvent[]>

    changePassword(input: ChangePasswordInput): Promise<void>

    startTwoFactorSetup(): Promise<TwoFactorSetup>

    setTwoFactor(
        enabled: boolean,
        code?: string,
        setupToken?: string,
    ): Promise<SecurityOverview>

    setAntiPhishingCode(
        code: string | null,
    ): Promise<SecurityOverview>

    setWithdrawalWhitelist(
        enabled: boolean,
    ): Promise<SecurityOverview>
}

interface SecurityOverviewResponse {
    mobile_verified: boolean
    email_verified: boolean
    two_factor_enabled: boolean
    anti_phishing_code_enabled: boolean
    withdrawal_whitelist_enabled: boolean
    active_sessions_count: number
}

interface TwoFactorSetupResponse {
    setup_token: string
    secret: string
    otpauth_uri: string
    issuer: string
    account_label: string
    expires_at: string
}

function mapSecurityOverview(
    data: SecurityOverviewResponse,
): SecurityOverview {
    return {
        ...mockDbSecurity,
        mobileVerified: Boolean(data.mobile_verified),
        emailVerified: Boolean(data.email_verified),
        twoFactorEnabled: Boolean(data.two_factor_enabled),
        antiPhishingEnabled: Boolean(
            data.anti_phishing_code_enabled,
        ),
        withdrawalWhitelistEnabled: Boolean(
            data.withdrawal_whitelist_enabled,
        ),
        activeSessionsCount: data.active_sessions_count,
    }
}

function overview(): SecurityOverview {
    const base = mockDb.sessions.length <= 1 ? 78 : 72
    const extra = mockDb.user.emailVerified ? 5 : 0

    return {
        ...mockDbSecurity,
        mobileVerified: mockDb.user.mobileVerified,
        emailVerified: mockDb.user.emailVerified,
        score: Math.min(
            100,
            base +
            extra +
            (mockDbSecurity.twoFactorEnabled ? 12 : 0) +
            (mockDbSecurity.antiPhishingEnabled ? 5 : 0),
        ),
        activeSessionsCount: mockDb.sessions.length,
    }
}

const mockDbSecurity: SecurityOverview = {
    score: 72,
    passwordConfigured: true,
    mobileVerified: true,
    emailVerified: false,
    twoFactorEnabled: false,
    antiPhishingEnabled: false,
    withdrawalWhitelistEnabled: false,
    activeSessionsCount: mockDb.sessions.length,
}

export function isMockTwoFactorEnabled(): boolean {
    return mockDbSecurity.twoFactorEnabled
}

export const securityService: SecurityService = {
    getOverview: async () => {
        const data = await api.get<SecurityOverviewResponse>(
            '/security/',
        )

        return mapSecurityOverview(data)
    },

    listSessions: () =>
        api.get<ActiveSession[]>(
            '/security/sessions/',
        ),

    revokeSession: (id: string) =>
        api.delete<void>(
            `/security/sessions/${id}/`,
        ),

    revokeOtherSessions: () =>
        api.delete<void>(
            '/security/sessions/others/',
        ),

    listEvents: () =>
        api.get<SecurityEvent[]>(
            '/security/events/',
        ),

    changePassword: (input: ChangePasswordInput) =>
        api.post<void>(
            '/security/password/',
            input,
        ),

    startTwoFactorSetup: async () => {
        const data = await api.post<TwoFactorSetupResponse>(
            '/security/two-factor/setup/',
        )

        return {
            setupToken: data.setup_token,
            secret: data.secret,
            otpauthUri: data.otpauth_uri,
            issuer: data.issuer,
            accountLabel: data.account_label,
            expiresAt: data.expires_at,
        }
    },

    setTwoFactor: async (
        enabled: boolean,
        code?: string,
        setupToken?: string,
    ) => {
        await api.patch<SecurityOverviewResponse>(
            '/security/two-factor/',
            {
                enabled,
                code,
                setupToken,
            },
        )

        return securityService.getOverview()
    },

    setAntiPhishingCode: async (
        code: string | null,
    ) => {
        await api.patch<SecurityOverviewResponse>(
            '/security/anti-phishing/',
            {
                code,
            },
        )

        return securityService.getOverview()
    },

    setWithdrawalWhitelist: async (
        enabled: boolean,
    ) => {
        await api.patch<SecurityOverviewResponse>(
            '/security/withdrawal-whitelist/',
            {
                enabled,
            },
        )

        return securityService.getOverview()
    },
}

export default securityService