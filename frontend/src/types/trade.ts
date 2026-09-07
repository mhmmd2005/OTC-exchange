import type { AssetSymbol, DecimalString, ISODateString, PaginationParams } from './common'

export type TradeSide = 'buy' | 'sell'
export type QuoteInputSide = 'toman' | 'crypto'
export type OrderStatus =
  | 'pending_payment'
  | 'payment_confirmed'
  | 'processing'
  | 'completed'
  | 'cancelled'
  | 'failed'
  | 'expired'

export interface QuoteRequest {
  side: TradeSide
  assetSymbol: AssetSymbol
  inputSide: QuoteInputSide
  amount: DecimalString
}

export interface TradeQuote {
  id: string
  side: TradeSide
  assetSymbol: AssetSymbol
  inputSide: QuoteInputSide
  rateToman: DecimalString
  cryptoAmount: DecimalString
  tomanAmount: DecimalString
  feeToman: DecimalString
  feePercent: DecimalString
  finalTomanAmount: DecimalString
  minimumToman: DecimalString
  maximumToman: DecimalString
  expiresAt: ISODateString
  createdAt: ISODateString
}

export interface CreateOrderInput {
  quoteId: string
  acceptedRateToman: DecimalString
  /** Stable per-confirmation key; reuse it when retrying an uncertain request. */
  clientRequestId: string
  paymentSource?: string
  destination?: string
}

export interface OrderTimelineEvent {
  id: string
  status: OrderStatus
  title: string
  description?: string
  occurredAt?: ISODateString
  completed: boolean
  current: boolean
}

export interface OtcOrder {
  id: string
  orderNumber: string
  side: TradeSide
  assetSymbol: AssetSymbol
  assetNameFa: string
  cryptoAmount: DecimalString
  tomanAmount: DecimalString
  rateToman: DecimalString
  feeToman: DecimalString
  finalTomanAmount: DecimalString
  status: OrderStatus
  createdAt: ISODateString
  updatedAt: ISODateString
  completedAt?: ISODateString
  paymentSource?: string
  destination?: string
  timeline: OrderTimelineEvent[]
}

export interface OrderFilters extends PaginationParams {
  side?: TradeSide
  status?: OrderStatus | 'active'
  assetSymbol?: AssetSymbol
  search?: string
}
