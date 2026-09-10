import type {
    AccountLevel,
    AuthFlowResult,
    AuthResult,
    KycStatus,
    LoginInput,
    OtpChallenge,
    PasswordResetProof,
    RegisterInput,
    RequestOtpInput,
    ResetPasswordInput,
    UserProfile,
    VerifyOtpInput,
} from '@/types'
import {normalizeDigits} from '@/utils/formatters'
import {LEGAL_DOCUMENTS} from '@/constants/legal'
import {api, ApiError, resolveApi} from './api'
import {createMockId, futureIso, nowIso} from './mock/helpers'
import {mockDb} from './mock/state'

export interface AuthService {
    login(input: LoginInput): Promise<OtpChallenge>

    register(input: RegisterInput): Promise<OtpChallenge>

    requestOtp(input: RequestOtpInput): Promise<OtpChallenge>

    verifyOtp(input: VerifyOtpInput): Promise<AuthFlowResult>

    completeLogin(flowToken: string, password: string): Promise<AuthResult>

    completeRegistration(
        flowToken: string,
        password: string,
        passwordConfirmation: string,
    ): Promise<AuthResult>

    verifyPasswordResetOtp(input: VerifyOtpInput): Promise<PasswordResetProof>

    resetPassword(input: ResetPasswordInput): Promise<void>

    getCurrentUser(): Promise<UserProfile>

    logout(refreshToken: string): Promise<void>
}

interface BackendOtpResponse {
    allowed: boolean
    account_exists: boolean
    challenge_id?: string
    expires_in?: number
    resend_available_in?: number
    next_step?: string
    phone_number?: string
    message?: string
}

interface BackendFlowResponse {
    flow_token: string
    next_step: 'password'
    expires_in: number
}

interface BackendUser {
    id: number
    phone_number: string
    full_name: string
    avatar: string | null
    is_phone_verified: boolean
    kyc_status: string
    kyc_level: string
    created_at: string
}

interface BackendAuthResponse {
    access: string
    refresh: string
    user: BackendUser
}

interface MockOtpChallenge extends OtpChallenge {
    attempts: number
}

interface MockFlow {
    purpose: 'login' | 'register' | 'reset_password'
    mobile: string
    expiresAt: number
}

const mockOtpChallenges = new Map<string, MockOtpChallenge>()
const mockFlows = new Map<string, MockFlow>()

function normalizeMobile(value: string): string {
    let mobile = normalizeDigits(value).replace(/\D/g, '')

    if (
        mobile.startsWith('98')
        && mobile.length === 12
    ) {
        mobile = `0${mobile.slice(2)}`
    }

    return mobile
}

function assertMobile(mobile: string): void {
    if (!/^09\d{9}$/.test(mobile)) {
        throw new ApiError(
            'شماره موبایل واردشده معتبر نیست.',
            'VALIDATION_ERROR',
            422,
            {
                fields: {
                    mobile:
                        'شماره موبایل باید با ۰۹ شروع شود و ۱۱ رقم داشته باشد.',
                },
            },
        )
    }
}

function mapBackendKycStatus(value: string): KycStatus {
    switch (value) {
        case 'in_progress':
            return 'in_progress'
        case 'pending_review':
            return 'pending'
        case 'approved':
            return 'verified'
        case 'rejected':
            return 'rejected'
        case 'needs_correction':
            return 'needs_correction'
        case 'verified':
            return 'verified'
        default:
            return 'not_started'
    }
}

function mapBackendAccountLevel(value: string): AccountLevel {
    if (
        value === 'level_0'
        || value === 'level_1'
        || value === 'level_2'
        || value === 'level_3'
    ) {
        return value
    }

    switch (value) {
        case 'basic':
            return 'level_0'
        case 'intermediate':
            return 'level_1'
        case 'advanced':
            return 'level_2'
        case 'professional':
            return 'level_3'
        default:
            return 'level_0'
    }
}

function adaptBackendUser(
    user: BackendUser,
    lastLoginAt?: string,
): UserProfile {
    const fullName = String(
        user.full_name ?? '',
    ).trim()

    const parts = fullName
        ? fullName.split(/\s+/)
        : []

    const firstName = parts.shift() ?? ''
    const lastName = parts.join(' ')

    return {
        id: String(user.id),
        firstName,
        lastName,
        fullName,
        mobile: normalizeMobile(user.phone_number),
        email: undefined,
        nationalId: '',
        birthDate: '',
        avatarUrl: user.avatar || undefined,
        mobileVerified: Boolean(
            user.is_phone_verified,
        ),
        emailVerified: false,
        bankVerified: false,
        kycStatus: mapBackendKycStatus(
            user.kyc_status,
        ),
        accountLevel: mapBackendAccountLevel(
            user.kyc_level,
        ),
        joinedAt: user.created_at,
        lastLoginAt:
            lastLoginAt
            ?? user.created_at,
    }
}

