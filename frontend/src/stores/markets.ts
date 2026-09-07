import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import type { AssetSymbol, MarketAsset, MarketListParams } from '@/types'
import { marketService } from '@/services/market.service'
import { compareDecimal } from '@/utils/decimal'

export const useMarketStore = defineStore('markets', () => {
  const assets = ref<MarketAsset[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const lastUpdated = ref<string | null>(null)
  let requestSequence = 0

  const tradableAssets = computed(() => assets.value.filter((asset) => asset.tradable))
  const gainers = computed(() => [...assets.value]
    .filter((asset) => !asset.change24hPercent.startsWith('-'))
    .sort((left, right) => compareDecimal(right.change24hPercent, left.change24hPercent)))

  function getBySymbol(symbol: AssetSymbol): MarketAsset | undefined {
    return assets.value.find((asset) => asset.symbol.toUpperCase() === symbol.toUpperCase())
  }

  async function fetchMarkets(params: MarketListParams = {}): Promise<MarketAsset[]> {
    const requestId = ++requestSequence
    loading.value = true
    error.value = null
    try {
      const result = await marketService.list(params)
      if (requestId === requestSequence) {
        assets.value = result
        lastUpdated.value = result[0]?.updatedAt ?? new Date().toISOString()
      }
      return result
    } catch (caught) {
      if (requestId === requestSequence) {
        error.value = caught instanceof Error ? caught.message : 'قیمت ارزها بارگیری نشد.'
      }
      throw caught
    } finally {
      if (requestId === requestSequence) loading.value = false
    }
  }

  return {
    assets,
    loading,
    error,
    lastUpdated,
    tradableAssets,
    gainers,
    getBySymbol,
    fetchMarkets,
    fetch: fetchMarkets,
    refreshPrices: () => fetchMarkets(),
  }
})

export const useMarketsStore = useMarketStore
