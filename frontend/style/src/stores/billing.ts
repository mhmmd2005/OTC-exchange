import { defineStore } from 'pinia'
import { useAuthStore } from './auth'
import { API_BASE } from './auth'

export const billingEndpoints = {
  OVERVIEW:          `${API_BASE}/billing/overview/`,
  HISTORY:           `${API_BASE}/billing/history/`,
  TOPUP_CRYPTO:      `${API_BASE}/billing/topup/crypto/`,
  CRYPTO_CURRENCIES: `${API_BASE}/billing/crypto/currencies/`,
  // optional
  TOPUP_PAYPAL:      `${API_BASE}/billing/topup/paypal/`,
  TOPUP_RESULT:      `${API_BASE}/billing/topup/result/`,
}

export const useBillingStore = defineStore('billing', {
  state: () => ({
    overview: null as any,
    history: [] as any[],
    currencies: [] as Array<{ code: string; name: string }>,
  }),

  actions: {
    async authorizedFetch(input: string, init?: RequestInit) {
      const auth = useAuthStore()
      return await auth.authorizedFetch(input, init)
    },

    async getOverview() {
      const res = await this.authorizedFetch(billingEndpoints.OVERVIEW, { method: 'GET' })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(data?.detail || `Load overview failed (${res.status})`)
      this.overview = data
      return data
    },

    async getCurrencies() {
      const res = await this.authorizedFetch(billingEndpoints.CRYPTO_CURRENCIES, { method: 'GET' })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(data?.detail || `Load crypto currencies failed (${res.status})`)
      this.currencies = Array.isArray(data?.currencies) ? data.currencies : []
      return this.currencies
    },

    async topupCrypto(payload: { amount: string; pay_currency?: string }) {
      const res = await this.authorizedFetch(billingEndpoints.TOPUP_CRYPTO, {
        method: 'POST',
        body: JSON.stringify(payload),
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(data?.detail || `Top-up failed (${res.status})`)
      return data
    },
    
    async getHistory(params?: {
      page?: number
      page_size?: number
      type?: string
      direction?: 'CREDIT' | 'DEBIT'
      provider?: string
      date_from?: string
      date_to?: string
      q?: string
    }) {
      const sp = new URLSearchParams()
      if (params?.page) sp.set('page', String(params.page))
      if (params?.page_size) sp.set('page_size', String(params.page_size))
      if (params?.type) sp.set('type', params.type)
      if (params?.direction) sp.set('direction', params.direction)
      if (params?.provider) sp.set('provider', params.provider)
      if (params?.date_from) sp.set('date_from', params.date_from)
      if (params?.date_to) sp.set('date_to', params.date_to)
      if (params?.q) sp.set('q', params.q)

      const url = sp.toString() ? `${billingEndpoints.HISTORY}?${sp.toString()}` : billingEndpoints.HISTORY
      const res = await this.authorizedFetch(url, { method: 'GET' })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(data?.detail || `Load history failed (${res.status})`)
      this.history = data?.results || data || []
      return data
    },
        async getTopupResult(params: Record<string, string | number | undefined>) {
      const sp = new URLSearchParams()
      Object.entries(params || {}).forEach(([k, v]) => { if (v != null) sp.set(k, String(v)) })
      const url = sp.toString() ? `${billingEndpoints.TOPUP_RESULT}?${sp}` : billingEndpoints.TOPUP_RESULT
      const res = await this.authorizedFetch(url, { method: 'GET' })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(data?.detail || `Load result failed (${res.status})`)
      return data
    },
  },
})