function adaptBackendAuthResponse(
    response: BackendAuthResponse,
): AuthResult {
    return {
        access: response.access,
        refresh: response.refresh,
        user: adaptBackendUser(
            response.user,
            new Date().toISOString(),
        ),
    }
}

function createChallengeFromBackend(
    response: BackendOtpResponse,
    input: RequestOtpInput,
): OtpChallenge {
    if (!response.allowed) {
        if (
            input.purpose === 'login'
            && response.next_step === 'registration'
        ) {
            throw new ApiError(
                'این شماره موبایل هنوز ثبت‌نام نشده است.',
                'NOT_FOUND',
                404,
                {
                    actionLabel: 'ساخت حساب جدید',
                    actionRoute: '/auth/register',
                },
            )
        }

        if (
            input.purpose === 'register'
            && response.account_exists
        ) {
            throw new ApiError(
                'این شماره موبایل قبلاً ثبت‌نام شده است.',
                'BAD_REQUEST',
                409,
                {
                    actionLabel: 'ورود به حساب',
                    actionRoute: '/auth/login',
                },
            )
        }

        if (
            input.purpose === 'reset_password'
            && !response.account_exists
        ) {
            throw new ApiError(
                'حسابی با این شماره موبایل پیدا نشد.',
                'NOT_FOUND',
                404,
            )
        }

        throw new ApiError(
            response.message
            ?? 'امکان ادامه این درخواست وجود ندارد.',
            'BAD_REQUEST',
            400,
        )
    }

    if (
        !response.challenge_id
        || !Number.isFinite(response.expires_in)
        || !Number.isFinite(
            response.resend_available_in,
        )
    ) {
        throw new ApiError(
            'پاسخ نامعتبر برای درخواست کد دریافت شد.',
            'SERVER_ERROR',
            502,
        )
    }

    const normalizedMobile = normalizeMobile(
        response.phone_number
        || input.mobile,
    )

    return {
        challengeId: String(
            response.challenge_id,
        ),
        mobile: normalizedMobile,
        purpose: input.purpose,
        expiresAt: new Date(
            Date.now()
            + Number(response.expires_in) * 1000,
        ).toISOString(),
        resendAt: new Date(
            Date.now()
            + Number(response.resend_available_in) * 1000,
        ).toISOString(),
    }
}

function createFlowFromBackend(
    response: BackendFlowResponse,
): AuthFlowResult {
    if (!response.flow_token) {
        throw new ApiError(
            'توکن موقت فرآیند احراز هویت دریافت نشد.',
            'SERVER_ERROR',
            502,
        )
    }

    return {
        flowToken: response.flow_token,
        nextStep: 'password',
        expiresAt: new Date(
            Date.now()
            + Number(response.expires_in || 600) * 1000,
        ).toISOString(),
    }
}

async function requestBackendOtp(
    input: RequestOtpInput,
): Promise<OtpChallenge> {
    assertMobile(
        normalizeMobile(input.mobile),
    )

    const backendPurpose =
        input.purpose === 'login'
            ? 'login'
            : input.purpose === 'register'
                ? 'registration'
                : input.purpose === 'reset_password'
                    ? 'password_reset'
                    : null

    if (!backendPurpose) {
        throw new ApiError(
            'این نوع OTP هنوز در Backend احراز هویت پیاده‌سازی نشده است.',
            'NOT_IMPLEMENTED',
            501,
        )
    }

    const endpoint =
        backendPurpose === 'login'
            ? '/auth/request-login-otp/'
            : backendPurpose === 'registration'
                ? '/auth/request-registration-otp/'
                : '/auth/request-password-reset-otp/'

    const response =
        await api.post<BackendOtpResponse>(
            endpoint,
            {
                phone_number: normalizeMobile(
                    input.mobile,
                ),
            },
        )

    return createChallengeFromBackend(
        response,
        input,
    )
}

