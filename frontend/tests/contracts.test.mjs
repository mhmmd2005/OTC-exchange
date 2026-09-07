import assert from 'node:assert/strict'
import { after, before, test } from 'node:test'
import { readFile } from 'node:fs/promises'
import { createServer } from 'vite'

let server
let authService
let tradeService
let walletService
let marketService
let mockDb
let resetMockDatabase
let legalDocuments
let financial
let portfolio
let persianDates
let apiRequest
let authUtils

before(async () => {
  server = await createServer({
    appType: 'custom',
    logLevel: 'silent',
    server: { middlewareMode: true },
  })

  const [auth, trade, wallet, market, state, legal, money, portfolioMath, dates, api, authHelpers] = await Promise.all([
    server.ssrLoadModule('/src/services/auth.service.ts'),
    server.ssrLoadModule('/src/services/trade.service.ts'),
    server.ssrLoadModule('/src/services/wallet.service.ts'),
    server.ssrLoadModule('/src/services/market.service.ts'),
    server.ssrLoadModule('/src/services/mock/state.ts'),
    server.ssrLoadModule('/src/constants/legal.ts'),
    server.ssrLoadModule('/src/utils/financial.ts'),
    server.ssrLoadModule('/src/utils/portfolio.ts'),
    server.ssrLoadModule('/src/utils/persianDateInput.ts'),
    server.ssrLoadModule('/src/services/api.ts'),
    server.ssrLoadModule('/src/pages/auth/auth.utils.ts'),
  ])

  assert.equal(api.isMockApiEnabled, true, 'contract tests require the explicit development mock flag')
  authService = auth.authService
  tradeService = trade.tradeService
  walletService = wallet.walletService
  marketService = market.marketService
  mockDb = state.mockDb
  resetMockDatabase = state.resetMockDatabase
  legalDocuments = legal.LEGAL_DOCUMENTS
  financial = money
  portfolio = portfolioMath
  persianDates = dates
  apiRequest = api.request
  authUtils = authHelpers
})

after(async () => {
  await server.close()
})

test('decimal math stays exact and accepts Persian financial input', () => {
  assert.equal(financial.multiplyDecimal('0.1', '0.2'), '0.02')
  assert.equal(
    financial.addDecimal('900719925474099312345678.9', '0.1'),
    '900719925474099312345679',
  )
  assert.equal(financial.parseFinancialInput('۱۲۳٬۴۵۶٫۷۸ تومان'), '123456.78')
  assert.equal(financial.roundDecimal('2.5', 0, 'half-even'), '2')
  assert.equal(financial.roundDecimal('3.5', 0, 'half-even'), '4')
  assert.equal(financial.calculatePercentageAmount('50000000', '0.15', 0), '75000')
})

test('portfolio history aligns service samples and values holdings without float drift', () => {
  const timestamp = (day) => `2026-08-${String(day).padStart(2, '0')}T09:42:00.000Z`
  const result = portfolio.buildPortfolioValueHistory('1000', [
    {
      total: '0.1',
      points: [
        { timestamp: timestamp(29), priceToman: '100' },
        { timestamp: timestamp(30), priceToman: '200' },
        { timestamp: timestamp(31), priceToman: '300' },
      ],
    },
    {
      total: '2',
      points: [
        { timestamp: timestamp(30), priceToman: '5' },
        { timestamp: timestamp(31), priceToman: '10' },
      ],
    },
  ])

  assert.deepEqual(result, [
    { timestamp: timestamp(30), valueToman: '1030' },
    { timestamp: timestamp(31), valueToman: '1050' },
  ])
})

test('development market history is deterministic and respects supported ranges', async () => {
  const [asset, day, week, month] = await Promise.all([
    marketService.getBySymbol('BTC'),
    marketService.getPriceHistory('BTC', '24h'),
    marketService.getPriceHistory('BTC', '7d'),
    marketService.getPriceHistory('BTC', '30d'),
  ])

  assert.equal(day.length, 25)
  assert.equal(week.length, 29)
  assert.equal(month.length, 31)
  assert.equal(day.at(-1).priceToman, asset.sellPriceToman)
  assert.equal(week.at(-1).priceToman, asset.sellPriceToman)
  assert.equal(month.at(-1).priceToman, asset.sellPriceToman)
  assert.equal(Date.parse(week.at(-1).timestamp) - Date.parse(week[0].timestamp), 7 * 24 * 60 * 60 * 1_000)
  assert.deepEqual(week, await marketService.getPriceHistory('BTC', '7d'))
})

