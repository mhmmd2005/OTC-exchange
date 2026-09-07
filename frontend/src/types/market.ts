import type { AssetSymbol, DecimalString, ISODateString, SortDirection } from './common'

export type NetworkStatus = 'active' | 'congested' | 'maintenance' | 'disabled'

export interface AssetNetwork {
  id: string
  assetSymbol: AssetSymbol
  code: string
  name: string
  displayName: string
  addressRegex?: string
  memoRequired: boolean
  depositEnabled: boolean
  withdrawalEnabled: boolean
  status: NetworkStatus
  confirmations: number
  estimatedArrivalMinutes: number
  minimumDeposit: DecimalString
  minimumWithdrawal: DecimalString
  withdrawalFee: DecimalString
}

export interface MarketAsset {
  id: string
  symbol: AssetSymbol
  nameFa: string
  nameEn: string
  iconUrl?: string
  color: string
  pricePrecision: number
  amountPrecision: number
  buyPriceToman: DecimalString
  sellPriceToman: DecimalString
  change24hPercent: DecimalString
  high24hToman: DecimalString
  low24hToman: DecimalString
  tradable: boolean
  depositEnabled: boolean
  withdrawalEnabled: boolean
  networks: AssetNetwork[]
  updatedAt: ISODateString
}

export type MarketSortField = 'symbol' | 'buyPrice' | 'sellPrice' | 'change24h' | 'balance'

export interface MarketListParams {
  search?: string
  favorites?: AssetSymbol[]
  favoritesOnly?: boolean
  sortBy?: MarketSortField
  sortDirection?: SortDirection
}

export interface PricePoint {
  timestamp: ISODateString
  priceToman: DecimalString
}

