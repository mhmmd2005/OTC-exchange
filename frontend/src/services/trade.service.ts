import type {
  CreateOrderInput,
  NotificationItem,
  OtcOrder,
  QuoteRequest,
  TradeQuote,
  Transaction,
  WalletAsset,
} from '@/types'
import {
  addDecimal,
  calculatePercentageAmount,
  calculateQuoteAmount,
  calculateQuoteTotal,
  compareDecimal,
  roundDecimal,
  subtractDecimal,
} from '@/utils/decimal'
import { ApiError, api, isMockApiEnabled, mockResponse } from './api'
import { mockAssets } from './mock/data'
import { createMockId, futureIso, nowIso } from './mock/helpers'
import { mockDb } from './mock/state'

export interface TradeService {
  getQuote(input: QuoteRequest, signal?: AbortSignal): Promise<TradeQuote>
  getQuoteById(id: string): Promise<TradeQuote>
  createOrder(input: CreateOrderInput): Promise<OtcOrder>
}

const quotes = new Map<string, TradeQuote>()
const ordersByRequestId = new Map<string, OtcOrder>()
const MINIMUM_ORDER_TOMAN = '1000000'
const MAXIMUM_ORDER_TOMAN = '500000000'
const FEE_PERCENT = '0.15'

function findMarket(symbol: string) {
  const market = mockAssets.find((item) => item.symbol.toUpperCase() === symbol.toUpperCase())
  if (!market) throw new ApiError('ارز مورد نظر پیدا نشد.', 'NOT_FOUND', 404)
  if (!market.tradable) {
    throw new ApiError('خرید و فروش این ارز موقتاً غیرفعال است.', 'ASSET_DISABLED', 409)
  }
  return market
}

function findWalletAsset(symbol: string): WalletAsset {
  const asset = mockDb.wallet.assets.find((item) => item.symbol.toUpperCase() === symbol.toUpperCase())
  if (!asset) throw new ApiError('کیف پول ارز مورد نظر پیدا نشد.', 'NOT_FOUND', 404)
  return asset
}

