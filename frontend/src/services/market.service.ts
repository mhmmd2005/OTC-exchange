import type { AssetSymbol, MarketAsset, MarketListParams, PricePoint } from '@/types'
import { compareDecimal } from '@/utils/decimal'
import { ApiError, api, resolveApi } from './api'
import { mockAssets, mockPriceHistoryByPeriod } from './mock/data'
import { normalizedSearch } from './mock/helpers'
import { mockDb } from './mock/state'

export interface MarketService {
  list(params?: MarketListParams): Promise<MarketAsset[]>
  getBySymbol(symbol: AssetSymbol): Promise<MarketAsset>
  getPriceHistory(symbol: AssetSymbol, period?: '24h' | '7d' | '30d'): Promise<PricePoint[]>
}

function findAsset(symbol: AssetSymbol): MarketAsset {
  const asset = mockAssets.find((item) => item.symbol.toUpperCase() === symbol.toUpperCase())
  if (!asset) throw new ApiError('ارز مورد نظر پیدا نشد.', 'NOT_FOUND', 404)
  return asset
}

export const marketService: MarketService = {
  list(params = {}) {
    return resolveApi(() => {
      const search = normalizedSearch(params.search)
      const favorites = new Set(params.favorites ?? [])
      let result = mockAssets.filter((asset) => {
        const matchesSearch = !search || [asset.symbol, asset.nameFa, asset.nameEn]
          .some((value) => value.toLocaleLowerCase('fa').includes(search))
        const matchesFavorites = !params.favoritesOnly || favorites.has(asset.symbol)
        return matchesSearch && matchesFavorites
      })

      if (params.sortBy) {
        const direction = params.sortDirection === 'asc' ? 1 : -1
        result = [...result].sort((left, right) => {
          if (params.sortBy === 'symbol') return left.symbol.localeCompare(right.symbol) * direction
          if (params.sortBy === 'balance') {
            const leftBalance = mockDb.wallet.assets.find((item) => item.symbol === left.symbol)?.tomanValue ?? '0'
            const rightBalance = mockDb.wallet.assets.find((item) => item.symbol === right.symbol)?.tomanValue ?? '0'
            return compareDecimal(leftBalance, rightBalance) * direction
          }
          const leftValue = params.sortBy === 'buyPrice'
            ? left.buyPriceToman
            : params.sortBy === 'sellPrice'
              ? left.sellPriceToman
              : left.change24hPercent
          const rightValue = params.sortBy === 'buyPrice'
            ? right.buyPriceToman
            : params.sortBy === 'sellPrice'
              ? right.sellPriceToman
              : right.change24hPercent
          return compareDecimal(leftValue, rightValue) * direction
        })
      }
      return result
    }, () => api.get<MarketAsset[]>('/markets', {
      query: {
        search: params.search,
        favoritesOnly: params.favoritesOnly,
        sortBy: params.sortBy,
        sortDirection: params.sortDirection,
        favorites: params.favorites,
      },
    }))
  },

  getBySymbol(symbol) {
    return resolveApi(() => findAsset(symbol), () => api.get<MarketAsset>(`/markets/${symbol}`))
  },

  getPriceHistory(symbol, period = '24h') {
    return resolveApi(() => {
      findAsset(symbol)
      return mockPriceHistoryByPeriod[period][symbol.toUpperCase()] ?? []
    }, () => api.get<PricePoint[]>(`/markets/${symbol}/history`, { query: { period } }))
  },
}

export default marketService
