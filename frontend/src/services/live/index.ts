import type {
    ActiveSession,
    AddBankAccountInput,
    AssetNetwork,
    AssetSymbol,
    AuthFlowResult,
    AuthResult,
    BankAccount,
    BasicIdentityInput,
    CreateOrderInput,
    CreateTicketInput,
    CryptoWithdrawalDraft,
    CryptoWithdrawalEstimate,
    CryptoWithdrawalInput,
    DashboardSummary,
    DepositAddress,
    FaqItem,
    IranianBank,
    LoginInput,
    MarketAsset,
    MarketListParams,
    NotificationFilters,
    NotificationItem,
    OrderFilters,
    OtcOrder,
    OtpChallenge,
    PaginatedResult,
    PasswordResetProof,
    PricePoint,
    QuoteRequest,
    RegisterInput,
    RequestOtpInput,
    ResetPasswordInput,
    SecurityEvent,
    SecurityOverview,
    SupportCategory,
    SupportTicket,
    TicketFilters,
    TicketMessage,
    TomanDepositInput,
    TomanDepositResult,
    TomanWithdrawalDraft,
    TomanWithdrawalInput,
    TradeQuote,
    Transaction,
    TransactionFilters,
    TwoFactorSetup,
    UpdateProfileInput,
    UserPreferences,
    UserProfile,
    VerificationStepId,
    VerificationSubmission,
    VerificationSummary,
    VerifyOtpInput,
    WalletAsset,
    WalletSummary,
    WithdrawalEstimate,
    WithdrawalOtpChallenge,
} from '@/types'
import {normalizeDigits} from '@/utils/formatters'
import {api, ApiError} from '../api'
import type {AuthService} from '../auth.service'
import type {BankService} from '../bank.service'
import type {MarketService} from '../market.service'
import type {NotificationService} from '../notification.service'
import type {OrderService} from '../order.service'
import type {ChangePasswordInput, SecurityService} from '../security.service'
import type {SupportService} from '../support.service'
import type {TradeService} from '../trade.service'
import type {TransactionService} from '../transaction.service'
import type {UserService} from '../user.service'
import type {VerificationService} from '../verification.service'
import type {WalletService} from '../wallet.service'

// Production services live behind a build-only alias in vite.config.ts. Keeping
// this module free of imports from services/mock guarantees that demo state,
// identities, addresses and fixed OTP/TOTP values cannot enter release chunks.

export {ApiError, isMockApiEnabled} from '../api'
export type {
    AuthService,
    BankService,
    ChangePasswordInput,
    MarketService,
    NotificationService,
    OrderService,
    SecurityService,
    SupportService,
    TradeService,
    TransactionService,
    UserService,
    VerificationService,
    WalletService,
}

export const authService: AuthService = {
    login: (input: LoginInput) =>
        api.post<OtpChallenge>('/auth/request-login-otp/', {
            phone_number: normalizeDigits(input.mobile),
        }),

    completeLogin: (flowToken: string, password: string) =>
        api.post<AuthResult>('/auth/login/verify-password/', {
            flow_token: flowToken,
            password,
        }),

    register: (input: RegisterInput) =>
        api.post<OtpChallenge>('/auth/request-registration-otp/', {
            phone_number: normalizeDigits(input.mobile),
        }),

    completeRegistration: (
        flowToken: string,
        password: string,
        passwordConfirmation: string,
    ) =>
        api.post<AuthResult>('/auth/register/set-password/', {
            flow_token: flowToken,
            password,
            confirm_password: passwordConfirmation,
        }),

    requestOtp: (input: RequestOtpInput) => api.post<OtpChallenge>('/auth/otp', input),

    verifyOtp: (input: VerifyOtpInput) =>
        api.post<AuthFlowResult>('/auth/verify-otp/', {
            challenge_id: input.challengeId,
            otp: normalizeDigits(input.code).replace(/\D/g, ''),
        }),

    verifyPasswordResetOtp: (input: VerifyOtpInput) =>
        api.post<PasswordResetProof>('/auth/password/verify', input),

    resetPassword: (input: ResetPasswordInput) => api.post<void>('/auth/reset-password/', input),

    getCurrentUser: () => api.get<UserProfile>('/auth/me/'),

    logout: (refreshToken: string) =>
        api.post<void>('/auth/logout/', {refresh: refreshToken}),
}

