import type { ActiveSession, SecurityEvent, SecurityOverview, TwoFactorSetup } from '@/types'
import { ApiError, api, resolveApi } from './api'
import { createMockId, futureIso, nowIso } from './mock/helpers'
import { mockDb } from './mock/state'

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
  getOverview() {
    return resolveApi(() => overview(), () => api.get<SecurityOverview>('/security'))
  },

  listSessions() {
    return resolveApi(() => mockDb.sessions, () => api.get<ActiveSession[]>('/security/sessions'))
  },

  revokeSession(id) {
    return resolveApi(() => {
      const session = mockDb.sessions.find((item) => item.id === id)
      if (!session) throw new ApiError('نشست مورد نظر پیدا نشد.', 'NOT_FOUND', 404)
      if (session.current) {
        throw new ApiError('برای خروج از نشست فعلی از گزینه خروج حساب استفاده کنید.', 'BAD_REQUEST', 409)
      }
      mockDb.sessions = mockDb.sessions.filter((item) => item.id !== id)
      mockDb.securityEvents.unshift({
        id: createMockId('sec'),
        type: 'session_revoked',
        title: 'دسترسی دستگاه قطع شد',
        description: `نشست ${session.deviceName} توسط شما پایان یافت.`,
        ipAddress: session.ipAddress,
        deviceName: session.deviceName,
        createdAt: nowIso(),
      })
    }, () => api.delete<void>(`/security/sessions/${id}`))
  },

  revokeOtherSessions() {
    return resolveApi(() => {
      mockDb.sessions = mockDb.sessions.filter((session) => session.current)
    }, () => api.delete<void>('/security/sessions/others'))
  },

  listEvents() {
    return resolveApi(() => mockDb.securityEvents, () => api.get<SecurityEvent[]>('/security/events'))
  },

  changePassword(input) {
    return resolveApi(() => {
      if (input.currentPassword.length < 8) {
        throw new ApiError('رمز عبور فعلی صحیح نیست.', 'VALIDATION_ERROR', 422, {
          fields: { currentPassword: 'رمز عبور فعلی را بررسی کنید.' },
        })
      }
      if (input.newPassword.length < 8 || input.newPassword !== input.newPasswordConfirmation) {
        throw new ApiError('رمز عبور جدید معتبر نیست یا تکرار آن مطابقت ندارد.', 'VALIDATION_ERROR', 422)
      }
      mockDb.securityEvents.unshift({
        id: createMockId('sec'),
        type: 'password_changed',
        title: 'رمز عبور تغییر کرد',
        description: 'رمز عبور حساب با موفقیت به‌روزرسانی شد.',
        ipAddress: '185.44.***.***',
        deviceName: 'دستگاه فعلی',
        createdAt: nowIso(),
      })
    }, () => api.post<void>('/security/password', input))
  },

  startTwoFactorSetup() {
    return resolveApi(() => {
      const setupToken = `mock_2fa_${createMockId('setup')}`
      const secret = 'JBSWY3DPEHPK3PXP'
      const issuer = 'Rosha'
      const accountLabel = mockDb.user.mobile
      activeMockTwoFactorSetup = {
        setupToken,
        secret,
        issuer,
        accountLabel,
        otpauthUri: `otpauth://totp/${encodeURIComponent(`${issuer}:${accountLabel}`)}?secret=${secret}&issuer=${issuer}&digits=6&period=30`,
        expiresAt: futureIso(10 * 60),
      }
      return activeMockTwoFactorSetup
    }, () => api.post<TwoFactorSetup>('/security/two-factor/setup'))
  },

  setTwoFactor(enabled, code, setupToken) {
    return resolveApi(() => {
      if (enabled && (!activeMockTwoFactorSetup || setupToken !== activeMockTwoFactorSetup.setupToken)) {
        throw new ApiError('درخواست فعال‌سازی منقضی شده است؛ دوباره کد QR بگیرید.', 'UNAUTHENTICATED', 401)
      }
      if (enabled && code !== '123456') {
        throw new ApiError('کد برنامه تأییدکننده صحیح نیست.', 'VALIDATION_ERROR', 422)
      }
      mockDbSecurity.twoFactorEnabled = enabled
      activeMockTwoFactorSetup = null
      return overview()
    }, () => api.patch<SecurityOverview>('/security/two-factor', { enabled, code, setupToken }))
  },

  setAntiPhishingCode(code) {
    return resolveApi(() => {
      const normalized = code?.trim() ?? ''
      if (normalized && (normalized.length < 4 || normalized.length > 20)) {
        throw new ApiError('کد ضد فیشینگ باید بین ۴ تا ۲۰ کاراکتر باشد.', 'VALIDATION_ERROR', 422)
      }
      mockDbSecurity.antiPhishingEnabled = Boolean(normalized)
      mockDbSecurity.antiPhishingCode = normalized || undefined
      return overview()
    }, () => api.patch<SecurityOverview>('/security/anti-phishing', { code }))
  },

  setWithdrawalWhitelist(enabled) {
    return resolveApi(() => {
      mockDbSecurity.withdrawalWhitelistEnabled = enabled
      return overview()
    }, () => api.patch<SecurityOverview>('/security/withdrawal-whitelist', { enabled }))
  },
}

export default securityService
