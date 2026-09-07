import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import type { AssetSymbol, WalletSummary } from '@/types'
import { walletService } from '@/services/wallet.service'

export const useWalletStore = defineStore('wallet', () => {
  const summary = ref<WalletSummary | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const lastUpdated = ref<string | null>(null)
  let requestSequence = 0

  const assets = computed(() => summary.value?.assets ?? [])
  const totalValueToman = computed(() => summary.value?.totalValueToman ?? '0')
  const availableToman = computed(() => summary.value?.availableToman ?? '0')
  const cryptoValueToman = computed(() => summary.value?.cryptoValueToman ?? '0')

  function getAsset(symbol: AssetSymbol) {
    return assets.value.find((asset) => asset.symbol.toUpperCase() === symbol.toUpperCase())
  }

  async function fetchWallet(force = false): Promise<WalletSummary> {
    if (summary.value && !force) return summary.value
    const requestId = ++requestSequence
    loading.value = true
    error.value = null
    try {
      const result = await walletService.getSummary()
      if (requestId === requestSequence) {
        summary.value = result
        lastUpdated.value = result.updatedAt
      }
      return result
    } catch (caught) {
      if (requestId === requestSequence) {
        error.value = caught instanceof Error ? caught.message : 'اطلاعات کیف پول بارگیری نشد.'
      }
      throw caught
    } finally {
      if (requestId === requestSequence) loading.value = false
    }
  }

  function clear(): void {
    requestSequence += 1
    summary.value = null
    loading.value = false
    error.value = null
    lastUpdated.value = null
  }

  return {
    summary,
    loading,
    error,
    lastUpdated,
    assets,
    totalValueToman,
    availableToman,
    cryptoValueToman,
    getAsset,
    fetchWallet,
    fetchSummary: fetchWallet,
    refresh: () => fetchWallet(true),
    clear,
  }
})

