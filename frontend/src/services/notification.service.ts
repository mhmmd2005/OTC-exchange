import type {
  NotificationFilters,
  NotificationItem,
  PaginatedResult,
} from '@/types'
import { ApiError, api, resolveApi } from './api'
import { paginate } from './mock/helpers'
import { mockDb } from './mock/state'

export interface NotificationService {
  list(filters?: NotificationFilters): Promise<PaginatedResult<NotificationItem>>
  getUnreadCount(): Promise<number>
  markAsRead(id: string): Promise<NotificationItem>
  markAllAsRead(): Promise<void>
  remove(id: string): Promise<void>
}

function findNotification(id: string): NotificationItem {
  const item = mockDb.notifications.find((notification) => notification.id === id)
  if (!item) throw new ApiError('اعلان مورد نظر پیدا نشد.', 'NOT_FOUND', 404)
  return item
}

export const notificationService: NotificationService = {
  list(filters = {}) {
    return resolveApi(() => {
      const filtered = mockDb.notifications.filter((item) =>
        (!filters.category || item.category === filters.category)
        && (filters.read === undefined || item.read === filters.read))
      return paginate(filtered, filters)
    }, () => api.get<PaginatedResult<NotificationItem>>('/notifications', {
      query: {
        page: filters.page,
        pageSize: filters.pageSize,
        category: filters.category,
        read: filters.read,
      },
    }))
  },

  getUnreadCount() {
    return resolveApi(
      () => mockDb.notifications.filter((item) => !item.read).length,
      () => api.get<number>('/notifications/unread-count'),
    )
  },

  markAsRead(id) {
    return resolveApi(() => {
      const item = findNotification(id)
      item.read = true
      return item
    }, () => api.patch<NotificationItem>(`/notifications/${id}`, { read: true }))
  },

  markAllAsRead() {
    return resolveApi(() => {
      mockDb.notifications.forEach((item) => { item.read = true })
    }, () => api.post<void>('/notifications/read-all'))
  },

  remove(id) {
    return resolveApi(() => {
      findNotification(id)
      const index = mockDb.notifications.findIndex((item) => item.id === id)
      mockDb.notifications.splice(index, 1)
    }, () => api.delete<void>(`/notifications/${id}`))
  },
}

export default notificationService