export const bankService: BankService = {
    listBanks: () => api.get<IranianBank[]>('/banks'),
    listAccounts: () => api.get<BankAccount[]>('/bank-accounts'),
    detectBank(cardNumber: string) {
        const bin = normalizeDigits(cardNumber).replace(/\D/g, '').slice(0, 6)
        return api.post<IranianBank | null>('/banks/detect', {bin})
    },
    addAccount: (input: AddBankAccountInput) => api.post<BankAccount>('/bank-accounts', input),
    setPreferred: (id: string) => api.post<BankAccount>(`/bank-accounts/${id}/preferred`),
    removeAccount: (id: string) => api.delete<void>(`/bank-accounts/${id}`),
}

export const marketService: MarketService = {
    list(params: MarketListParams = {}) {
        return api.get<MarketAsset[]>('/markets', {
            query: {
                search: params.search,
                favoritesOnly: params.favoritesOnly,
                sortBy: params.sortBy,
                sortDirection: params.sortDirection,
                favorites: params.favorites,
            },
        })
    },
    getBySymbol: (symbol: AssetSymbol) => api.get<MarketAsset>(`/markets/${symbol}`),
    getPriceHistory: (symbol: AssetSymbol, period: '24h' | '7d' | '30d' = '24h') =>
        api.get<PricePoint[]>(`/markets/${symbol}/history`, {query: {period}}),
}

export const notificationService: NotificationService = {
    list(filters: NotificationFilters = {}) {
        return api.get<PaginatedResult<NotificationItem>>('/notifications', {
            query: {
                page: filters.page,
                pageSize: filters.pageSize,
                category: filters.category,
                read: filters.read,
            },
        })
    },
    getUnreadCount: () => api.get<number>('/notifications/unread-count'),
    markAsRead: (id: string) => api.patch<NotificationItem>(`/notifications/${id}`, {read: true}),
    markAllAsRead: () => api.post<void>('/notifications/read-all'),
    remove: (id: string) => api.delete<void>(`/notifications/${id}`),
}

export const orderService: OrderService = {
    list(filters: OrderFilters = {}) {
        return api.get<PaginatedResult<OtcOrder>>('/orders', {
            query: {
                page: filters.page,
                pageSize: filters.pageSize,
                side: filters.side,
                status: filters.status,
                asset: filters.assetSymbol,
                search: filters.search,
            },
        })
    },
    getById: (id: string) => api.get<OtcOrder>(`/orders/${id}`),
    cancel: (id: string) => api.post<OtcOrder>(`/orders/${id}/cancel`),
}

export const securityService: SecurityService = {
    getOverview: () => api.get<SecurityOverview>('/security'),
    listSessions: () => api.get<ActiveSession[]>('/security/sessions'),
    revokeSession: (id: string) => api.delete<void>(`/security/sessions/${id}`),
    revokeOtherSessions: () => api.delete<void>('/security/sessions/others'),
    listEvents: () => api.get<SecurityEvent[]>('/security/events'),
    changePassword: (input: ChangePasswordInput) => api.post<void>('/security/password', input),
    startTwoFactorSetup: () => api.post<TwoFactorSetup>('/security/two-factor/setup'),
    setTwoFactor: (enabled: boolean, code?: string, setupToken?: string) =>
        api.patch<SecurityOverview>('/security/two-factor', {enabled, code, setupToken}),
    setAntiPhishingCode: (code: string | null) =>
        api.patch<SecurityOverview>('/security/anti-phishing', {code}),
    setWithdrawalWhitelist: (enabled: boolean) =>
        api.patch<SecurityOverview>('/security/withdrawal-whitelist', {enabled}),
}

export const supportService: SupportService = {
    listFaqs: (search?: string, category?: SupportCategory) =>
        api.get<FaqItem[]>('/support/faqs', {query: {search, category}}),
    listTickets(filters: TicketFilters = {}) {
        return api.get<PaginatedResult<SupportTicket>>('/support/tickets', {
            query: {
                page: filters.page,
                pageSize: filters.pageSize,
                status: filters.status,
                category: filters.category,
                search: filters.search,
            },
        })
    },
    getTicket: (id: string) => api.get<SupportTicket>(`/support/tickets/${id}`),
    createTicket: (input: CreateTicketInput) => api.post<SupportTicket>('/support/tickets', input),
    reply: (ticketId: string, body: string) =>
        api.post<TicketMessage>(`/support/tickets/${ticketId}/messages`, {body}),
    close: (ticketId: string) => api.post<SupportTicket>(`/support/tickets/${ticketId}/close`),
}

