export type WithdrawalAddressStatus =
  | 'pending_confirmation'
  | 'cooling_down'
  | 'active'
  | 'disabled'
  | 'blocked'
  | 'revoked'

export type WithdrawalAddressVerificationMethod =
  | 'security_confirmation'
  | 'ownership_signature'
  | 'admin_verified'

export interface WithdrawalAddress {
  id: string
  assetSymbol: string
  assetNameFa: string
  assetNameEn: string
  networkCode: string
  networkName: string
  networkDisplayName: string
  address: string
  memo: string
  label: string
  status: WithdrawalAddressStatus
  verificationMethod: WithdrawalAddressVerificationMethod
  isDefault: boolean
  confirmationRequestedAt: string | null
  confirmedAt: string | null
  cooldownUntil: string | null
  activatedAt: string | null
  lastUsedAt: string | null
  revokedAt: string | null
  blockedReason: string
  createdAt: string
  updatedAt: string
}

export interface WithdrawalAddressCreateInput {
  asset: string
  network: string
  address: string
  memo?: string
  label?: string
}

export interface WithdrawalAddressConfirmation {
  challengeId: string
  expiresIn: number
  resendAvailableIn: number
  destinationHint: string
}

export interface WithdrawalAddressCreateResponse {
  address: WithdrawalAddress
  confirmation: WithdrawalAddressConfirmation
}

export interface WithdrawalAddressConfirmInput {
  challengeId: string
  otp: string
  twoFactorCode?: string
}