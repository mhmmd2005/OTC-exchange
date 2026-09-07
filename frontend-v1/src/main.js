import { createApp } from 'vue'
import { createPinia } from 'pinia'
import '@fontsource/vazirmatn/400.css'
import '@fontsource/vazirmatn/500.css'
import '@fontsource/vazirmatn/600.css'
import '@fontsource/vazirmatn/700.css'
import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'
import './style.css'

const storedTheme = localStorage.getItem('otc-theme') || 'dark'
document.documentElement.setAttribute('data-theme', storedTheme)

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)

const auth = useAuthStore()
auth.initialize()

app.use(router)
app.mount('#app')
