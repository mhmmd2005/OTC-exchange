import type { PaginatedResult, Transaction, TransactionFilters } from '@/types'
import { ApiError, api, resolveApi } from './api'
import { normalizedSearch, paginate } from './mock/helpers'
import { mockDb } from './mock/state'

export interface TransactionService {
  list(filters?: TransactionFilters): Promise<PaginatedResult<Transaction>>
  getById(id: string): Promise<Transaction>
}

export const transactionService: TransactionService = {
  list(filters = {}) {
    return resolveApi(() => {
      const search = normalizedSearch(filters.search)
      const from = filters.from ? Date.parse(filters.from) : Number.NEGATIVE_INFINITY
      const to = filters.to ? Date.parse(filters.to) : Number.POSITIVE_INFINITY
      const filtered = mockDb.transactions.filter((transaction) => {
        const timestamp = Date.parse(transaction.createdAt)
        const matchesSearch = !search
          || transaction.referenceNumber.toLowerCase().includes(search)
          || transaction.title.includes(search)
          || transaction.txId?.toLowerCase().includes(search)
        return (!filters.type || transaction.type === filters.type)
          && (!filters.status || transaction.status === filters.status)
          && (!filters.assetSymbol || transaction.assetSymbol === filters.assetSymbol)
          && (!filters.networkCode || transaction.networkCode === filters.networkCode)
          && timestamp >= from
          && timestamp <= to
          && Boolean(matchesSearch)
      })
      return paginate(filtered, filters)
    }, () => api.get<PaginatedResult<Transaction>>('/transactions/', {
      query: {
        page: filters.page,
        pageSize: filters.pageSize,
        type: filters.type,
        status: filters.status,
        asset: filters.assetSymbol,
        network: filters.networkCode,
        from: filters.from,
        to: filters.to,
        search: filters.search,
      },
    }))
  },

  getById(id) {
    return resolveApi(() => {
      const transaction = mockDb.transactions.find(
        (item) => item.id === id || item.referenceNumber === id,
      )
      if (!transaction) throw new ApiError('تراکنش مورد نظر پیدا نشد.', 'NOT_FOUND', 404)
      return transaction
    }, () => api.get<Transaction>(`/transactions/${id}`))
  },
}

export default transactionService
