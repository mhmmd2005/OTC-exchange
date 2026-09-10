import type {ActiveSession, SecurityEvent, SecurityOverview, TwoFactorSetup} from '@/types'
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

    setTwoFactor(enabled: boolean, code?: string, setupToken?: string): Promise<SecurityOverview>

    setAntiPhishingCode(code: string | null): Promise<SecurityOverview>

    setWithdrawalWhitelist(enabled: boolean): Promise<SecurityOverview>
}

function overview(): SecurityOverview {
    const base = mockDb.sessions.length <= 1 ? 78 : 72
    const extra = mockDb.user.emailVerified ? 5 : 0
    return {
        ...mockDbSecurity,
        mobileVerified: mockDb.user.mobileVerified,
        emailVerified: mockDb.user.emailVerified,
        score: Math.min(100, base + extra + (mockDbSecurity.twoFactorEnabled ? 12 : 0)
            + (mockDbSecurity.antiPhishingEnabled ? 5 : 0)),
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

/** Mock-backend policy hook; never used by the live API path. */
export function isMockTwoFactorEnabled(): boolean {
    return mockDbSecurity.twoFactorEnabled
}

let activeMockTwoFactorSetup: TwoFactorSetup | null = null

export const securityService: SecurityService = {
    getOverview: () =>
        api.get<SecurityOverview>('/security/'),

    listSessions: () =>
        api.get<ActiveSession[]>('/security/sessions/'),

    revokeSession: (id: string) =>
        api.delete<void>(`/security/sessions/${id}/`),

    revokeOtherSessions: () =>
        api.delete<void>('/security/sessions/others/'),

    listEvents: () =>
        api.get<SecurityEvent[]>('/security/events/'),

    changePassword: (input: ChangePasswordInput) =>
        api.post<void>('/security/password/', input),

    startTwoFactorSetup: () =>
        api.post<TwoFactorSetup>('/security/two-factor/setup/'),

    setTwoFactor: (
        enabled: boolean,
        code?: string,
        setupToken?: string,
    ) =>
        api.patch<SecurityOverview>(
            '/security/two-factor/',
            {
                enabled,
                code,
                setupToken,
            },
        ),

    setAntiPhishingCode: (
        code: string | null,
    ) =>
        api.patch<SecurityOverview>(
            '/security/anti-phishing/',
            {code},
        ),

    setWithdrawalWhitelist: (
        enabled: boolean,
    ) =>
        api.patch<SecurityOverview>(
            '/security/withdrawal-whitelist/',
            {enabled},
        ),
}

export default securityService
