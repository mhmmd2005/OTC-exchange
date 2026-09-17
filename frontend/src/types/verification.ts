import type { DecimalString, ISODateString } from './common'
import type { AccountLevel, KycStatus, UserLimits } from './user'

export type VerificationStepId =
  | 'mobile'
  | 'basic_info'
  | 'identity'
  | 'bank'

export interface BasicIdentityInput {
  firstName: string
  lastName: string
  nationalId: string
  birthDate: string
}

export interface VerificationStep {
  id: VerificationStepId
  title: string
  description: string
  status: KycStatus
  required: boolean
  locked?: boolean
  rejectionReason?: string
  completedAt?: ISODateString
  actionLabel?: string
  actionRoute?: string
}

export interface AccountLevelBenefit {
  label: string
  value: DecimalString | string
}

export interface AccountLevelInfo {
  level: AccountLevel
  title: string
  description: string
  active: boolean
  requirements: string[]
  benefits: AccountLevelBenefit[]
}

export interface VerificationSummary {
  status: KycStatus
  currentLevel: AccountLevel
  progressPercent: number
  message: string
  currentStepId: VerificationStepId | null
  reviewPending: boolean
  basicInfo: BasicIdentityInput
  steps: VerificationStep[]
  levels: AccountLevelInfo[]
  limits: UserLimits
}

export interface VerificationSubmission {
  id: string
  stepId: VerificationStepId
  status: KycStatus
  submittedAt: ISODateString
  nextStep?: VerificationStepId | null
  reviewPending?: boolean
  message?: string
}