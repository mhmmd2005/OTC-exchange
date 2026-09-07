import type {
  AssetNetwork,
  AssetSymbol,
  CryptoWithdrawalDraft,
  CryptoWithdrawalEstimate,
  CryptoWithdrawalInput,
  DepositAddress,
  TomanWithdrawalDraft,
  TomanDepositInput,
  TomanDepositResult,
  TomanWithdrawalInput,
  Transaction,
  WalletAsset,
  WalletSummary,
  WithdrawalOtpChallenge,
  WithdrawalEstimate,
} from '@/types'
import {
  addDecimal,
  calculateQuoteTotal,
  compareDecimal,
  subtractDecimal,
} from '@/utils/decimal'
import { normalizeDigits } from '@/utils/formatters'
import { ApiError, api, resolveApi } from './api'
import { createMockId, futureIso, nowIso } from './mock/helpers'
import { mockDb } from './mock/state'
import { mockAssets } from './mock/data'
import { isMockTwoFactorEnabled } from './security.service'

export interface WalletService {
  getSummary(): Promise<WalletSummary>
  getAsset(symbol: AssetSymbol): Promise<WalletAsset>
  getNetworks(symbol: AssetSymbol): Promise<AssetNetwork[]>
  getDepositAddress(symbol: AssetSymbol, networkCode: string): Promise<DepositAddress>
  createTomanDeposit(input: TomanDepositInput): Promise<TomanDepositResult>
  getTomanDeposit(id: string): Promise<TomanDepositResult>
  completeTomanDeposit(id: string): Promise<Transaction>
  estimateTomanWithdrawal(input: TomanWithdrawalDraft): Promise<WithdrawalEstimate>
  createTomanWithdrawal(input: TomanWithdrawalInput): Promise<Transaction>
  estimateCryptoWithdrawal(input: CryptoWithdrawalDraft): Promise<CryptoWithdrawalEstimate>
  requestCryptoWithdrawalOtp(estimateToken: string, estimateVersion: number): Promise<WithdrawalOtpChallenge>
  resendCryptoWithdrawalOtp(challengeToken: string): Promise<WithdrawalOtpChallenge>
  createCryptoWithdrawal(input: CryptoWithdrawalInput): Promise<Transaction>
}

const mockTomanDepositIntents = new Map<string, TomanDepositResult>()
const withdrawalEstimateVersion = 1

interface MockTomanWithdrawalIntent {
  estimate: WithdrawalEstimate
  consumed: boolean
}

interface MockCryptoWithdrawalIntent {
  estimate: CryptoWithdrawalEstimate
  consumed: boolean
}

interface MockWithdrawalOtpChallenge extends WithdrawalOtpChallenge {
  attempts: number
  sends: number
  rateLimitedUntil?: string
}

interface MockIdempotentTransaction {
  estimateToken: string
  transaction: Transaction
}

const mockTomanWithdrawalIntents = new Map<string, MockTomanWithdrawalIntent>()
const mockCryptoWithdrawalIntents = new Map<string, MockCryptoWithdrawalIntent>()
const mockWithdrawalOtpChallenges = new Map<string, MockWithdrawalOtpChallenge>()
const mockWithdrawalOtpByEstimate = new Map<string, string>()
const mockTomanWithdrawalResults = new Map<string, MockIdempotentTransaction>()
const mockCryptoWithdrawalResults = new Map<string, MockIdempotentTransaction>()

function assertIdempotencyKey(value: string): void {
  if (!/^[A-Za-z0-9_-]{16,128}$/.test(value)) {
    throw new ApiError('شناسه امن درخواست معتبر نیست؛ صفحه را تازه‌سازی و دوباره تلاش کنید.', 'BAD_REQUEST', 400)
  }
}

function assertEstimateActive(expiresAt: string): void {
  if (!Number.isFinite(Date.parse(expiresAt)) || Date.parse(expiresAt) <= Date.now()) {
    throw new ApiError('مهلت برآورد برداشت به پایان رسیده است؛ مبلغ را دوباره بررسی کنید.', 'QUOTE_EXPIRED', 410)
  }
}

