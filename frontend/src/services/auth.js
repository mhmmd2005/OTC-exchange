import { mockUser } from '../mock/data'
import { isValidIranianMobile, normalizePhone } from '../utils/phone'
import { validatePassword } from '../utils/passwordValidation'

const DEV_OTP = '123456'
const DEV_PASSWORD = 'Demo@1234'

const demoUser = {
  ...mockUser,
  id: 1,
  phone_number: '+989123456789',
  fullName: 'مهدی قاسمی',
  avatar: 'MG',
  kycStatus: 'تأیید شده',
  kycLevel: 'سطح ۲',
}

const userStore = new Map([[demoUser.phone_number, { user: demoUser, password: DEV_PASSWORD }]])
const mockChallenges = new Map()

function sleep(ms = 450) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function buildUserFromPhone(phone, overrides = {}) {
  return {
    id: Date.now() + Math.random(),
    phone_number: phone,
    fullName: overrides.fullName || 'کاربر جدید',
    email: '',
    avatar: overrides.avatar || 'U',
    kycStatus: 'در حال بررسی',
    kycLevel: 'سطح ۱',
    ...overrides,
  }
}

function findChallengeByToken(flowToken) {
  for (const challenge of mockChallenges.values()) {
    if (challenge.flowToken === flowToken) return challenge
  }
  return null
}

export const authService = {
  async requestLoginOtp(phone) {
    await sleep()

    const normalized = normalizePhone(phone)
    if (!isValidIranianMobile(normalized)) {
      return { ok: false, message: 'شماره موبایل معتبر نیست.' }
    }

    if (userStore.has(normalized)) {
      const challengeId = `login-${Date.now()}`
      const challenge = {
        challengeId,
        phone: normalized,
        mode: 'login',
        otp: DEV_OTP,
        expiresAt: Date.now() + 120000,
      }
      mockChallenges.set(challengeId, challenge)

      return {
        ok: true,
        challengeId,
        phone: normalized,
        expiresAt: challenge.expiresAt,
        mode: 'login',
        needsRegistration: false,
      }
    }

    const challengeId = `register-${Date.now()}`
    const challenge = {
      challengeId,
      phone: normalized,
      mode: 'register',
      otp: DEV_OTP,
      expiresAt: Date.now() + 120000,
    }
    mockChallenges.set(challengeId, challenge)

    return {
      ok: true,
      challengeId,
      phone: normalized,
      expiresAt: challenge.expiresAt,
      mode: 'register',
      needsRegistration: true,
    }
  },

  async requestRegistrationOtp(phone) {
    await sleep()

    const normalized = normalizePhone(phone)
    if (!isValidIranianMobile(normalized)) {
      return { ok: false, message: 'شماره موبایل معتبر نیست.' }
    }

    if (userStore.has(normalized)) {
      return {
        ok: true,
        alreadyRegistered: true,
        phone: normalized,
        message: 'این شماره قبلا ثبت شده است.',
      }
    }

    const challengeId = `register-${Date.now()}`
    const challenge = {
      challengeId,
      phone: normalized,
      mode: 'register',
      otp: DEV_OTP,
      expiresAt: Date.now() + 120000,
    }
    mockChallenges.set(challengeId, challenge)

    return {
      ok: true,
      challengeId,
      phone: normalized,
      expiresAt: challenge.expiresAt,
      alreadyRegistered: false,
      mode: 'register',
    }
  },

  async verifyOtp(challengeId, otp) {
    await sleep(320)

    const challenge = mockChallenges.get(challengeId)
    if (!challenge) {
      return { ok: false, message: 'کد تایید صحیح نیست.' }
    }

    if (Date.now() > challenge.expiresAt) {
      mockChallenges.delete(challengeId)
      return { ok: false, expired: true, message: 'کد تایید منقضی شده است.' }
    }

    if (String(otp).trim() !== String(challenge.otp)) {
      return { ok: false, message: 'کد تایید صحیح نیست.' }
    }

    const flowToken = `flow-${Date.now()}`
    challenge.flowToken = flowToken
    mockChallenges.set(challengeId, challenge)

    return {
      ok: true,
      flowToken,
      mode: challenge.mode,
      phone: challenge.phone,
    }
  },

  async verifyLoginPassword(flowToken, password) {
    await sleep(420)

    const challenge = findChallengeByToken(flowToken)
    if (!challenge) {
      return { ok: false, message: 'رمز عبور صحیح نیست.' }
    }

    const userRecord = userStore.get(challenge.phone)
    if (!userRecord) {
      return { ok: false, message: 'رمز عبور صحیح نیست.' }
    }

    if (String(password) !== userRecord.password) {
      return { ok: false, message: 'رمز عبور صحیح نیست.' }
    }

    return { ok: true, user: userRecord.user }
  },

  async registerWithPassword(flowToken, password, confirmPassword) {
    await sleep(420)

    const challenge = findChallengeByToken(flowToken)
    if (!challenge) {
      return { ok: false, message: 'جلسه احراز هویت نامعتبر است.' }
    }

    if (!password || !confirmPassword) {
      return { ok: false, message: 'رمز عبور را وارد کنید.' }
    }

    if (password !== confirmPassword) {
      return { ok: false, message: 'رمزهای عبور یکسان نیستند.' }
    }

    if (!validatePassword(password)) {
      return { ok: false, message: 'رمز عبور شرایط لازم را ندارد.' }
    }

    const user = buildUserFromPhone(challenge.phone, {
      fullName: 'کاربر جدید',
      avatar: 'U',
    })

    userStore.set(challenge.phone, { user, password })

    return { ok: true, user }
  },

  async getCurrentUser() {
    await sleep(120)
    return { data: { user: demoUser } }
  },
}

export default authService
