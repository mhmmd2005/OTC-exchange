import { defineStore } from 'pinia'
import { ref } from 'vue'
import { marketService } from '../services/market'

export const useMarketStore = defineStore('market', () => {
  const prices = ref([])
  const series = ref({})
  const loading = ref(false)

  async function fetchPrices() {
    loading.value = true
    try {
      const response = await marketService.getPrices()
      prices.value = response.data
    } finally {
      loading.value = false
    }
  }

  async function fetchSeries() {
    const response = await marketService.getChartSeries()
    series.value = response.data
  }

  return { prices, series, loading, fetchPrices, fetchSeries }
})