function buildQuote(input: QuoteRequest): TradeQuote {
  if (!input.amount || compareDecimal(input.amount, '0') <= 0) {
    throw new ApiError('یک مبلغ معتبر وارد کنید.', 'VALIDATION_ERROR', 422, {
      fields: { amount: 'مبلغ باید بیشتر از صفر باشد.' },
    })
  }

  const market = findMarket(input.assetSymbol)
  const rateToman = input.side === 'buy' ? market.buyPriceToman : market.sellPriceToman
  const cryptoAmount = input.inputSide === 'crypto'
    ? roundDecimal(input.amount, market.amountPrecision, 'down')
    : calculateQuoteAmount(input.amount, rateToman, market.amountPrecision)
  // The quote is reconciled from one canonical crypto quantity. For a Toman
  // input this avoids silently charging the unconvertible rounding remainder.
  const requestedTomanAmount = input.inputSide === 'toman'
    ? input.amount
    : calculateQuoteTotal(cryptoAmount, rateToman)
  const tomanAmount = calculateQuoteTotal(cryptoAmount, rateToman)

  if (compareDecimal(requestedTomanAmount, MINIMUM_ORDER_TOMAN) < 0) {
    throw new ApiError('حداقل مبلغ سفارش ۱ میلیون تومان است.', 'BELOW_MINIMUM', 422, {
      fields: { amount: 'مبلغ سفارش را افزایش دهید.' },
    })
  }
  if (compareDecimal(requestedTomanAmount, MAXIMUM_ORDER_TOMAN) > 0) {
    throw new ApiError('سقف هر سفارش ۵۰۰ میلیون تومان است.', 'ABOVE_MAXIMUM', 422, {
      fields: { amount: 'مبلغ سفارش را کاهش دهید.' },
    })
  }

  if (mockDb.user.kycStatus !== 'verified') {
    throw new ApiError(
      'برای خرید و فروش باید احراز هویت خود را تکمیل کنید.',
      'KYC_REQUIRED',
      403,
      { actionLabel: 'تکمیل احراز هویت', actionRoute: '/app/verification' },
    )
  }

  const limit = input.side === 'buy'
    ? mockDb.verification.limits.dailyBuy
    : mockDb.verification.limits.dailySell
  const used = input.side === 'buy'
    ? mockDb.verification.limits.usedBuy
    : mockDb.verification.limits.usedSell
  const remaining = subtractDecimal(limit, used)
  if (compareDecimal(tomanAmount, remaining) > 0) {
    throw new ApiError(
      'مبلغ سفارش از سقف باقی‌مانده امروز بیشتر است.',
      'DAILY_LIMIT_EXCEEDED',
      409,
      { remaining, actionLabel: 'مشاهده سقف‌ها', actionRoute: '/app/verification' },
    )
  }

  const feeToman = calculatePercentageAmount(tomanAmount, FEE_PERCENT, 0)
  const finalTomanAmount = input.side === 'buy'
    ? addDecimal(tomanAmount, feeToman)
    : subtractDecimal(tomanAmount, feeToman)

  if (input.side === 'buy' && compareDecimal(finalTomanAmount, mockDb.wallet.availableToman) > 0) {
    throw new ApiError(
      'موجودی تومان برای این خرید کافی نیست.',
      'INSUFFICIENT_TOMAN_BALANCE',
      409,
      { actionLabel: 'واریز تومان', actionRoute: '/app/deposit/toman' },
    )
  }
  if (input.side === 'sell') {
    const walletAsset = findWalletAsset(input.assetSymbol)
    if (compareDecimal(cryptoAmount, walletAsset.available) > 0) {
      throw new ApiError(
        `موجودی قابل فروش ${walletAsset.nameFa} کافی نیست.`,
        'INSUFFICIENT_CRYPTO_BALANCE',
        409,
      )
    }
  }

  const createdAt = nowIso()
  const quote: TradeQuote = {
    id: createMockId('quote'),
    side: input.side,
    assetSymbol: input.assetSymbol,
    inputSide: input.inputSide,
    rateToman,
    cryptoAmount,
    tomanAmount,
    feeToman,
    feePercent: FEE_PERCENT,
    finalTomanAmount,
    minimumToman: MINIMUM_ORDER_TOMAN,
    maximumToman: MAXIMUM_ORDER_TOMAN,
    createdAt,
    expiresAt: futureIso(30),
  }
  quotes.set(quote.id, quote)
  return quote
}

function findQuote(id: string): TradeQuote {
  const quote = quotes.get(id)
  if (!quote) {
    throw new ApiError('نرخ مورد نظر پیدا نشد. نرخ تازه دریافت کنید.', 'QUOTE_EXPIRED', 410)
  }
  if (Date.parse(quote.expiresAt) <= Date.now()) {
    quotes.delete(id)
    throw new ApiError('مهلت این نرخ تمام شده است. نرخ تازه دریافت کنید.', 'QUOTE_EXPIRED', 410)
  }
  return quote
}

