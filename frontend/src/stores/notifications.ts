import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import type { NotificationFilters, NotificationItem } from '@/types'
import { notificationService } from '@/services/notification.service'

export const useNotificationsStore = defineStore('notifications', () => {
  const items = ref<NotificationItem[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const total = ref(0)
  const globalUnreadCount = ref(0)
  const unreadLoading = ref(false)

  const unreadCount = computed(() => globalUnreadCount.value)
  const hasUnread = computed(() => unreadCount.value > 0)

  async function fetchUnreadCount(): Promise<number> {
    unreadLoading.value = true
    try {
      const count = await notificationService.getUnreadCount()
      globalUnreadCount.value = count
      return count
    } finally {
      unreadLoading.value = false
    }
  }

  async function fetchNotifications(filters: NotificationFilters = {}): Promise<NotificationItem[]> {
    loading.value = true
    error.value = null
    try {
      const [result, unread] = await Promise.all([
        notificationService.list({ pageSize: 50, ...filters }),
        notificationService.getUnreadCount(),
      ])
      items.value = result.items
      total.value = result.total
      globalUnreadCount.value = unread
      return result.items
    } catch (caught) {
      error.value = caught instanceof Error ? caught.message : 'اعلان‌ها بارگیری نشدند.'
      throw caught
    } finally {
      loading.value = false
    }
  }

  async function markAsRead(id: string): Promise<void> {
    const item = items.value.find((notification) => notification.id === id)
    const previous = item?.read
    if (item) item.read = true
    try {
      const updated = await notificationService.markAsRead(id)
      if (item) Object.assign(item, updated)
      if (previous === false) globalUnreadCount.value = Math.max(0, globalUnreadCount.value - 1)
    } catch (caught) {
      if (item && previous !== undefined) item.read = previous
      error.value = caught instanceof Error ? caught.message : 'اعلان خوانده نشد.'
      throw caught
    }
  }

  async function markAllAsRead(): Promise<void> {
    const previous = items.value.map((item) => item.read)
    items.value.forEach((item) => { item.read = true })
    try {
      await notificationService.markAllAsRead()
      globalUnreadCount.value = 0
    } catch (caught) {
      items.value.forEach((item, index) => { item.read = previous[index] ?? item.read })
      error.value = caught instanceof Error ? caught.message : 'اعلان‌ها به‌روزرسانی نشدند.'
      throw caught
    }
  }

  async function remove(id: string): Promise<void> {
    const index = items.value.findIndex((item) => item.id === id)
    const removed = index >= 0 ? items.value.splice(index, 1)[0] : undefined
    try {
      await notificationService.remove(id)
      total.value = Math.max(0, total.value - 1)
      if (removed && !removed.read) globalUnreadCount.value = Math.max(0, globalUnreadCount.value - 1)
    } catch (caught) {
      if (removed) items.value.splice(index, 0, removed)
      error.value = caught instanceof Error ? caught.message : 'حذف اعلان انجام نشد.'
      throw caught
    }
  }

  return {
    items,
    loading,
    error,
    total,
    unreadCount,
    unreadLoading,
    hasUnread,
    fetchUnreadCount,
    fetchNotifications,
    fetch: fetchNotifications,
    markAsRead,
    markAllAsRead,
    remove,
  }
})

export const useNotificationStore = useNotificationsStore
