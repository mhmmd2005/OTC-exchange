import type {
  AuthResult,
  LoginInput,
  OtpChallenge,
  PasswordResetProof,
  RegisterInput,
  RequestOtpInput,
  ResetPasswordInput,
  UserProfile,
  VerifyOtpInput,
} from '@/types'
import { normalizeDigits } from '@/utils/formatters'
import { LEGAL_DOCUMENTS } from '@/constants/legal'
import { ApiError, api, resolveApi } from './api'
import { createMockId, futureIso, nowIso } from './mock/helpers'
import { mockDb } from './mock/state'

export interface AuthService {
  login(input: LoginInput): Promise<AuthResult>
  register(input: RegisterInput): Promise<OtpChallenge>
  requestOtp(input: RequestOtpInput): Promise<OtpChallenge>
  verifyOtp(input: VerifyOtpInput): Promise<AuthResult>
  verifyPasswordResetOtp(input: VerifyOtpInput): Promise<PasswordResetProof>
  resetPassword(input: ResetPasswordInput): Promise<void>
  getCurrentUser(): Promise<UserProfile>
  logout(): Promise<void>
}

const mockPasswordResetProofs = new Map<string, { mobile: string; expiresAt: number }>()
interface MockOtpChallenge extends OtpChallenge { attempts: number }
const mockOtpChallenges = new Map<string, MockOtpChallenge>()
const latestOtpChallengeByScope = new Map<string, string>()

function normalizeMobile(value: string): string {
  let mobile = normalizeDigits(value).replace(/\D/g, '')
  if (mobile.startsWith('98') && mobile.length === 12) mobile = `0${mobile.slice(2)}`
  return mobile
}

function assertMobile(mobile: string): void {
  if (!/^09\d{9}$/.test(mobile)) {
    throw new ApiError('شماره موبایل واردشده معتبر نیست.', 'VALIDATION_ERROR', 422, {
      fields: { mobile: 'شماره موبایل باید با ۰۹ شروع شود و ۱۱ رقم داشته باشد.' },
    })
  }
}

function createChallenge(input: RequestOtpInput): OtpChallenge {
  const mobile = normalizeMobile(input.mobile)
  assertMobile(mobile)
  const scope = `${mobile}:${input.purpose}`
  const previousId = latestOtpChallengeByScope.get(scope)
  const previous = previousId ? mockOtpChallenges.get(previousId) : undefined
  if (previous && Date.parse(previous.resendAt) > Date.now()) {
    const retryAfter = Math.ceil((Date.parse(previous.resendAt) - Date.now()) / 1000)
    throw new ApiError('برای ارسال دوباره کد کمی صبر کنید.', 'RATE_LIMITED', 429, { retryAfter })
  }
  if (previousId) mockOtpChallenges.delete(previousId)
  const challenge: MockOtpChallenge = {
    challengeId: createMockId('otp'),
    mobile,
    purpose: input.purpose,
    expiresAt: futureIso(120),
    resendAt: futureIso(60),
    attempts: 0,
  }
  mockOtpChallenges.set(challenge.challengeId, challenge)
  latestOtpChallengeByScope.set(scope, challenge.challengeId)
  return challenge
}

function assertChallenge(input: VerifyOtpInput): MockOtpChallenge {
  const challenge = mockOtpChallenges.get(input.challengeId)
  const mobile = normalizeMobile(input.mobile)
  if (
    !challenge
    || challenge.mobile !== mobile
    || challenge.purpose !== input.purpose
    || Date.parse(challenge.expiresAt) <= Date.now()
  ) {
    if (challenge) mockOtpChallenges.delete(input.challengeId)
    throw new ApiError('درخواست کد منقضی یا نامعتبر است؛ کد تازه بگیرید.', 'UNAUTHENTICATED', 401)
  }
  if (challenge.attempts >= 5) {
    throw new ApiError('تعداد تلاش‌های ناموفق بیش از حد مجاز است؛ کد تازه بگیرید.', 'RATE_LIMITED', 429)
  }
  return challenge
}

function consumeChallenge(challenge: OtpChallenge): void {
  mockOtpChallenges.delete(challenge.challengeId)
  latestOtpChallengeByScope.delete(`${challenge.mobile}:${challenge.purpose}`)
}