export const tradeService: TradeService = {
    getQuote: (input: QuoteRequest, signal?: AbortSignal) =>
        api.post<TradeQuote>('/trade/quotes', input, {signal}),
    getQuoteById: (id: string) => api.get<TradeQuote>(`/trade/quotes/${id}`),
    createOrder(input: CreateOrderInput) {
        if (!input.clientRequestId.trim()) {
            return Promise.reject(new ApiError('شناسه امن درخواست ارسال نشده است.', 'VALIDATION_ERROR', 422))
        }
        return api.post<OtcOrder>('/trade/orders', input, {
            headers: {'Idempotency-Key': input.clientRequestId},
        })
    },
}

export const transactionService: TransactionService = {
    list(filters: TransactionFilters = {}) {
        return api.get<PaginatedResult<Transaction>>('/transactions', {
            query: {
                page: filters.page,
                pageSize: filters.pageSize,
                type: filters.type,
                status: filters.status,
                asset: filters.assetSymbol,
                network: filters.networkCode,
                from: filters.from,
                to: filters.to,
                search: filters.search,
            },
        })
    },
    getById: (id: string) => api.get<Transaction>(`/transactions/${id}`),
}

export const userService: UserService = {
    getProfile: () => api.get<UserProfile>('/users/me'),
    updateProfile: (input: UpdateProfileInput) => api.patch<UserProfile>('/users/me', input),
    getDashboardSummary: () => api.get<DashboardSummary>('/dashboard/summary'),
    getPreferences: () => api.get<UserPreferences>('/users/me/preferences'),
    updatePreferences: (input: Partial<UserPreferences>) =>
        api.patch<UserPreferences>('/users/me/preferences', input),
}

export const verificationService: VerificationService = {
    getSummary: () => api.get<VerificationSummary>('/verification'),
    submitBasicInfo: (input: BasicIdentityInput) =>
        api.post<VerificationSubmission>('/verification/basic-info', input),
    submitStep: (stepId: VerificationStepId, payload: FormData | Record<string, unknown>) =>
        api.post<VerificationSubmission>(`/verification/${stepId}`, payload),
}

export const walletService: WalletService = {
    getSummary: () => api.get<WalletSummary>('/wallet'),
    getAsset: (symbol: AssetSymbol) => api.get<WalletAsset>(`/wallet/${symbol}`),
    getNetworks: (symbol: AssetSymbol) => api.get<AssetNetwork[]>(`/wallet/${symbol}/networks`),
    getDepositAddress: (symbol: AssetSymbol, networkCode: string) =>
        api.get<DepositAddress>(`/wallet/${symbol}/deposit-address`, {query: {network: networkCode}}),
    createTomanDeposit: (input: TomanDepositInput) =>
        api.post<TomanDepositResult>('/wallet/toman/deposits', input),
    getTomanDeposit: (id: string) => api.get<TomanDepositResult>(`/wallet/toman/deposits/${id}`),
    completeTomanDeposit: (id: string) =>
        api.post<Transaction>(`/wallet/toman/deposits/${id}/complete`),
    estimateTomanWithdrawal: (input: TomanWithdrawalDraft) =>
        api.post<WithdrawalEstimate>('/wallet/toman/withdrawals/estimate', input),
    createTomanWithdrawal(input: TomanWithdrawalInput) {
        const {idempotencyKey, ...payload} = input
        return api.post<Transaction>('/wallet/toman/withdrawals', payload, {
            headers: {'Idempotency-Key': idempotencyKey},
        })
    },
    estimateCryptoWithdrawal: (input: CryptoWithdrawalDraft) =>
        api.post<CryptoWithdrawalEstimate>('/wallet/crypto/withdrawals/estimate', input),
    requestCryptoWithdrawalOtp: (estimateToken: string, estimateVersion: number) =>
        api.post<WithdrawalOtpChallenge>('/wallet/crypto/withdrawals/otp-challenges', {
            estimateToken,
            estimateVersion,
            purpose: 'crypto_withdrawal',
        }),
    resendCryptoWithdrawalOtp: (challengeToken: string) =>
        api.post<WithdrawalOtpChallenge>(
            `/wallet/crypto/withdrawals/otp-challenges/${challengeToken}/resend`,
            {purpose: 'crypto_withdrawal'},
        ),
    createCryptoWithdrawal(input: CryptoWithdrawalInput) {
        const {idempotencyKey, ...payload} = input
        return api.post<Transaction>('/wallet/crypto/withdrawals', payload, {
            headers: {'Idempotency-Key': idempotencyKey},
        })
    },
}