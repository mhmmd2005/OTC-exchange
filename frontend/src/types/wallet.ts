import type { AssetSymbol, DecimalString, ISODateString } from './common'
import type { AssetNetwork } from './market'

export interface WalletAsset {
  symbol: AssetSymbol
  nameFa: string
  nameEn: string
  iconUrl?: string
  color: string
  available: DecimalString
  locked: DecimalString
  total: DecimalString
  tomanValue: DecimalString
  buyEnabled: boolean
  sellEnabled: boolean
  depositEnabled: boolean
  withdrawalEnabled: boolean
  networks: AssetNetwork[]
}

export interface WalletSummary {
  totalValueToman: DecimalString
  tomanBalance: DecimalString
  availableToman: DecimalString
  lockedToman: DecimalString
  cryptoValueToman: DecimalString
  assets: WalletAsset[]
  updatedAt: ISODateString
}

export type PortfolioPeriod = '24h' | '7d' | '30d'

export interface PortfolioValuePoint {
  timestamp: ISODateString
  valueToman: DecimalString
}

export interface DepositAddress {
  assetSymbol: AssetSymbol
  networkCode: string
  address: string
  memo?: string
  minimumDeposit: DecimalString
  requiredConfirmations: number
  createdAt: ISODateString
}

export interface TomanDepositInput {
  amount: DecimalString
  bankAccountId: string
}

export interface TomanDepositResult {
  id: string
  amount: DecimalString
  paymentUrl: string
  expiresAt: ISODateString
}

export interface TomanWithdrawalInput {
  estimateToken: string
  estimateVersion: number
  idempotencyKey: string
}

export interface TomanWithdrawalDraft {
  amount: DecimalString
  bankAccountId: string
}

export interface WithdrawalEstimate {
  estimateToken: string
  estimateVersion: number
  expiresAt: ISODateString
  amount: DecimalString
  bankAccountId: string
  fee: DecimalString
  receivable: DecimalString
  estimatedSettlement: string
}

export interface CryptoWithdrawalDraft {
  assetSymbol: AssetSymbol
  networkCode: string
  address: string
  memo?: string
  amount: DecimalString
}

export interface CryptoWithdrawalInput {
  estimateToken: string
  estimateVersion: number
  otpChallengeToken: string
  otp: string
  twoFactorCode?: string
  idempotencyKey: string
}

export interface CryptoWithdrawalEstimate {
  estimateToken: string
  estimateVersion: number
  expiresAt: ISODateString
  assetSymbol: AssetSymbol
  networkCode: string
  address: string
  memo?: string
  amount: DecimalString
  tomanEquivalent: DecimalString
  fee: DecimalString
  receivable: DecimalString
  estimatedArrivalMinutes: number
}

export interface WithdrawalOtpChallenge {
  challengeToken: string
  purpose: 'crypto_withdrawal'
  estimateToken: string
  estimateVersion: number
  destinationHint: string
  expiresAt: ISODateString
  resendAvailableAt: ISODateString
}
