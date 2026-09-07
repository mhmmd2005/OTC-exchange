import { computed, onMounted, ref } from 'vue'

const theme = ref('dark')

export function useTheme() {
  const isDark = computed(() => theme.value === 'dark')

  const applyTheme = (value) => {
    const nextTheme = value === 'light' ? 'light' : 'dark'
    theme.value = nextTheme
    document.documentElement.setAttribute('data-theme', nextTheme)
    localStorage.setItem('otc-theme', nextTheme)
  }

  const toggleTheme = () => {
    applyTheme(isDark.value ? 'light' : 'dark')
  }

  onMounted(() => {
    const saved = localStorage.getItem('otc-theme')
    applyTheme(saved || 'dark')
  })

  return { theme, isDark, toggleTheme }
}