function getTomanWithdrawalIntent(token: string, version: number): MockTomanWithdrawalIntent {
  const intent = mockTomanWithdrawalIntents.get(token)
  if (!intent || intent.estimate.estimateVersion !== version) {
    throw new ApiError('برآورد برداشت معتبر نیست؛ دوباره آن را دریافت کنید.', 'BAD_REQUEST', 409)
  }
  assertEstimateActive(intent.estimate.expiresAt)
  if (intent.consumed) throw new ApiError('این درخواست برداشت پیش‌تر ثبت شده است.', 'BAD_REQUEST', 409)
  return intent
}

function getCryptoWithdrawalIntent(token: string, version: number): MockCryptoWithdrawalIntent {
  const intent = mockCryptoWithdrawalIntents.get(token)
  if (!intent || intent.estimate.estimateVersion !== version) {
    throw new ApiError('برآورد برداشت معتبر نیست؛ دوباره آن را دریافت کنید.', 'BAD_REQUEST', 409)
  }
  assertEstimateActive(intent.estimate.expiresAt)
  if (intent.consumed) throw new ApiError('این درخواست برداشت پیش‌تر ثبت شده است.', 'BAD_REQUEST', 409)
  return intent
}

function assertOtpSendAllowed(challenge: MockWithdrawalOtpChallenge): void {
  if (challenge.sends < 5) return
  challenge.rateLimitedUntil ||= futureIso(5 * 60)
  const retryAfterSeconds = Math.max(
    0,
    Math.ceil((Date.parse(challenge.rateLimitedUntil) - Date.now()) / 1_000),
  )
  if (retryAfterSeconds > 0) {
    throw new ApiError('تعداد ارسال کد بیش از حد مجاز است؛ چند دقیقه بعد تلاش کنید.', 'RATE_LIMITED', 429, {
      retryAfterSeconds,
    })
  }
  challenge.sends = 0
  challenge.rateLimitedUntil = undefined
}

function findWalletAsset(symbol: AssetSymbol): WalletAsset {
  const asset = mockDb.wallet.assets.find((item) => item.symbol.toUpperCase() === symbol.toUpperCase())
  if (!asset) throw new ApiError('کیف پول ارز مورد نظر پیدا نشد.', 'NOT_FOUND', 404)
  return asset
}

function findNetwork(symbol: AssetSymbol, networkCode: string): AssetNetwork {
  const network = findWalletAsset(symbol).networks.find(
    (item) => item.code.toUpperCase() === networkCode.toUpperCase(),
  )
  if (!network) throw new ApiError('شبکه انتخاب‌شده برای این ارز در دسترس نیست.', 'NOT_FOUND', 404)
  return network
}

function assertPositiveAmount(amount: string): void {
  if (!amount || compareDecimal(amount, '0') <= 0) {
    throw new ApiError('مبلغ باید بیشتر از صفر باشد.', 'VALIDATION_ERROR', 422, {
      fields: { amount: 'یک مبلغ معتبر وارد کنید.' },
    })
  }
}

const depositAddresses: Record<string, { address: string; memo?: string }> = {
  'USDT:TRC20': { address: 'TYpR7V8xYn6PXJb9s5aJvM3duGsXhQ2Wef' },
  'USDT:ERC20': { address: '0x4c7a9f10e1b4c8a476cab3c2d21a2ec040973e2d' },
  'BTC:BTC': { address: 'bc1q9u8g7a6f5e4d3c2b1x0w9v8t7s6r5q4p3n2m1k' },
  'ETH:ERC20': { address: '0x4c7a9f10e1b4c8a476cab3c2d21a2ec040973e2d' },
  'TRX:TRC20': { address: 'TYpR7V8xYn6PXJb9s5aJvM3duGsXhQ2Wef' },
  'TON:TON': { address: 'UQD0xE9vJ1iLzAp4qQcsNL6-WdRxa3kHh7mV2CjuefQpwH3b', memo: '847201' },
}

