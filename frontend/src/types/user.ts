import type { DecimalString, ISODateString } from './common'

export type AccountLevel = 'level_0' | 'level_1' | 'level_2' | 'level_3'
export type KycStatus =
  | 'not_started'
  | 'in_progress'
  | 'pending'
  | 'verified'
  | 'needs_correction'
  | 'rejected'

export interface UserProfile {
  id: string
  firstName: string
  lastName: string
  fullName: string
  mobile: string
  email?: string
  nationalId: string
  birthDate: string
  avatarUrl?: string
  mobileVerified: boolean
  emailVerified: boolean
  bankVerified: boolean
  kycStatus: KycStatus
  accountLevel: AccountLevel
  joinedAt: ISODateString
  lastLoginAt: ISODateString
}

export interface UserLimits {
  accountLevel: AccountLevel
  dailyBuy: DecimalString
  dailySell: DecimalString
  dailyTomanDeposit: DecimalString
  dailyTomanWithdrawal: DecimalString
  dailyCryptoWithdrawalTomanEquivalent: DecimalString
  usedBuy: DecimalString
  usedSell: DecimalString
  usedTomanDeposit: DecimalString
  usedTomanWithdrawal: DecimalString
  usedCryptoWithdrawalTomanEquivalent: DecimalString
}

export interface UpdateProfileInput {
  firstName?: string
  lastName?: string
  email?: string
}

export interface DashboardSummary {
  user: UserProfile
  totalPortfolioToman: DecimalString
  tomanBalance: DecimalString
  cryptoValueToman: DecimalString
  pendingOrdersCount: number
  unreadNotificationsCount: number
  kycStatus: KycStatus
  accountLevel: AccountLevel
}