export const tradeService: TradeService = {
  getQuote(input, signal) {
    if (isMockApiEnabled) return mockResponse(() => buildQuote(input), { delay: 260, signal })
    return api.post<TradeQuote>('/trade/quotes', input, { signal })
  },

  getQuoteById(id) {
    if (isMockApiEnabled) return mockResponse(() => findQuote(id))
    return api.get<TradeQuote>(`/trade/quotes/${id}`)
  },

  createOrder(input) {
    if (!input.clientRequestId.trim()) {
      return Promise.reject(new ApiError('شناسه امن درخواست ارسال نشده است.', 'VALIDATION_ERROR', 422))
    }
    if (!isMockApiEnabled) {
      return api.post<OtcOrder>('/trade/orders', input, {
        headers: { 'Idempotency-Key': input.clientRequestId },
      })
    }

    return mockResponse(() => {
      const existingOrder = ordersByRequestId.get(input.clientRequestId)
      if (existingOrder) return existingOrder
      const quote = findQuote(input.quoteId)
      if (compareDecimal(input.acceptedRateToman, quote.rateToman) !== 0) {
        throw new ApiError(
          'قیمت به‌روزرسانی شده است. نرخ جدید را بررسی و تأیید کنید.',
          'PRICE_CHANGED',
          409,
          { previousRate: input.acceptedRateToman, currentRate: quote.rateToman },
        )
      }

      const market = findMarket(quote.assetSymbol)
      const walletAsset = findWalletAsset(quote.assetSymbol)
      const createdAt = nowIso()
      const orderNumber = `OTC-${Date.now().toString().slice(-9)}`
      const order: OtcOrder = {
        id: createMockId('ord'),
        orderNumber,
        side: quote.side,
        assetSymbol: quote.assetSymbol,
        assetNameFa: market.nameFa,
        cryptoAmount: quote.cryptoAmount,
        tomanAmount: quote.tomanAmount,
        rateToman: quote.rateToman,
        feeToman: quote.feeToman,
        finalTomanAmount: quote.finalTomanAmount,
        status: 'processing',
        createdAt,
        updatedAt: createdAt,
        paymentSource: input.paymentSource
          ?? (quote.side === 'buy' ? 'کیف پول تومان' : `کیف پول ${market.nameFa} روشا`),
        destination: input.destination
          ?? (quote.side === 'buy' ? `کیف پول ${market.nameFa} روشا` : 'کیف پول تومان'),
        timeline: [
          {
            id: createMockId('timeline'),
            status: 'pending_payment',
            title: 'سفارش ثبت شد',
            occurredAt: createdAt,
            completed: true,
            current: false,
          },
          {
            id: createMockId('timeline'),
            status: 'payment_confirmed',
            title: quote.side === 'buy' ? 'پرداخت تأیید شد' : 'دارایی دریافت شد',
            occurredAt: createdAt,
            completed: true,
            current: false,
          },
          {
            id: createMockId('timeline'),
            status: 'processing',
            title: 'در حال پردازش',
            description: 'سفارش شما در صف پردازش خودکار قرار دارد.',
            occurredAt: createdAt,
            completed: false,
            current: true,
          },
          {
            id: createMockId('timeline'),
            status: 'completed',
            title: 'تکمیل سفارش',
            completed: false,
            current: false,
          },
        ],
      }

      if (quote.side === 'buy') {
        mockDb.wallet.availableToman = subtractDecimal(
          mockDb.wallet.availableToman,
          quote.finalTomanAmount,
        )
        mockDb.wallet.lockedToman = addDecimal(mockDb.wallet.lockedToman, quote.finalTomanAmount)
      } else {
        walletAsset.available = subtractDecimal(walletAsset.available, quote.cryptoAmount)
        walletAsset.locked = addDecimal(walletAsset.locked, quote.cryptoAmount)
      }

      if (quote.side === 'buy') {
        mockDb.verification.limits.usedBuy = addDecimal(
          mockDb.verification.limits.usedBuy,
          quote.tomanAmount,
        )
      } else {
        mockDb.verification.limits.usedSell = addDecimal(
          mockDb.verification.limits.usedSell,
          quote.tomanAmount,
        )
      }

      const transaction: Transaction = {
        id: createMockId('txn'),
        referenceNumber: `TRX-${Date.now().toString().slice(-8)}`,
        type: quote.side,
        status: 'processing',
        assetSymbol: quote.assetSymbol,
        amount: quote.cryptoAmount,
        tomanAmount: quote.finalTomanAmount,
        fee: quote.feeToman,
        orderId: order.id,
        title: `${quote.side === 'buy' ? 'خرید' : 'فروش'} ${market.nameFa}`,
        description: `${quote.side === 'buy' ? 'خرید OTC از' : 'فروش OTC به'} روشا`,
        createdAt,
      }
      const notification: NotificationItem = {
        id: createMockId('not'),
        category: 'order',
        title: 'سفارش شما ثبت شد',
        message: `سفارش ${quote.side === 'buy' ? 'خرید' : 'فروش'} ${quote.cryptoAmount} ${quote.assetSymbol} در حال پردازش است.`,
        read: false,
        createdAt,
        action: { label: 'مشاهده سفارش', to: `/app/orders/${order.id}` },
      }

      mockDb.orders.unshift(order)
      mockDb.transactions.unshift(transaction)
      mockDb.notifications.unshift(notification)
      ordersByRequestId.set(input.clientRequestId, order)
      quotes.delete(quote.id)
      return order
    }, { delay: 420 })
  },
}

export default tradeService