export const walletService: WalletService = {
  getSummary() {
    return resolveApi(() => mockDb.wallet, () => api.get<WalletSummary>('/wallet'))
  },

  getAsset(symbol) {
    return resolveApi(() => findWalletAsset(symbol), () => api.get<WalletAsset>(`/wallet/${symbol}`))
  },

  getNetworks(symbol) {
    return resolveApi(() => findWalletAsset(symbol).networks, () =>
      api.get<AssetNetwork[]>(`/wallet/${symbol}/networks`))
  },

  getDepositAddress(symbol, networkCode) {
    return resolveApi(() => {
      const network = findNetwork(symbol, networkCode)
      if (!network.depositEnabled || ['disabled', 'maintenance'].includes(network.status)) {
        throw new ApiError(
          'واریز روی این شبکه موقتاً در دسترس نیست. شبکه دیگری انتخاب کنید.',
          'NETWORK_DISABLED',
          409,
        )
      }
      const destination = depositAddresses[`${symbol.toUpperCase()}:${network.code.toUpperCase()}`]
      if (!destination) throw new ApiError('آدرس واریز آماده نیست. دوباره تلاش کنید.', 'SERVER_ERROR', 503)
      return {
        assetSymbol: symbol,
        networkCode: network.code,
        address: destination.address,
        memo: destination.memo,
        minimumDeposit: network.minimumDeposit,
        requiredConfirmations: network.confirmations,
        createdAt: nowIso(),
      }
    }, () => api.get<DepositAddress>(`/wallet/${symbol}/deposit-address`, {
      query: { network: networkCode },
    }))
  },

  createTomanDeposit(input) {
    return resolveApi(() => {
      assertPositiveAmount(input.amount)
      if (compareDecimal(input.amount, '100000') < 0) {
        throw new ApiError('حداقل مبلغ واریز ۱۰۰ هزار تومان است.', 'BELOW_MINIMUM', 422)
      }
      const remaining = subtractDecimal(
        mockDb.verification.limits.dailyTomanDeposit,
        mockDb.verification.limits.usedTomanDeposit,
      )
      if (compareDecimal(input.amount, remaining) > 0) {
        throw new ApiError('مبلغ از سقف باقی‌مانده واریز امروز بیشتر است.', 'DAILY_LIMIT_EXCEEDED', 409, {
          remaining,
          actionLabel: 'مشاهده سقف‌ها',
          actionRoute: '/app/verification',
        })
      }
      const account = mockDb.bankAccounts.find((item) => item.id === input.bankAccountId)
      if (!account || account.status !== 'verified') {
        throw new ApiError(
          'برای واریز، یک کارت بانکی تأییدشده انتخاب کنید.',
          'BANK_ACCOUNT_REQUIRED',
          409,
          { actionLabel: 'افزودن حساب بانکی', actionRoute: '/app/bank-accounts' },
        )
      }
      const id = createMockId('dep')
      const result = {
        id,
        amount: input.amount,
        paymentUrl: `/mock-payment/${id}`,
        expiresAt: futureIso(10 * 60),
      }
      mockTomanDepositIntents.set(id, result)
      return result
    }, () => api.post<TomanDepositResult>('/wallet/toman/deposits', input))
  },

  getTomanDeposit(id) {
    return resolveApi(() => {
      const intent = mockTomanDepositIntents.get(id)
      if (!intent) throw new ApiError('درخواست پرداخت پیدا نشد یا منقضی شده است.', 'NOT_FOUND', 404)
      return intent
    }, () => api.get<TomanDepositResult>(`/wallet/toman/deposits/${id}`))
  },

  completeTomanDeposit(id) {
    return resolveApi(() => {
      const intent = mockTomanDepositIntents.get(id)
      if (!intent) throw new ApiError('درخواست پرداخت پیدا نشد یا منقضی شده است.', 'NOT_FOUND', 404)
      if (Date.parse(intent.expiresAt) <= Date.now()) {
        mockTomanDepositIntents.delete(id)
        throw new ApiError('مهلت پرداخت به پایان رسیده است؛ یک درگاه تازه بسازید.', 'BAD_REQUEST', 410)
      }
      const amount = intent.amount
      const existing = mockDb.transactions.find(
        (item) => item.type === 'toman_deposit' && item.description?.includes(id),
      )
      if (existing) return existing

      const transaction: Transaction = {
        id: createMockId('txn'),
        referenceNumber: `TRX-${Date.now().toString().slice(-8)}`,
        type: 'toman_deposit',
        status: 'completed',
        assetSymbol: 'IRT',
        amount,
        tomanAmount: amount,
        fee: '0',
        title: 'واریز تومان',
        description: `پرداخت آزمایشی ${id}`,
        createdAt: nowIso(),
        completedAt: nowIso(),
      }
      mockDb.wallet.availableToman = addDecimal(mockDb.wallet.availableToman, amount)
      mockDb.wallet.tomanBalance = addDecimal(mockDb.wallet.tomanBalance, amount)
      mockDb.wallet.totalValueToman = addDecimal(mockDb.wallet.totalValueToman, amount)
      mockDb.verification.limits.usedTomanDeposit = addDecimal(
        mockDb.verification.limits.usedTomanDeposit,
        amount,
      )
      mockDb.transactions.unshift(transaction)
      return transaction
    }, () => api.post<Transaction>(`/wallet/toman/deposits/${id}/complete`))
  },

  estimateTomanWithdrawal(input) {
    return resolveApi(() => {
      const amount = input.amount
      assertPositiveAmount(amount)
      const fee = '6000'
      if (compareDecimal(amount, '50000') < 0) {
        throw new ApiError('حداقل مبلغ برداشت ۵۰ هزار تومان است.', 'BELOW_MINIMUM', 422)
      }
      if (compareDecimal(amount, mockDb.wallet.availableToman) > 0) {
        throw new ApiError(
          'موجودی قابل برداشت تومان کافی نیست.',
          'INSUFFICIENT_TOMAN_BALANCE',
          409,
          { actionLabel: 'واریز تومان', actionRoute: '/app/deposit/toman' },
        )
      }
      const remaining = subtractDecimal(
        mockDb.verification.limits.dailyTomanWithdrawal,
        mockDb.verification.limits.usedTomanWithdrawal,
      )
      if (compareDecimal(amount, remaining) > 0) {
        throw new ApiError('مبلغ از سقف باقی‌مانده برداشت امروز بیشتر است.', 'DAILY_LIMIT_EXCEEDED', 409, {
          remaining,
          actionLabel: 'مشاهده سقف‌ها',
          actionRoute: '/app/verification',
        })
      }
      const account = mockDb.bankAccounts.find((item) => item.id === input.bankAccountId)
      if (!account || account.status !== 'verified') {
        throw new ApiError(
          'برای برداشت تومان ابتدا یک حساب بانکی تأییدشده اضافه کنید.',
          'BANK_ACCOUNT_REQUIRED',
          409,
          { actionLabel: 'افزودن حساب بانکی', actionRoute: '/app/bank-accounts' },
        )
      }
      const estimate: WithdrawalEstimate = {
        estimateToken: createMockId('twd_est'),
        estimateVersion: withdrawalEstimateVersion,
        expiresAt: futureIso(5 * 60),
        amount,
        bankAccountId: account.id,
        fee,
        receivable: subtractDecimal(amount, fee),
        estimatedSettlement: 'اولین چرخه پایای روز کاری بعد',
      }
      mockTomanWithdrawalIntents.set(estimate.estimateToken, { estimate, consumed: false })
      return estimate
    }, () => api.post<WithdrawalEstimate>('/wallet/toman/withdrawals/estimate', input))
  },

  createTomanWithdrawal(input) {
    return resolveApi(() => {
      assertIdempotencyKey(input.idempotencyKey)
      const previous = mockTomanWithdrawalResults.get(input.idempotencyKey)
      if (previous) {
        if (previous.estimateToken !== input.estimateToken) {
          throw new ApiError('شناسه درخواست برای برآورد دیگری استفاده شده است.', 'BAD_REQUEST', 409)
        }
        return previous.transaction
      }

      const intent = getTomanWithdrawalIntent(input.estimateToken, input.estimateVersion)
      const { estimate } = intent
      const account = mockDb.bankAccounts.find((item) => item.id === estimate.bankAccountId)
      if (!account || account.status !== 'verified') {
        throw new ApiError(
          'حساب مقصد دیگر قابل استفاده نیست؛ حساب دیگری انتخاب کنید.',
          'BANK_ACCOUNT_REQUIRED',
          409,
          { actionLabel: 'مدیریت حساب‌ها', actionRoute: '/app/bank-accounts' },
        )
      }
      if (compareDecimal(estimate.amount, mockDb.wallet.availableToman) > 0) {
        throw new ApiError('موجودی قابل برداشت تومان کافی نیست.', 'INSUFFICIENT_TOMAN_BALANCE', 409)
      }
      const remaining = subtractDecimal(
        mockDb.verification.limits.dailyTomanWithdrawal,
        mockDb.verification.limits.usedTomanWithdrawal,
      )
      if (compareDecimal(estimate.amount, remaining) > 0) {
        throw new ApiError('سقف باقی‌مانده برداشت امروز تغییر کرده است.', 'DAILY_LIMIT_EXCEEDED', 409)
      }

      const transaction: Transaction = {
        id: createMockId('txn'),
        referenceNumber: `TRX-${Date.now().toString().slice(-8)}`,
        type: 'toman_withdrawal',
        status: 'pending',
        assetSymbol: 'IRT',
        amount: estimate.amount,
        tomanAmount: estimate.receivable,
        fee: estimate.fee,
        bankAccountId: account.id,
        title: 'برداشت تومان',
        description: `تسویه به ${account.bank.nameFa}`,
        createdAt: nowIso(),
      }
      mockDb.wallet.availableToman = subtractDecimal(mockDb.wallet.availableToman, estimate.amount)
      mockDb.wallet.lockedToman = addDecimal(mockDb.wallet.lockedToman, estimate.amount)
      mockDb.verification.limits.usedTomanWithdrawal = addDecimal(
        mockDb.verification.limits.usedTomanWithdrawal,
        estimate.amount,
      )
      intent.consumed = true
      mockTomanWithdrawalResults.set(input.idempotencyKey, {
        estimateToken: estimate.estimateToken,
        transaction,
      })
      mockDb.transactions.unshift(transaction)
      return transaction
    }, () => {
      const { idempotencyKey, ...payload } = input
      return api.post<Transaction>('/wallet/toman/withdrawals', payload, {
        headers: { 'Idempotency-Key': idempotencyKey },
      })
    })
  },

  estimateCryptoWithdrawal(input) {
    return resolveApi(() => {
      assertPositiveAmount(input.amount)
      const asset = findWalletAsset(input.assetSymbol)
      const network = findNetwork(input.assetSymbol, input.networkCode)
      if (mockDb.user.kycStatus !== 'verified') {
        throw new ApiError(
          'برای برداشت رمزارز باید احراز هویت سطح دو را تکمیل کنید.',
          'KYC_REQUIRED',
          403,
          { actionLabel: 'تکمیل احراز هویت', actionRoute: '/app/verification' },
        )
      }
      if (!asset.withdrawalEnabled || !network.withdrawalEnabled || network.status !== 'active') {
        throw new ApiError(
          'برداشت روی این شبکه موقتاً در دسترس نیست. شبکه دیگری انتخاب کنید.',
          'NETWORK_DISABLED',
          409,
        )
      }
      if (compareDecimal(input.amount, network.minimumWithdrawal) < 0) {
        throw new ApiError(
          `مبلغ برداشت از حداقل مجاز ${network.minimumWithdrawal} ${asset.symbol} کمتر است.`,
          'BELOW_MINIMUM',
          422,
        )
      }
      if (compareDecimal(input.amount, asset.available) > 0) {
        throw new ApiError('موجودی رمزارز کافی نیست.', 'INSUFFICIENT_CRYPTO_BALANCE', 409)
      }
      const market = mockAssets.find((item) => item.symbol === input.assetSymbol)
      if (!market) throw new ApiError('نرخ معادل تومان این دارایی در دسترس نیست.', 'NOT_FOUND', 404)
      const tomanEquivalent = calculateQuoteTotal(input.amount, market.sellPriceToman)
      const dailyRemaining = subtractDecimal(
        mockDb.verification.limits.dailyCryptoWithdrawalTomanEquivalent,
        mockDb.verification.limits.usedCryptoWithdrawalTomanEquivalent,
      )
      if (compareDecimal(tomanEquivalent, dailyRemaining) > 0) {
        throw new ApiError('مبلغ از سقف باقی‌مانده برداشت رمزارز امروز بیشتر است.', 'DAILY_LIMIT_EXCEEDED', 409, {
          remaining: dailyRemaining,
          actionLabel: 'مشاهده سقف‌ها',
          actionRoute: '/app/verification',
        })
      }
      if (!input.address.trim()
        || (network.addressRegex && !new RegExp(network.addressRegex).test(input.address.trim()))) {
        throw new ApiError('آدرس مقصد با شبکه انتخاب‌شده سازگار نیست.', 'VALIDATION_ERROR', 422, {
          fields: { address: 'آدرس کیف پول را دوباره بررسی کنید.' },
        })
      }
      if (network.memoRequired && !input.memo?.trim()) {
        throw new ApiError('ممو یا تگ مقصد برای این شبکه الزامی است.', 'VALIDATION_ERROR', 422, {
          fields: { memo: 'ممو یا تگ مقصد را وارد کنید.' },
        })
      }
      const address = input.address.trim()
      const memo = input.memo?.trim() || undefined
      const estimate: CryptoWithdrawalEstimate = {
        estimateToken: createMockId('cwd_est'),
        estimateVersion: withdrawalEstimateVersion,
        expiresAt: futureIso(5 * 60),
        assetSymbol: input.assetSymbol,
        networkCode: network.code,
        address,
        memo,
        amount: input.amount,
        tomanEquivalent,
        fee: network.withdrawalFee,
        receivable: subtractDecimal(input.amount, network.withdrawalFee),
        estimatedArrivalMinutes: network.estimatedArrivalMinutes,
      }
      mockCryptoWithdrawalIntents.set(estimate.estimateToken, { estimate, consumed: false })
      return estimate
    }, () => api.post<CryptoWithdrawalEstimate>('/wallet/crypto/withdrawals/estimate', input))
  },

  requestCryptoWithdrawalOtp(estimateToken, estimateVersion) {
    return resolveApi(() => {
      getCryptoWithdrawalIntent(estimateToken, estimateVersion)
      const previousToken = mockWithdrawalOtpByEstimate.get(estimateToken)
      const previous = previousToken ? mockWithdrawalOtpChallenges.get(previousToken) : undefined
      if (previous && Date.parse(previous.expiresAt) > Date.now()) return previous
      if (previous) {
        assertOtpSendAllowed(previous)
        previous.expiresAt = futureIso(2 * 60)
        previous.resendAvailableAt = futureIso(30)
        previous.attempts = 0
        previous.sends += 1
        return previous
      }

      const challenge: MockWithdrawalOtpChallenge = {
        challengeToken: createMockId('cwd_otp'),
        purpose: 'crypto_withdrawal',
        estimateToken,
        estimateVersion,
        destinationHint: `${mockDb.user.mobile.slice(0, 4)}***${mockDb.user.mobile.slice(-4)}`,
        expiresAt: futureIso(2 * 60),
        resendAvailableAt: futureIso(30),
        attempts: 0,
        sends: 1,
      }
      mockWithdrawalOtpChallenges.set(challenge.challengeToken, challenge)
      mockWithdrawalOtpByEstimate.set(estimateToken, challenge.challengeToken)
      return challenge
    }, () => api.post<WithdrawalOtpChallenge>('/wallet/crypto/withdrawals/otp-challenges', {
      estimateToken,
      estimateVersion,
      purpose: 'crypto_withdrawal',
    }))
  },

  resendCryptoWithdrawalOtp(challengeToken) {
    return resolveApi(() => {
      const challenge = mockWithdrawalOtpChallenges.get(challengeToken)
      if (!challenge || challenge.purpose !== 'crypto_withdrawal') {
        throw new ApiError('درخواست کد برداشت معتبر نیست؛ دوباره از مرحله بررسی ادامه دهید.', 'BAD_REQUEST', 404)
      }
      getCryptoWithdrawalIntent(challenge.estimateToken, challenge.estimateVersion)
      const retryAfterSeconds = Math.max(0, Math.ceil((Date.parse(challenge.resendAvailableAt) - Date.now()) / 1_000))
      if (retryAfterSeconds > 0) {
        throw new ApiError('برای ارسال دوباره کد کمی صبر کنید.', 'RATE_LIMITED', 429, { retryAfterSeconds })
      }
      assertOtpSendAllowed(challenge)
      challenge.expiresAt = futureIso(2 * 60)
      challenge.resendAvailableAt = futureIso(30)
      challenge.attempts = 0
      challenge.sends += 1
      return challenge
    }, () => api.post<WithdrawalOtpChallenge>(
      `/wallet/crypto/withdrawals/otp-challenges/${challengeToken}/resend`,
      { purpose: 'crypto_withdrawal' },
    ))
  },

  createCryptoWithdrawal(input) {
    return resolveApi(() => {
      assertIdempotencyKey(input.idempotencyKey)
      const previous = mockCryptoWithdrawalResults.get(input.idempotencyKey)
      if (previous) {
        if (previous.estimateToken !== input.estimateToken) {
          throw new ApiError('شناسه درخواست برای برآورد دیگری استفاده شده است.', 'BAD_REQUEST', 409)
        }
        return previous.transaction
      }

      const intent = getCryptoWithdrawalIntent(input.estimateToken, input.estimateVersion)
      const challenge = mockWithdrawalOtpChallenges.get(input.otpChallengeToken)
      if (!challenge
        || challenge.purpose !== 'crypto_withdrawal'
        || challenge.estimateToken !== input.estimateToken
        || challenge.estimateVersion !== input.estimateVersion) {
        throw new ApiError('کد تأیید به این برداشت تعلق ندارد؛ کد تازه‌ای دریافت کنید.', 'VALIDATION_ERROR', 422, {
          fields: { otp: 'کد تأیید این برداشت معتبر نیست.' },
        })
      }
      if (Date.parse(challenge.expiresAt) <= Date.now()) {
        throw new ApiError('مهلت کد تأیید به پایان رسیده است؛ کد تازه‌ای دریافت کنید.', 'VALIDATION_ERROR', 410, {
          fields: { otp: 'کد تأیید منقضی شده است.' },
        })
      }
      if (challenge.attempts >= 5) {
        throw new ApiError('تعداد تلاش‌های ناموفق بیش از حد مجاز است؛ کد تازه‌ای دریافت کنید.', 'RATE_LIMITED', 429, {
          fields: { otp: 'این کد به دلیل تلاش‌های ناموفق قفل شده است.' },
        })
      }
      if (normalizeDigits(input.otp).replace(/\D/g, '') !== '123456') {
        challenge.attempts += 1
        throw new ApiError('کد تأیید برداشت صحیح نیست.', 'VALIDATION_ERROR', 422, {
          fields: { otp: 'برای نسخه نمایشی، کد ۱۲۳۴۵۶ را وارد کنید.' },
        })
      }
      if (isMockTwoFactorEnabled() && !input.twoFactorCode) {
        throw new ApiError('کد برنامه تأییدکننده برای این حساب الزامی است.', 'VALIDATION_ERROR', 422, {
          fields: { twoFactorCode: 'کد شش‌رقمی برنامه را وارد کنید.' },
        })
      }
      if (isMockTwoFactorEnabled()
        && normalizeDigits(input.twoFactorCode ?? '').replace(/\D/g, '') !== '123456') {
        throw new ApiError('کد برنامه تأییدکننده صحیح نیست.', 'VALIDATION_ERROR', 422, {
          fields: { twoFactorCode: 'کد شش‌رقمی برنامه را دوباره بررسی کنید.' },
        })
      }

      const { estimate } = intent
      const asset = findWalletAsset(estimate.assetSymbol)
      const network = findNetwork(estimate.assetSymbol, estimate.networkCode)
      if (mockDb.user.kycStatus !== 'verified') {
        throw new ApiError('وضعیت احراز هویت تغییر کرده است.', 'KYC_REQUIRED', 403)
      }
      if (!asset.withdrawalEnabled || !network.withdrawalEnabled || network.status !== 'active') {
        throw new ApiError('برداشت روی این شبکه دیگر در دسترس نیست.', 'NETWORK_DISABLED', 409)
      }
      if (compareDecimal(estimate.amount, asset.available) > 0) {
        throw new ApiError('موجودی رمزارز کافی نیست.', 'INSUFFICIENT_CRYPTO_BALANCE', 409)
      }
      const dailyRemaining = subtractDecimal(
        mockDb.verification.limits.dailyCryptoWithdrawalTomanEquivalent,
        mockDb.verification.limits.usedCryptoWithdrawalTomanEquivalent,
      )
      if (compareDecimal(estimate.tomanEquivalent, dailyRemaining) > 0) {
        throw new ApiError('سقف باقی‌مانده برداشت رمزارز امروز تغییر کرده است.', 'DAILY_LIMIT_EXCEEDED', 409)
      }

      const transaction: Transaction = {
        id: createMockId('txn'),
        referenceNumber: `TRX-${Date.now().toString().slice(-8)}`,
        type: 'crypto_withdrawal',
        status: 'pending',
        assetSymbol: estimate.assetSymbol,
        amount: estimate.amount,
        fee: estimate.fee,
        networkCode: estimate.networkCode,
        address: estimate.address,
        confirmations: 0,
        requiredConfirmations: network.confirmations,
        title: `برداشت ${asset.nameFa}`,
        description: `در انتظار بررسی امنیتی روی شبکه ${estimate.networkCode}`,
        createdAt: nowIso(),
      }
      asset.available = subtractDecimal(asset.available, estimate.amount)
      asset.locked = addDecimal(asset.locked, estimate.amount)
      mockDb.verification.limits.usedCryptoWithdrawalTomanEquivalent = addDecimal(
        mockDb.verification.limits.usedCryptoWithdrawalTomanEquivalent,
        estimate.tomanEquivalent,
      )
      intent.consumed = true
      mockCryptoWithdrawalResults.set(input.idempotencyKey, {
        estimateToken: estimate.estimateToken,
        transaction,
      })
      mockDb.transactions.unshift(transaction)
      mockDb.securityEvents.unshift({
        id: createMockId('sec'),
        type: 'withdrawal_confirmed',
        title: 'برداشت رمزارز تأیید شد',
        description: `برداشت ${estimate.amount} ${estimate.assetSymbol} با تأیید پیامکی ثبت شد.`,
        ipAddress: '185.44.***.***',
        deviceName: 'دستگاه فعلی',
        createdAt: nowIso(),
      })
      return transaction
    }, () => {
      const { idempotencyKey, ...payload } = input
      return api.post<Transaction>('/wallet/crypto/withdrawals', payload, {
        headers: { 'Idempotency-Key': idempotencyKey },
      })
    })
  },
}

export default walletService
