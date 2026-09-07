<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { usePreferencesStore } from '@/stores/preferences'
import AppIcon from './AppIcon.vue'

withDefaults(defineProps<{ mode?: 'icon' | 'tile' }>(), { mode: 'icon' })

const preferences = usePreferencesStore()
const systemDark = ref(false)
let mediaQuery: MediaQueryList | undefined

const dark = computed(() => preferences.theme === 'dark'
  || (preferences.theme === 'system' && systemDark.value))
const actionLabel = computed(() => dark.value ? 'فعال‌کردن پوسته روشن' : 'فعال‌کردن پوسته تیره')
const currentLabel = computed(() => dark.value ? 'پوسته تیره' : 'پوسته روشن')

function syncSystemTheme(event?: MediaQueryListEvent): void {
  systemDark.value = event?.matches ?? mediaQuery?.matches ?? false
}

function toggleTheme(): void {
  void preferences.saveTheme(dark.value ? 'light' : 'dark').catch(() => undefined)
}

onMounted(() => {
  mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
  syncSystemTheme()
  mediaQuery.addEventListener('change', syncSystemTheme)
})

onBeforeUnmount(() => mediaQuery?.removeEventListener('change', syncSystemTheme))
</script>

<template>
  <button
    type="button"
    class="theme-quick-toggle"
    :class="`theme-quick-toggle--${mode}`"
    :aria-label="actionLabel"
    :aria-busy="preferences.themeSyncing || undefined"
    :title="mode === 'icon' ? actionLabel : undefined"
    @click="toggleTheme"
  >
    <span class="theme-quick-toggle__icon" aria-hidden="true">
      <AppIcon :name="dark ? 'moon' : 'sun'" :size="mode === 'icon' ? 20 : 22" />
    </span>
    <span v-if="mode === 'tile'" class="theme-quick-toggle__copy">
      <strong>{{ currentLabel }}</strong>
      <small>{{ dark ? 'تغییر به روشن' : 'تغییر به تیره' }}</small>
    </span>
    <span class="sr-only" role="status" aria-live="polite">
      {{ preferences.themeSyncError || '' }}
    </span>
  </button>
</template>

<style scoped>
.theme-quick-toggle { color: var(--color-text-secondary); }
.theme-quick-toggle--icon { display: grid; width: 2.75rem; height: 2.75rem; flex: 0 0 auto; border: 1px solid var(--control-border); border-radius: var(--radius-md); background: var(--color-surface-1); place-items: center; transition: border-color var(--transition-fast), background var(--transition-fast), color var(--transition-fast); }
.theme-quick-toggle--icon:hover { border-color: var(--color-border-hover); background: var(--color-surface-3); color: var(--color-primary); }
.theme-quick-toggle--icon:focus-visible,.theme-quick-toggle--tile:focus-visible { outline: 2px solid var(--color-border-focus); outline-offset: 2px; }
.theme-quick-toggle--tile { display: flex; min-width: 0; min-height: 6.4rem; flex-direction: column; align-items: center; justify-content: center; gap: var(--space-2); padding: var(--space-2); border: 1px solid var(--color-border-soft); border-radius: var(--radius-md); background: var(--color-surface-2); text-align: center; }
.theme-quick-toggle__icon { display: grid; width: 2.6rem; height: 2.6rem; flex: 0 0 auto; border-radius: .8rem; background: var(--color-primary-soft); color: var(--color-primary); place-items: center; }
.theme-quick-toggle__copy { display: grid; min-width: 0; gap: .1rem; }
.theme-quick-toggle__copy strong { font-size: var(--font-size-xs); font-weight: 500; }
.theme-quick-toggle__copy small { color: var(--color-text-muted); font-size: .62rem; }
@media (max-width: 767px) { .theme-quick-toggle--icon { width: 2.6rem; height: 2.6rem; } }
</style>
