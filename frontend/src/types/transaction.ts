import type {
  AssetSymbol,
  DateRange,
  DecimalString,
  ISODateString,
  PaginationParams,
} from './common'

export type TransactionType =
  | 'buy'
  | 'sell'
  | 'toman_deposit'
  | 'toman_withdrawal'
  | 'crypto_deposit'
  | 'crypto_withdrawal'
  | 'fee'
  | 'refund'
  | 'reversal'

export type TransactionStatus =
  | 'pending'
  | 'processing'
  | 'completed'
  | 'failed'
  | 'cancelled'
  | 'reversed'

export interface Transaction {
  id: string
  referenceNumber: string
  type: TransactionType
  status: TransactionStatus
  assetSymbol: AssetSymbol
  amount: DecimalString
  tomanAmount?: DecimalString
  fee?: DecimalString
  networkCode?: string
  address?: string
  txId?: string
  confirmations?: number
  requiredConfirmations?: number
  bankAccountId?: string
  orderId?: string
  title: string
  description?: string
  createdAt: ISODateString
  completedAt?: ISODateString
}

export interface TransactionFilters extends PaginationParams, DateRange {
  type?: TransactionType
  status?: TransactionStatus
  assetSymbol?: AssetSymbol
  networkCode?: string
  search?: string
}
