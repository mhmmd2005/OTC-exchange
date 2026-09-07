import type { OrderFilters, OtcOrder, PaginatedResult } from '@/types'
import { ApiError, api, resolveApi } from './api'
import { normalizedSearch, paginate } from './mock/helpers'
import { mockDb } from './mock/state'

export interface OrderService {
  list(filters?: OrderFilters): Promise<PaginatedResult<OtcOrder>>
  getById(id: string): Promise<OtcOrder>
  cancel(id: string): Promise<OtcOrder>
}

function findOrder(id: string): OtcOrder {
  const order = mockDb.orders.find((item) => item.id === id || item.orderNumber === id)
  if (!order) throw new ApiError('سفارش مورد نظر پیدا نشد.', 'NOT_FOUND', 404)
  return order
}

export const orderService: OrderService = {
  list(filters = {}) {
    return resolveApi(() => {
      const search = normalizedSearch(filters.search)
      const activeStatuses = new Set(['pending_payment', 'payment_confirmed', 'processing'])
      const filtered = mockDb.orders.filter((order) => {
        const matchesSide = !filters.side || order.side === filters.side
        const matchesAsset = !filters.assetSymbol || order.assetSymbol === filters.assetSymbol
        const matchesStatus = !filters.status
          || (filters.status === 'active' ? activeStatuses.has(order.status) : order.status === filters.status)
        const matchesSearch = !search || order.orderNumber.toLowerCase().includes(search)
          || order.assetNameFa.includes(search) || order.assetSymbol.toLowerCase().includes(search)
        return matchesSide && matchesAsset && matchesStatus && matchesSearch
      })
      return paginate(filtered, filters)
    }, () => api.get<PaginatedResult<OtcOrder>>('/orders', {
      query: {
        page: filters.page,
        pageSize: filters.pageSize,
        side: filters.side,
        status: filters.status,
        asset: filters.assetSymbol,
        search: filters.search,
      },
    }))
  },

  getById(id) {
    return resolveApi(() => findOrder(id), () => api.get<OtcOrder>(`/orders/${id}`))
  },

  cancel(id) {
    return resolveApi(() => {
      const order = findOrder(id)
      if (order.status !== 'pending_payment') {
        throw new ApiError('این سفارش دیگر قابل لغو نیست.', 'BAD_REQUEST', 409)
      }
      order.status = 'cancelled'
      order.updatedAt = new Date().toISOString()
      order.timeline.push({
        id: `timeline_${Date.now()}`,
        status: 'cancelled',
        title: 'سفارش لغو شد',
        occurredAt: order.updatedAt,
        completed: true,
        current: true,
      })
      return order
    }, () => api.post<OtcOrder>(`/orders/${id}/cancel`))
  },
}

export default orderService

