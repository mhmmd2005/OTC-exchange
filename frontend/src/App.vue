<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { RouterView } from 'vue-router'

const isOffline = ref(!navigator.onLine)
const syncConnection = () => { isOffline.value = !navigator.onLine }

onMounted(() => {
  window.addEventListener('online', syncConnection)
  window.addEventListener('offline', syncConnection)
})

onUnmounted(() => {
  window.removeEventListener('online', syncConnection)
  window.removeEventListener('offline', syncConnection)
})
</script>

<template>
  <div v-if="isOffline" class="offline-banner" role="status">
    <span class="offline-dot" aria-hidden="true" />
    اتصال اینترنت برقرار نیست؛ اطلاعات مالی نمایش‌داده‌شده به‌روزرسانی نمی‌شود.
  </div>
  <RouterView />
</template>
