<script setup>
import {onMounted, onUnmounted,} from 'vue'
import {useRouter} from 'vue-router'
import Toast from './components/Toast.vue'
import {useAuthStore} from './stores/auth'
import {startIdleSession, stopIdleSession,} from './services/idleSession'
import api from './services/api'

const router = useRouter()
const authStore = useAuthStore()

async function handleAuthExpired() {
  stopIdleSession()
  authStore.clearAuth()

  if (
      router.currentRoute.value.path !==
      '/login'
  ) {
    await router.replace('/login')
  }
}

onMounted(() => {
  authStore.initialize()

  window.addEventListener(
      'otc-auth-expired',
      handleAuthExpired,
  )

  if (authStore.isAuthenticated) {
    startIdleSession(
        authStore,
        router,
        api,
    )
  }
})

onUnmounted(() => {
  window.removeEventListener(
      'otc-auth-expired',
      handleAuthExpired,
  )

  stopIdleSession()
})
</script>

<template>
  <div class="app-root">
    <RouterView/>
    <Toast/>
  </div>
</template>