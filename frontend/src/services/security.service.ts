import type {ActiveSession, SecurityEvent, SecurityEventType, SecurityOverview, TwoFactorSetup,} from '@/types'
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

    changePassword(
        input: ChangePasswordInput,
    ): Promise<void>

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
    mobileVerified: boolean
    emailVerified: boolean
    twoFactorEnabled: boolean
    antiPhishingEnabled: boolean
    antiPhishingCode: string
    withdrawalWhitelistEnabled: boolean
    activeSessionsCount: number
}

interface SecurityEventResponse {
    id: number
    user: number | null
    event_type: string
    description: string
    ip_address: string | null
    created_at: string
}

interface SecurityEventListResponse {
    count: number
    next: string | null
    previous: string | null
    results: SecurityEventResponse[]
}

interface TwoFactorSetupResponse {
    setup_token: string
    secret: string
    otpauth_uri: string
    issuer: string
    account_label: string
    expires_at: string
}

const eventTitleMap: Record<string, string> = {
    otp_requested: 'درخواست کد تأیید',
    otp_verified: 'کد تأیید شد',
    otp_failed: 'کد تأیید ناموفق بود',
    login_success: 'ورود موفق',
    login_failure: 'ورود ناموفق',
    registration_success: 'ثبت‌نام موفق',
    logout: 'خروج از حساب',
    password_change: 'رمز عبور تغییر کرد',
    password_reset_success: 'رمز عبور بازنشانی شد',
    kyc_update: 'اطلاعات احراز هویت تغییر کرد',
    security_alert: 'هشدار امنیتی',
    two_factor_enabled:
        'ورود دومرحله‌ای فعال شد',
    two_factor_disabled:
        'ورود دومرحله‌ای غیرفعال شد',
    anti_phishing_created:
        'کد ضد فیشینگ ثبت شد',
    anti_phishing_updated:
        'کد ضد فیشینگ تغییر کرد',
    anti_phishing_deleted:
        'کد ضد فیشینگ حذف شد',
}

function mapSecurityOverview(
    data: SecurityOverviewResponse,
): SecurityOverview {
    return {
        ...mockDbSecurity,
        mobileVerified:
            Boolean(data.mobileVerified),
        emailVerified:
            Boolean(data.emailVerified),
        twoFactorEnabled:
            Boolean(data.twoFactorEnabled),
        antiPhishingEnabled:
            Boolean(data.antiPhishingEnabled),
        antiPhishingCode:
            data.antiPhishingCode ?? '',
        withdrawalWhitelistEnabled:
            Boolean(
                data.withdrawalWhitelistEnabled,
            ),
        activeSessionsCount:
            Number(
                data.activeSessionsCount ?? 0,
            ),
    }
}

function mapSecurityEvent(
    data: SecurityEventResponse,
): SecurityEvent {
    return {
        id: String(data.id),
        type:
            data.event_type as SecurityEventType,
        title:
            eventTitleMap[data.event_type]
            ?? 'رویداد امنیتی',
        description:
            data.description
            || 'رویداد امنیتی ثبت شد.',
        ipAddress:
            data.ip_address ?? '—',
        deviceName: 'مرورگر',
        createdAt: data.created_at,
    }
}

const mockDbSecurity: SecurityOverview = {
    score: 72,
    passwordConfigured: true,
    mobileVerified: true,
    emailVerified: false,
    twoFactorEnabled: false,
    antiPhishingEnabled: false,
    antiPhishingCode: '',
    withdrawalWhitelistEnabled: false,
    activeSessionsCount:
    mockDb.sessions.length,
}

export function isMockTwoFactorEnabled(): boolean {
    return mockDbSecurity.twoFactorEnabled
}

export const securityService: SecurityService = {
    getOverview: async () => {
        const data =
            await api.get<SecurityOverviewResponse>(
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

    listEvents: async () => {
        const data =
            await api.get<
                | SecurityEventResponse[]
                | SecurityEventListResponse
            >('/security/events/')

        if (Array.isArray(data)) {
            return data.map(
                mapSecurityEvent,
            )
        }

        return data.results.map(
            mapSecurityEvent,
        )
    },

    changePassword: (
        input: ChangePasswordInput,
    ) =>
        api.post<void>(
            '/security/password/',
            input,
        ),

    startTwoFactorSetup: async () => {
        const data =
            await api.post<TwoFactorSetupResponse>(
                '/security/two-factor/setup/',
            )

        return {
            setupToken: data.setup_token,
            secret: data.secret,
            otpauthUri: data.otpauth_uri,
            issuer: data.issuer,
            accountLabel:
            data.account_label,
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