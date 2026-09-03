import { defineStore } from 'pinia'
import { ref } from 'vue'
import { walletService } from '../services/wallet'

export const useWalletStore = defineStore('wallet', () => {
  const wallets = ref([])
  const loading = ref(false)

  async function fetchWallets() {
    loading.value = true
    try {
      const response = await walletService.getWallets()
      wallets.value = response.data
    } finally {
      loading.value = false
    }
  }

  async function fetchWalletById(id) {
    const response = await walletService.getWalletById(id)
    return response.data
  }

  return { wallets, loading, fetchWallets, fetchWalletById }
})
