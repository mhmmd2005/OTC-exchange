import {isValidIranianMobile, normalizePhone} from '../utils/phone'

const USERS_KEY = 'otc-mock-users'
const OTP_KEY = 'otc-mock-otp'
const FLOW_KEY = 'otc-mock-flow'
const OTP_CODE = '123456'

function getUsers() {
    try {
        const users = JSON.parse(localStorage.getItem(USERS_KEY) || 'null')
        if (Array.isArray(users) && users.length) return users
    } catch {
    }

    const defaults = [{
        id: 1,
        phone_number: '+989123456780',
        full_name: 'کاربر تستی',
        avatar: null,
        password: 'Aa123456!',
        is_phone_verified: true,
        kyc_status: 'not_started',
        kyc_level: 'basic',
        created_at: new Date().toISOString(),
    }]

    localStorage.setItem(USERS_KEY, JSON.stringify(defaults))
    return defaults
}

function saveUsers(users) {
    localStorage.setItem(USERS_KEY, JSON.stringify(users))
}

function findUser(phone) {
    const normalized = normalizePhone(phone)
    return getUsers().find(user => user.phone_number === normalized || user.phone_number === `+98${normalized.slice(1)}`)
}

function createToken(prefix) {
    return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2)}`
}

function createOtpChallenge(phone, purpose) {
    const challengeId = String(Date.now())
    const flowToken = createToken(`mock-${purpose}`)

    localStorage.setItem(OTP_KEY, JSON.stringify({
        challengeId,
        phone,
        purpose,
        otp: OTP_CODE,
        expiresAt: Date.now() + 180000,
        verified: false,
        flowToken,
    }))

    return {challengeId, flowToken}
}

function getOtpChallenge() {
    try {
        return JSON.parse(localStorage.getItem(OTP_KEY) || 'null')
    } catch {
        return null
    }
}

function getFlow(flowToken) {
    try {
        const flow = JSON.parse(localStorage.getItem(FLOW_KEY) || 'null')
        if (!flow || flow.flowToken !== flowToken || flow.expiresAt < Date.now()) return null
        return flow
    } catch {
        return null
    }
}

function createFlow(challenge, flowToken) {
    localStorage.setItem(FLOW_KEY, JSON.stringify({
        flowToken,
        challengeId: challenge.challengeId,
        phone: challenge.phone,
        purpose: challenge.purpose,
        expiresAt: Date.now() + 600000,
    }))
}

function mapUser(user) {
    if (!user) return null
    const {password, ...safeUser} = user
    return safeUser
}

function buildAuthResponse(user) {
    return {
        ok: true,
        access: createToken('mock-access'),
        refresh: createToken('mock-refresh'),
        user: mapUser(user),
    }
}

export const authService = {
    async requestLoginOtp(phone) {
        const normalized = normalizePhone(phone)

        if (!isValidIranianMobile(normalized)) {
            return {ok: false, message: 'شماره موبایل معتبر نیست.'}
        }

        const user = findUser(normalized)

        if (!user) {
            return {
                ok: true,
                phone: normalized,
                needsRegistration: true,
                mode: 'register',
                message: 'برای این شماره حسابی وجود ندارد.',
            }
        }

        const challenge = createOtpChallenge(normalized, 'login')

        return {
            ok: true,
            challengeId: challenge.challengeId,
            phone: normalized,
            expiresIn: 180,
            resendAvailableIn: 120,
            needsRegistration: false,
            mode: 'login',
        }
    },

    async requestRegistrationOtp(phone) {
        const normalized = normalizePhone(phone)

        if (!isValidIranianMobile(normalized)) {
            return {ok: false, message: 'شماره موبایل معتبر نیست.'}
        }

        const user = findUser(normalized)

        if (user) {
            return {
                ok: true,
                alreadyRegistered: true,
                phone: normalized,
                message: 'این شماره قبلاً ثبت شده است.',
            }
        }

        const challenge = createOtpChallenge(normalized, 'registration')

        return {
            ok: true,
            challengeId: challenge.challengeId,
            phone: normalized,
            expiresIn: 180,
            resendAvailableIn: 120,
            alreadyRegistered: false,
            mode: 'register',
        }
    },

    async requestPasswordResetOtp(phone) {
        const normalized = normalizePhone(phone)

        if (!isValidIranianMobile(normalized)) {
            return {ok: false, message: 'شماره موبایل معتبر نیست.'}
        }

        const user = findUser(normalized)

        if (!user) {
            return {ok: false, message: 'حسابی با این شماره پیدا نشد.'}
        }

        const challenge = createOtpChallenge(normalized, 'password_reset')

        return {
            ok: true,
            challengeId: challenge.challengeId,
            phone: normalized,
            expiresIn: 180,
            resendAvailableIn: 120,
        }
    },

    async verifyOtp(challengeId, otp) {
        const challenge = getOtpChallenge()

        if (!challenge || challenge.challengeId !== String(challengeId)) {
            return {ok: false, message: 'درخواست تأیید معتبر نیست.'}
        }

        if (challenge.expiresAt < Date.now()) {
            return {ok: false, message: 'کد تأیید منقضی شده است.'}
        }

        if (String(otp) !== OTP_CODE) {
            return {ok: false, message: 'کد تأیید صحیح نیست.'}
        }

        const flowToken = createToken(`mock-${challenge.purpose}`)

        challenge.verified = true
        challenge.flowToken = flowToken

        localStorage.setItem(OTP_KEY, JSON.stringify(challenge))
        createFlow(challenge, flowToken)

        return {
            ok: true,
            flowToken,
            nextStep: challenge.purpose === 'password_reset' ? 'password_reset' : 'password',
            expiresIn: 600,
        }
    },

    async verifyLoginPassword(flowToken, password) {
        const flow = getFlow(flowToken)

        if (!flow || flow.purpose !== 'login') {
            return {ok: false, message: 'درخواست ورود معتبر نیست.'}
        }

        const user = findUser(flow.phone)

        if (!user || user.password !== password) {
            return {ok: false, message: 'رمز عبور صحیح نیست.'}
        }

        return buildAuthResponse(user)
    },

    async registerWithPassword(flowToken, password, confirmPassword) {
        const flow = getFlow(flowToken)

        if (!flow || flow.purpose !== 'registration') {
            return {ok: false, message: 'درخواست ثبت‌نام معتبر نیست.'}
        }

        if (password !== confirmPassword) {
            return {ok: false, message: 'رمزهای عبور یکسان نیستند.'}
        }

        if (password.length < 6) {
            return {ok: false, message: 'رمز عبور باید حداقل ۶ کاراکتر باشد.'}
        }

        const users = getUsers()

        if (findUser(flow.phone)) {
            return {ok: false, message: 'این شماره قبلاً ثبت شده است.'}
        }

        const user = {
            id: Date.now(),
            phone_number: `+98${flow.phone.slice(1)}`,
            full_name: '',
            avatar: null,
            password,
            is_phone_verified: true,
            kyc_status: 'not_started',
            kyc_level: 'basic',
            created_at: new Date().toISOString(),
        }

        users.push(user)
        saveUsers(users)

        return buildAuthResponse(user)
    },

    async resetPassword(flowToken, password, confirmPassword) {
        const flow = getFlow(flowToken)

        if (!flow || flow.purpose !== 'password_reset') {
            return {ok: false, message: 'درخواست بازیابی معتبر نیست.'}
        }

        if (password !== confirmPassword) {
            return {ok: false, message: 'رمزهای عبور یکسان نیستند.'}
        }

        if (password.length < 6) {
            return {ok: false, message: 'رمز عبور باید حداقل ۶ کاراکتر باشد.'}
        }

        const users = getUsers()
        const index = users.findIndex(user =>
            user.phone_number === flow.phone ||
            user.phone_number === `+98${flow.phone.slice(1)}`
        )

        if (index === -1) {
            return {ok: false, message: 'حسابی با این شماره پیدا نشد.'}
        }

        users[index].password = password
        saveUsers(users)

        localStorage.removeItem(OTP_KEY)
        localStorage.removeItem(FLOW_KEY)

        return {
            ok: true,
            message: 'رمز عبور با موفقیت تغییر کرد.',
        }
    },

    async getCurrentUser() {
        const token = localStorage.getItem('otc-access-token')
        const savedUser = localStorage.getItem('otc-user')

        if (!token || !savedUser) {
            throw new Error('کاربر وارد نشده است.')
        }

        return {
            data: {
                user: JSON.parse(savedUser),
            },
        }
    },

    async refresh(refreshToken) {
        if (!refreshToken) throw new Error('Refresh token موجود نیست.')

        return {
            access: createToken('mock-access'),
            refresh: refreshToken,
        }
    },

    async logout() {
        return {message: 'خروج با موفقیت انجام شد.'}
    },
}

export default authService