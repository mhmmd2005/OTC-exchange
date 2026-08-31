import { createApp } from 'vue'
import { createPinia } from 'pinia'
import '@fontsource/vazirmatn/400.css'
import '@fontsource/vazirmatn/500.css'
import '@fontsource/vazirmatn/600.css'
import '@fontsource/vazirmatn/700.css'
import App from './App.vue'
import router from './router'
import './style.css'

const storedTheme = localStorage.getItem('otc-theme') || 'dark'
document.documentElement.setAttribute('data-theme', storedTheme)

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
