<script setup>
import { storeToRefs } from 'pinia'
import { useNotificationStore } from '../stores/notification'

const notificationStore = useNotificationStore()
const { toasts } = storeToRefs(notificationStore)
</script>

<template>
  <div class="toast-stack">
    <div v-for="toast in toasts" :key="toast.id" :class="['toast-item', toast.type]">
      <div class="toast-title">{{ toast.title }}</div>
      <div class="toast-text">{{ toast.text }}</div>
    </div>
  </div>
</template>
