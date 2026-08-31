import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useNotificationStore = defineStore('notification', () => {
  const toasts = ref([])

  function addToast({ title, text, type = 'success' }) {
    const id = Date.now() + Math.random()
    toasts.value.push({ id, title, text, type })
    setTimeout(() => {
      toasts.value = toasts.value.filter((toast) => toast.id !== id)
    }, 3500)
  }

  return { toasts, addToast }
})

export { useNotificationsStore as useNotificationCenterStore } from './notifications'