async function verifyBackendOtp(
    input: VerifyOtpInput,
): Promise<AuthFlowResult> {
    const response =
        await api.post<BackendFlowResponse>(
            '/auth/verify-otp/',
            {
                challenge_id: input.challengeId,
                otp: normalizeDigits(input.code)
                    .replace(/\D/g, ''),
            },
        )

    return createFlowFromBackend(response)
}

function createMockChallenge(
    input: RequestOtpInput,
): OtpChallenge {
    const mobile = normalizeMobile(
        input.mobile,
    )

    assertMobile(mobile)

    const challenge: MockOtpChallenge = {
        challengeId: createMockId('otp'),
        mobile,
        purpose: input.purpose,
        expiresAt: futureIso(180),
        resendAt: futureIso(120),
        attempts: 0,
    }

    mockOtpChallenges.set(
        challenge.challengeId,
        challenge,
    )

    return challenge
}

function createMockFlow(
    challenge: MockOtpChallenge,
): AuthFlowResult {
    const flowToken = createMockId('flow')
    const expiresAt = Date.now() + 10 * 60 * 1000

    mockFlows.set(
        flowToken,
        {
            purpose:
                challenge.purpose as
                    | 'login'
                    | 'register'
                    | 'reset_password',
            mobile: challenge.mobile,
            expiresAt,
        },
    )

    return {
        flowToken,
        nextStep: 'password',
        expiresAt:
            new Date(expiresAt).toISOString(),
    }
}

function getMockFlow(
    flowToken: string,
    purpose:
        | 'login'
        | 'register'
        | 'reset_password',
): MockFlow {
    const flow = mockFlows.get(flowToken)

    if (
        !flow
        || flow.purpose !== purpose
        || flow.expiresAt <= Date.now()
    ) {
        mockFlows.delete(flowToken)

        throw new ApiError(
            'فرآیند احراز هویت منقضی یا نامعتبر است.',
            'UNAUTHENTICATED',
            401,
        )
    }

    return flow
}

