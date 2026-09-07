import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'
import { usePreferencesStore } from './stores/preferences'
import './styles/main.css'

document.documentElement.lang = 'fa'
document.documentElement.dir = 'rtl'

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(router)

const preferences = usePreferencesStore(pinia)
preferences.apply()
const systemTheme = window.matchMedia('(prefers-color-scheme: dark)')
systemTheme.addEventListener('change', () => {
  if (preferences.preferences.theme === 'system') preferences.apply()
})

window.addEventListener('rosha:unauthorized', () => {
  const auth = useAuthStore()
  const current = router.currentRoute.value
  auth.expireSession()
  if (!current.path.startsWith('/auth/')) {
    void router.replace({ name: 'session-expired', query: { redirect: current.fullPath } })
  }
})

app.mount('#app')

if ('serviceWorker' in navigator && import.meta.env.PROD) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(() => undefined)
  })
}
