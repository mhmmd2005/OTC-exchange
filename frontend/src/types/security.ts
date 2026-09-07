import type { ISODateString, ThemePreference } from './common'

export interface ActiveSession {
  id: string
  deviceName: string
  deviceType: 'desktop' | 'mobile' | 'tablet'
  browser: string
  os: string
  ipAddress: string
  approximateLocation?: string
  current: boolean
  createdAt: ISODateString
  lastActiveAt: ISODateString
}

export type SecurityEventType =
  | 'login_success'
  | 'login_failed'
  | 'password_changed'
  | 'two_factor_enabled'
  | 'session_revoked'
  | 'withdrawal_confirmed'

export interface SecurityEvent {
  id: string
  type: SecurityEventType
  title: string
  description: string
  ipAddress: string
  deviceName: string
  createdAt: ISODateString
}

export interface SecurityOverview {
  score: number
  passwordConfigured: boolean
  mobileVerified: boolean
  emailVerified: boolean
  twoFactorEnabled: boolean
  antiPhishingEnabled: boolean
  antiPhishingCode?: string
  withdrawalWhitelistEnabled: boolean
  activeSessionsCount: number
}

export interface TwoFactorSetup {
  setupToken: string
  secret: string
  otpauthUri: string
  issuer: string
  accountLabel: string
  expiresAt: ISODateString
}

export interface UserPreferences {
  theme: ThemePreference
  hideBalances: boolean
  hideZeroBalances: boolean
  usePersianDigits: boolean
  reduceMotion: boolean
  favoriteAssets: string[]
  notificationChannels: {
    inApp: boolean
    sms: boolean
    email: boolean
  }
}