test('Persian date filters use inclusive Tehran day boundaries', () => {
  assert.equal(
    persianDates.persianDateBoundaryIso('۱۴۰۵/۰۶/۰۹', 'start'),
    '2026-08-30T20:30:00.000Z',
  )
  assert.equal(
    persianDates.persianDateBoundaryIso('1405-06-09', 'end'),
    '2026-08-31T20:29:59.999Z',
  )
  assert.equal(persianDates.persianDateBoundaryIso('۱۴۰۵/۱۳/۰۱', 'start'), null)
})

test('API transport is cookie-only and rejects an HTML SPA fallback', async () => {
  const originalFetch = globalThis.fetch
  let capturedRequest
  try {
    globalThis.fetch = async (url, init) => {
      capturedRequest = { url, init }
      return new Response(JSON.stringify({ data: { ok: true } }), {
        status: 200,
        headers: { 'content-type': 'application/json' },
      })
    }
    assert.deepEqual(await apiRequest('/transport-contract'), { ok: true })
    assert.equal(capturedRequest.init.credentials, 'include')
    assert.equal(new Headers(capturedRequest.init.headers).has('Authorization'), false)

    globalThis.fetch = async () => new Response('<!doctype html><title>SPA</title>', {
      status: 200,
      headers: { 'content-type': 'text/html' },
    })
    await assert.rejects(
      apiRequest('/users/me'),
      (error) => error?.code === 'SERVER_ERROR' && error?.status === 502,
    )
  } finally {
    globalThis.fetch = originalFetch
  }
})

test('registration OTP is challenge-bound, single-use, and cookie-auth shaped', async () => {
  resetMockDatabase()
  const mobile = '09121112233'
  const challenge = await authService.register({
    mobile,
    password: 'A-secure-password-123',
    passwordConfirmation: 'A-secure-password-123',
    acceptedTerms: true,
    termsVersion: legalDocuments.terms.version,
    privacyVersion: legalDocuments.privacy.version,
    acceptedAt: new Date().toISOString(),
  })

  await assert.rejects(
    authService.verifyOtp({
      mobile,
      purpose: 'register',
      challengeId: 'otp_not_the_issued_challenge',
      code: '123456',
    }),
    (error) => error?.code === 'UNAUTHENTICATED',
  )

  const result = await authService.verifyOtp({
    mobile,
    purpose: 'register',
    challengeId: challenge.challengeId,
    code: '۱۲۳۴۵۶',
  })
  assert.deepEqual(Object.keys(result), ['user'])
  assert.equal(result.user.mobileVerified, true)

  await assert.rejects(
    authService.verifyOtp({
      mobile,
      purpose: 'register',
      challengeId: challenge.challengeId,
      code: '123456',
    }),
    (error) => error?.code === 'UNAUTHENTICATED',
  )
})

test('KYC mobile confirmation reuses the established challenge-bound auth OTP contract', async () => {
  resetMockDatabase()
  const mobileStep = mockDb.verification.steps.find((step) => step.id === 'mobile')
  assert.ok(mobileStep)
  mobileStep.status = 'not_started'
  delete mobileStep.completedAt
  mockDb.verification.status = 'not_started'
  mockDb.user.kycStatus = 'not_started'
  mockDb.user.mobileVerified = false

  const challenge = await authService.requestOtp({ mobile: mockDb.user.mobile, purpose: 'login' })
  assert.equal(challenge.purpose, 'login')
  assert.equal(challenge.mobile, mockDb.user.mobile)

  await assert.rejects(
    authService.verifyOtp({
      mobile: mockDb.user.mobile,
      purpose: 'login',
      challengeId: 'otp_not_the_issued_challenge',
      code: '123456',
    }),
    (error) => error?.code === 'UNAUTHENTICATED',
  )

  const result = await authService.verifyOtp({
    mobile: mockDb.user.mobile,
    purpose: 'login',
    challengeId: challenge.challengeId,
    code: '۱۲۳۴۵۶',
  })
  assert.equal(mobileStep.status, 'verified')
  assert.equal(result.user.mobileVerified, true)

  await assert.rejects(
    authService.verifyOtp({
      mobile: mockDb.user.mobile,
      purpose: 'login',
      challengeId: challenge.challengeId,
      code: '123456',
    }),
    (error) => error?.code === 'UNAUTHENTICATED',
  )
})