export const authService: AuthService = {
  login(input) {
    return resolveApi(() => {
      const mobile = normalizeMobile(input.mobile)
      assertMobile(mobile)
      if (input.password.length < 8) {
        throw new ApiError('شماره موبایل یا رمز عبور صحیح نیست.', 'UNAUTHENTICATED', 401)
      }
      mockDb.user.mobile = mobile
      mockDb.user.lastLoginAt = new Date().toISOString()
      return { user: mockDb.user }
    }, () => api.post<AuthResult>('/auth/login', input))
  },

  register(input) {
    return resolveApi(() => {
      const mobile = normalizeMobile(input.mobile)
      assertMobile(mobile)
      if (!input.acceptedTerms) {
        throw new ApiError('برای ادامه، پذیرش قوانین الزامی است.', 'VALIDATION_ERROR', 422, {
          fields: { acceptedTerms: 'لطفاً قوانین استفاده از خدمات را بپذیرید.' },
        })
      }
      if (
        input.termsVersion !== LEGAL_DOCUMENTS.terms.version
        || input.privacyVersion !== LEGAL_DOCUMENTS.privacy.version
        || !Number.isFinite(Date.parse(input.acceptedAt))
      ) {
        throw new ApiError('نسخه اسناد حقوقی معتبر نیست؛ صفحه را تازه‌سازی کنید.', 'VALIDATION_ERROR', 422, {
          fields: { acceptedTerms: 'شرایط استفاده و حریم خصوصی را دوباره بررسی و تأیید کنید.' },
        })
      }
      if (input.password.length < 8) {
        throw new ApiError('رمز عبور باید حداقل ۸ کاراکتر باشد.', 'VALIDATION_ERROR', 422, {
          fields: { password: 'حداقل ۸ کاراکتر وارد کنید.' },
        })
      }
      if (input.password !== input.passwordConfirmation) {
        throw new ApiError('تکرار رمز عبور یکسان نیست.', 'VALIDATION_ERROR', 422, {
          fields: { passwordConfirmation: 'رمزهای عبور با هم مطابقت ندارند.' },
        })
      }
      mockDb.user.mobile = mobile
      return createChallenge({ mobile, purpose: 'register' })
    }, () => api.post<OtpChallenge>('/auth/register', input))
  },

  requestOtp(input) {
    return resolveApi(() => createChallenge(input), () => api.post<OtpChallenge>('/auth/otp', input))
  },

  verifyOtp(input) {
    return resolveApi(() => {
      const mobile = normalizeMobile(input.mobile)
      assertMobile(mobile)
      const challenge = assertChallenge(input)
      const code = normalizeDigits(input.code).replace(/\D/g, '')
      if (code !== '123456') {
        challenge.attempts += 1
        throw new ApiError('کد تأیید صحیح نیست یا منقضی شده است.', 'VALIDATION_ERROR', 422, {
          fields: { code: 'برای نسخه نمایشی، کد ۱۲۳۴۵۶ را وارد کنید.' },
        })
      }
      consumeChallenge(challenge)
      mockDb.user.mobile = mobile
      mockDb.user.mobileVerified = true
      const mobileStep = mockDb.verification.steps.find((step) => step.id === 'mobile')
      if (mobileStep) {
        mobileStep.status = 'verified'
        mobileStep.completedAt = nowIso()
      }
      return { user: mockDb.user }
    }, () => api.post<AuthResult>('/auth/otp/verify', input))
  },

  verifyPasswordResetOtp(input) {
    return resolveApi(() => {
      const mobile = normalizeMobile(input.mobile)
      assertMobile(mobile)
      const challenge = assertChallenge(input)
      const code = normalizeDigits(input.code).replace(/\D/g, '')
      if (input.purpose !== 'reset_password' || code !== '123456') {
        challenge.attempts += 1
        throw new ApiError('کد تأیید صحیح نیست یا منقضی شده است.', 'VALIDATION_ERROR', 422, {
          fields: { code: 'برای نسخه نمایشی، کد ۱۲۳۴۵۶ را وارد کنید.' },
        })
      }
      consumeChallenge(challenge)
      const resetToken = `mock_reset_${createMockId('proof')}`
      const expiresAt = Date.now() + 10 * 60 * 1000
      mockPasswordResetProofs.set(resetToken, { mobile, expiresAt })
      return { mobile, resetToken, expiresAt: new Date(expiresAt).toISOString() }
    }, () => api.post<PasswordResetProof>('/auth/password/verify', input))
  },

  resetPassword(input) {
    return resolveApi(() => {
      const proof = mockPasswordResetProofs.get(input.resetToken)
      if (!proof || proof.expiresAt <= Date.now()) {
        mockPasswordResetProofs.delete(input.resetToken)
        throw new ApiError('مجوز بازیابی منقضی شده است؛ دوباره کد بگیرید.', 'UNAUTHENTICATED', 401)
      }
      if (input.password.length < 8 || input.password !== input.passwordConfirmation) {
        throw new ApiError('رمز عبور جدید معتبر نیست.', 'VALIDATION_ERROR', 422)
      }
      mockPasswordResetProofs.delete(input.resetToken)
    }, () => api.post<void>('/auth/password/reset', input))
  },

  getCurrentUser() {
    return resolveApi(() => mockDb.user, () => api.get<UserProfile>('/users/me'))
  },

  logout() {
    return resolveApi(() => undefined, () => api.post<void>('/auth/logout'))
  },
}

export default authService