export const authService: AuthService = {
    login(input) {
        return resolveApi(
            () => createMockChallenge({
                mobile: input.mobile,
                purpose: 'login',
            }),
            () =>
                requestBackendOtp({
                    mobile: input.mobile,
                    purpose: 'login',
                }),
        )
    },

    register(input) {
        return resolveApi(
            () => {
                const mobile = normalizeMobile(
                    input.mobile,
                )

                assertMobile(mobile)

                if (!input.acceptedTerms) {
                    throw new ApiError(
                        'برای ادامه، پذیرش قوانین الزامی است.',
                        'VALIDATION_ERROR',
                        422,
                    )
                }

                if (
                    input.termsVersion
                    !== LEGAL_DOCUMENTS.terms.version
                    || input.privacyVersion
                    !== LEGAL_DOCUMENTS.privacy.version
                    || !Number.isFinite(
                        Date.parse(input.acceptedAt),
                    )
                ) {
                    throw new ApiError(
                        'نسخه اسناد حقوقی معتبر نیست.',
                        'VALIDATION_ERROR',
                        422,
                    )
                }

                if (
                    input.password.length < 8
                    || input.password
                    !== input.passwordConfirmation
                ) {
                    throw new ApiError(
                        'اطلاعات رمز عبور معتبر نیست.',
                        'VALIDATION_ERROR',
                        422,
                    )
                }

                return createMockChallenge({
                    mobile,
                    purpose: 'register',
                })
            },
            () =>
                requestBackendOtp({
                    mobile: input.mobile,
                    purpose: 'register',
                }),
        )
    },

    requestOtp(input) {
        return resolveApi(
            () => createMockChallenge(input),
            () => requestBackendOtp(input),
        )
    },

    verifyOtp(input) {
        return resolveApi(
            () => {
                const challenge =
                    mockOtpChallenges.get(
                        input.challengeId,
                    )

                if (
                    !challenge
                    || challenge.purpose
                    !== input.purpose
                    || challenge.mobile
                    !== normalizeMobile(
                        input.mobile,
                    )
                    || Date.parse(
                        challenge.expiresAt,
                    ) <= Date.now()
                ) {
                    throw new ApiError(
                        'کد تأیید منقضی یا نامعتبر است.',
                        'UNAUTHENTICATED',
                        401,
                    )
                }

                const code = normalizeDigits(
                    input.code,
                ).replace(/\D/g, '')

                if (code !== '123456') {
                    challenge.attempts += 1

                    throw new ApiError(
                        'کد تأیید صحیح نیست.',
                        'VALIDATION_ERROR',
                        422,
                        {
                            fields: {
                                code:
                                    'برای نسخه نمایشی، کد ۱۲۳۴۵۶ را وارد کنید.',
                            },
                        },
                    )
                }

                mockOtpChallenges.delete(
                    input.challengeId,
                )

                return createMockFlow(
                    challenge,
                )
            },
            () => verifyBackendOtp(input),
        )
    },

    completeLogin(
        flowToken,
        password,
    ) {
        return resolveApi(
            () => {
                const flow = getMockFlow(
                    flowToken,
                    'login',
                )

                if (password.length < 8) {
                    throw new ApiError(
                        'رمز عبور صحیح نیست.',
                        'UNAUTHENTICATED',
                        401,
                    )
                }

                mockDb.user.mobile = flow.mobile
                mockDb.user.lastLoginAt = nowIso()
                mockDb.user.mobileVerified = true

                return {
                    access:
                        `mock_access_${createMockId('token')}`,
                    refresh:
                        `mock_refresh_${createMockId('token')}`,
                    user: mockDb.user,
                }
            },
            async () => {
                const response =
                    await api.post<BackendAuthResponse>(
                        '/auth/login/verify-password/',
                        {
                            flow_token: flowToken,
                            password,
                        },
                    )

                return adaptBackendAuthResponse(
                    response,
                )
            },
        )
    },

    completeRegistration(
        flowToken,
        password,
        passwordConfirmation,
    ) {
        return resolveApi(
            () => {
                const flow = getMockFlow(
                    flowToken,
                    'register',
                )

                if (
                    password.length < 8
                    || password !== passwordConfirmation
                ) {
                    throw new ApiError(
                        'رمز عبور معتبر نیست.',
                        'VALIDATION_ERROR',
                        422,
                    )
                }

                mockDb.user.mobile = flow.mobile
                mockDb.user.mobileVerified = true
                mockDb.user.lastLoginAt = nowIso()

                return {
                    access:
                        `mock_access_${createMockId('token')}`,
                    refresh:
                        `mock_refresh_${createMockId('token')}`,
                    user: mockDb.user,
                }
            },
            async () => {
                const response =
                    await api.post<BackendAuthResponse>(
                        '/auth/register/set-password/',
                        {
                            flow_token: flowToken,
                            password,
                            confirm_password:
                            passwordConfirmation,
                        },
                    )

                return adaptBackendAuthResponse(
                    response,
                )
            },
        )
    },

    verifyPasswordResetOtp(input) {
        return resolveApi(
            async () => {
                const flow =
                    await authService.verifyOtp(
                        input,
                    )

                return {
                    mobile: normalizeMobile(
                        input.mobile,
                    ),
                    flowToken: flow.flowToken,
                    expiresAt: flow.expiresAt,
                }
            },
            async () => {
                const flow =
                    await verifyBackendOtp(input)

                return {
                    mobile: normalizeMobile(
                        input.mobile,
                    ),
                    flowToken: flow.flowToken,
                    expiresAt: flow.expiresAt,
                }
            },
        )
    },

    resetPassword(input) {
        return resolveApi(
            () => {
                const flow =
                    getMockFlow(
                        input.flowToken,
                        'reset_password',
                    )

                if (
                    input.password.length < 8
                    || input.password
                    !== input.passwordConfirmation
                ) {
                    throw new ApiError(
                        'رمز عبور جدید معتبر نیست.',
                        'VALIDATION_ERROR',
                        422,
                    )
                }

                mockFlows.delete(
                    input.flowToken,
                )

                mockDb.user.mobile = flow.mobile
            },
            async () => {
                await api.post(
                    '/auth/reset-password/',
                    {
                        flow_token: input.flowToken,
                        password: input.password,
                        confirm_password:
                        input.passwordConfirmation,
                    },
                )
            },
        )
    },

    getCurrentUser() {
        return resolveApi(
            () => mockDb.user,
            async () => {
                const response =
                    await api.get<BackendUser>(
                        '/auth/me/',
                    )

                return adaptBackendUser(
                    response,
                )
            },
        )
    },

    logout(refreshToken) {
        return resolveApi(
            () => {
                mockFlows.clear()
            },
            async () => {
                await api.post(
                    '/auth/logout/',
                    {
                        refresh: refreshToken,
                    },
                )
            },
        )
    },
}

export default authService