test('auth return paths stay inside the authenticated application shell', () => {
  assert.equal(authUtils.safeAppRedirect('/app/verification?step=mobile'), '/app/verification?step=mobile')
  assert.equal(authUtils.safeAppRedirect('/app/dashboard#ready'), '/app/dashboard#ready')
  assert.equal(authUtils.safeAppRedirect('https://attacker.example/steal'), '/app/dashboard')
  assert.equal(authUtils.safeAppRedirect('//attacker.example/steal'), '/app/dashboard')
  assert.equal(authUtils.safeAppRedirect('/app//attacker.example/steal'), '/app/dashboard')
  assert.equal(authUtils.safeAppRedirect('/app\\attacker.example/steal'), '/app/dashboard')
})

test('password reset proof is single-use and cannot reset with mismatched passwords', async () => {
  resetMockDatabase()
  const mobile = '09123334455'
  const challenge = await authService.requestOtp({ mobile, purpose: 'reset_password' })
  const proof = await authService.verifyPasswordResetOtp({
    mobile,
    purpose: 'reset_password',
    challengeId: challenge.challengeId,
    code: '۱۲۳۴۵۶',
  })

  await assert.rejects(
    authService.resetPassword({
      resetToken: proof.resetToken,
      password: 'new-password-123',
      passwordConfirmation: 'different-password',
    }),
    (error) => error?.code === 'VALIDATION_ERROR',
  )

  await authService.resetPassword({
    resetToken: proof.resetToken,
    password: 'new-password-123',
    passwordConfirmation: 'new-password-123',
  })

  await assert.rejects(
    authService.resetPassword({
      resetToken: proof.resetToken,
      password: 'new-password-123',
      passwordConfirmation: 'new-password-123',
    }),
    (error) => error?.code === 'UNAUTHENTICATED',
  )
})

