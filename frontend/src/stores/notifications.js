import { defineStore } from 'pinia'
import { ref } from 'vue'
import { notificationsService } from '../services/notifications'

export const useNotificationsStore = defineStore('notifications', () => {
  const list = ref([])

  async function fetchNotifications() {
    const response = await notificationsService.getNotifications()
    list.value = response.data
  }

  function addToast({ title, text, type = 'success' }) {
    list.value.unshift({
      id: Date.now(),
      title,
      message: text,
      type,
      status: 'unread',
      time: 'همین حالا',
    })
  }

  return { list, fetchNotifications, addToast }
})
