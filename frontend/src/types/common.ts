export type DecimalString = string
export type ISODateString = string
export type Identifier = string

export type AsyncState = 'idle' | 'loading' | 'success' | 'error'
export type SortDirection = 'asc' | 'desc'
export type ThemePreference = 'dark' | 'light' | 'system'

export interface ApiEnvelope<T> {
  data: T
  message?: string
  requestId?: string
}

export interface PaginationParams {
  page?: number
  pageSize?: number
}

export interface PaginatedResult<T> {
  items: T[]
  page: number
  pageSize: number
  total: number
  totalPages: number
}

export interface SelectOption<T extends string = string> {
  value: T
  label: string
  description?: string
  disabled?: boolean
}

export interface MoneyAmount {
  amount: DecimalString
  currency: 'IRT'
}

export interface CryptoAmount {
  amount: DecimalString
  symbol: AssetSymbol
}

export type AssetSymbol =
  | 'IRT'
  | 'USDT'
  | 'BTC'
  | 'ETH'
  | 'TRX'
  | 'TON'
  | (string & {})

export interface DailyLimit {
  limit: DecimalString
  used: DecimalString
  remaining: DecimalString
  currency: AssetSymbol
}

export interface DateRange {
  from?: ISODateString
  to?: ISODateString
}

export interface ActionLink {
  label: string
  to: string
}

export type StatusTone = 'neutral' | 'info' | 'success' | 'warning' | 'danger'

export interface StatusDefinition {
  label: string
  tone: StatusTone
  description?: string
}