test('OTP UI supports full-code paste, localized digits, keyboard recovery, and retry-safe resend', async () => {
  const source = await readFile(new URL('../src/components/ui/OtpInput.vue', import.meta.url), 'utf8')
  const resendHandler = source.match(/function handleResend\(\) \{([\s\S]*?)\n\}/)?.[1] ?? ''

  assert.match(source, /@paste="handlePaste"/)
  assert.match(source, /replace\(\/\[۰-۹\]\/g/)
  assert.match(source, /event\.key === 'Backspace'/)
  assert.match(source, /autocomplete="index === 0 \? 'one-time-code' : 'off'"/)
  assert.match(resendHandler, /emit\('resend'\)/)
  assert.doesNotMatch(resendHandler, /restartCountdown/)
})

test('OTC quote reconciles from canonical crypto and order retry is idempotent', async () => {
  resetMockDatabase()
  const requestedToman = '50000000'
  const beforeOrders = mockDb.orders.length
  const beforeUsed = mockDb.verification.limits.usedBuy
  const beforeAvailable = mockDb.wallet.availableToman
  const quote = await tradeService.getQuote({
    side: 'buy',
    assetSymbol: 'USDT',
    inputSide: 'toman',
    amount: requestedToman,
  })

  assert.equal(
    quote.tomanAmount,
    financial.calculateQuoteTotal(quote.cryptoAmount, quote.rateToman),
  )
  assert.equal(financial.compareDecimal(quote.tomanAmount, requestedToman) <= 0, true)
  assert.equal(
    quote.finalTomanAmount,
    financial.addDecimal(quote.tomanAmount, quote.feeToman),
  )

  const clientRequestId = `test_trade_${Date.now()}_0001`
  const input = {
    quoteId: quote.id,
    acceptedRateToman: quote.rateToman,
    clientRequestId,
  }
  const first = await tradeService.createOrder(input)
  const retry = await tradeService.createOrder(input)

  assert.equal(retry.id, first.id)
  assert.equal(mockDb.orders.length, beforeOrders + 1)
  assert.equal(
    mockDb.verification.limits.usedBuy,
    financial.addDecimal(beforeUsed, quote.tomanAmount),
  )
  assert.equal(
    mockDb.wallet.availableToman,
    financial.subtractDecimal(beforeAvailable, quote.finalTomanAmount),
  )
})

test('PRICE_CHANGED UI exits always invalidate and recover the paused quote', async () => {
  const source = await readFile(
    new URL('../src/components/trade/OtcQuickTrade.vue', import.meta.url),
    'utf8',
  )

  const recovery = source.match(/const exitPriceChange = \(reopenReview = false\) => \{([\s\S]*?)\n\}/)?.[1] ?? ''
  assert.match(recovery, /if \(!priceChange\.value\) return/)
  assert.match(recovery, /priceChange\.value = null/)
  assert.match(recovery, /reopenReviewAfterRefresh = reopenReview/)
  assert.match(recovery, /calculate\(\)/)
  assert.match(source, /@update:model-value="handlePriceChangeVisibility"/)
  assert.match(source, /@click="exitPriceChange\(true\)"/)
  assert.match(source, /@click="exitPriceChange\(\)"/)
})

test('Toman withdrawal is estimate-bound and exactly-once across retries', async () => {
  resetMockDatabase()
  const amount = '10000000'
  const beforeTransactions = mockDb.transactions.length
  const beforeAvailable = mockDb.wallet.availableToman
  const estimate = await walletService.estimateTomanWithdrawal({
    amount,
    bankAccountId: 'bank_acc_saman',
  })
  assert.equal(estimate.receivable, '9994000')

  const input = {
    estimateToken: estimate.estimateToken,
    estimateVersion: estimate.estimateVersion,
    idempotencyKey: `test_toman_withdraw_${Date.now()}_0001`,
  }
  const first = await walletService.createTomanWithdrawal(input)
  const retry = await walletService.createTomanWithdrawal(input)

  assert.equal(retry.id, first.id)
  assert.equal(mockDb.transactions.length, beforeTransactions + 1)
  assert.equal(mockDb.verification.limits.usedTomanWithdrawal, amount)
  assert.equal(
    mockDb.wallet.availableToman,
    financial.subtractDecimal(beforeAvailable, amount),
  )
})

test('crypto withdrawal binds estimate and OTP and commits idempotently', async () => {
  resetMockDatabase()
  const asset = mockDb.wallet.assets.find((item) => item.symbol === 'USDT')
  assert.ok(asset)
  const beforeAvailable = asset.available
  const beforeTransactions = mockDb.transactions.length
  const estimate = await walletService.estimateCryptoWithdrawal({
    assetSymbol: 'USDT',
    networkCode: 'TRC20',
    address: 'TYpR7V8xYn6PXJb9s5aJvM3duGsXhQ2Wef',
    amount: '10',
  })
  const challenge = await walletService.requestCryptoWithdrawalOtp(
    estimate.estimateToken,
    estimate.estimateVersion,
  )
  const baseInput = {
    estimateToken: estimate.estimateToken,
    estimateVersion: estimate.estimateVersion,
    otpChallengeToken: challenge.challengeToken,
  }

  await assert.rejects(
    walletService.createCryptoWithdrawal({
      ...baseInput,
      otp: '000000',
      idempotencyKey: `test_crypto_wrong_${Date.now()}_0001`,
    }),
    (error) => error?.code === 'VALIDATION_ERROR',
  )

  const input = {
    ...baseInput,
    otp: '۱۲۳۴۵۶',
    idempotencyKey: `test_crypto_withdraw_${Date.now()}_0001`,
  }
  const first = await walletService.createCryptoWithdrawal(input)
  const retry = await walletService.createCryptoWithdrawal(input)

  assert.equal(retry.id, first.id)
  assert.equal(first.networkCode, 'TRC20')
  assert.equal(mockDb.transactions.length, beforeTransactions + 1)
  assert.equal(
    mockDb.verification.limits.usedCryptoWithdrawalTomanEquivalent,
    estimate.tomanEquivalent,
  )
  assert.equal(asset.available, financial.subtractDecimal(beforeAvailable, estimate.amount))
})
