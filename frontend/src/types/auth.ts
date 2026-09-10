import type {ISODateString} from './common'
import type {UserProfile} from './user'

export interface LoginInput {
    mobile: string
    password: string
    remember?: boolean
}

export interface RegisterInput {
    mobile: string
    password: string
    passwordConfirmation: string
    referralCode?: string
    acceptedTerms: boolean
    termsVersion: string
    privacyVersion: string
    acceptedAt: ISODateString
}

export type OtpPurpose = 'register' | 'login' | 'reset_password' | 'withdrawal'

export interface RequestOtpInput {
    mobile: string
    purpose: OtpPurpose
}

export interface VerifyOtpInput extends RequestOtpInput {
    challengeId: string
    code: string
}

export interface ResetPasswordInput {
    flowToken: string
    password: string
    passwordConfirmation: string
}

export interface PasswordResetProof {
    mobile: string
    flowToken: string
    expiresAt: ISODateString
}

export interface OtpChallenge {
    challengeId: string
    mobile: string
    purpose: OtpPurpose
    expiresAt: ISODateString
    resendAt: ISODateString
}

export interface AuthFlowResult {
    flowToken: string
    nextStep: 'password'
    expiresAt: ISODateString
}

export interface AuthResult {
    access: string
    refresh: string
    user: UserProfile
}