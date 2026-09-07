import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import type { AssetSymbol, ThemePreference, UserPreferences } from '@/types'
import { userService } from '@/services/user.service'
import { setUiDigitPreference } from '@/utils/formatters'

const STORAGE_KEY = 'rosha.preferences.v1'
const THEME_COLORS = {
  dark: '#050e1a',
  light: '#f2f6fb',
} as const

const defaults: UserPreferences = {
  theme: 'dark',
  hideBalances: false,
  hideZeroBalances: false,
  usePersianDigits: true,
  reduceMotion: false,
  favoriteAssets: ['USDT', 'BTC'],
  notificationChannels: { inApp: true, sms: true, email: false },
}

function loadStoredPreferences(): Partial<UserPreferences> {
  if (typeof window === 'undefined') return {}
  try {
    return JSON.parse(window.localStorage.getItem(STORAGE_KEY) ?? '{}') as Partial<UserPreferences>
  } catch {
    return {}
  }
}

function normalizeTheme(value: unknown): ThemePreference {
  return value === 'light' || value === 'system' ? value : 'dark'
}

function mergePreferences(input: Partial<UserPreferences>): UserPreferences {
  return {
    ...defaults,
    ...input,
    theme: normalizeTheme(input.theme),
    favoriteAssets: Array.isArray(input.favoriteAssets)
      ? [...new Set(input.favoriteAssets)]
      : [...defaults.favoriteAssets],
    notificationChannels: {
      ...defaults.notificationChannels,
      ...input.notificationChannels,
    },
  }
}

export const usePreferencesStore = defineStore('preferences', () => {
  const preferences = ref<UserPreferences>(mergePreferences(loadStoredPreferences()))
  const hydrated = ref(false)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const themeSyncing = ref(false)
  const themeSyncError = ref<string | null>(null)
  let themeSyncRevision = 0
  let themeSyncQueue: Promise<void> = Promise.resolve()

  const hideBalances = computed(() => preferences.value.hideBalances)
  const hideZeroBalances = computed(() => preferences.value.hideZeroBalances)
  const theme = computed(() => preferences.value.theme)
  const favoriteAssets = computed(() => preferences.value.favoriteAssets)

  function persist(): void {
    if (typeof window !== 'undefined') {
      try {
        window.localStorage.setItem(STORAGE_KEY, JSON.stringify(preferences.value))
      } catch {
        // Applying the selected theme must still work when storage is unavailable.
      }
    }
    applyDocumentPreferences()
  }

  function applyDocumentPreferences(input: UserPreferences = preferences.value): void {
    if (typeof document === 'undefined') return
    const selected = input.theme
    const dark = selected === 'dark'
      || (selected === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)
    document.documentElement.dataset.theme = dark ? 'dark' : 'light'
    document.documentElement.dataset.digits = input.usePersianDigits ? 'persian' : 'latin'
    document.documentElement.dataset.reduceMotion = input.reduceMotion ? 'true' : 'false'
    document.documentElement.style.colorScheme = dark ? 'dark' : 'light'
    document.querySelector<HTMLMetaElement>('meta[name="theme-color"]')
      ?.setAttribute('content', dark ? THEME_COLORS.dark : THEME_COLORS.light)
    document.querySelector<HTMLMetaElement>('meta[name="color-scheme"]')
      ?.setAttribute('content', dark ? 'dark' : 'light')
    document.querySelector<HTMLMetaElement>('meta[name="apple-mobile-web-app-status-bar-style"]')
      ?.setAttribute('content', dark ? 'black-translucent' : 'default')
    setUiDigitPreference(input.usePersianDigits)
  }

  async function hydrate(): Promise<void> {
    if (hydrated.value) {
      error.value = null
      applyDocumentPreferences()
      return
    }
    loading.value = true
    error.value = null
    try {
      const remote = await userService.getPreferences()
      preferences.value = mergePreferences({ ...remote, ...loadStoredPreferences() })
    } catch (caught) {
      error.value = caught instanceof Error ? caught.message : 'تنظیمات بارگیری نشد.'
      preferences.value = mergePreferences(loadStoredPreferences())
    } finally {
      hydrated.value = true
      loading.value = false
      persist()
    }
  }

  function update(input: Partial<UserPreferences>): void {
    preferences.value = mergePreferences({
      ...preferences.value,
      ...input,
      notificationChannels: input.notificationChannels
        ? { ...preferences.value.notificationChannels, ...input.notificationChannels }
        : preferences.value.notificationChannels,
    })
    persist()
  }

  function toggleBalances(): void {
    update({ hideBalances: !preferences.value.hideBalances })
  }

  function toggleZeroBalances(): void {
    update({ hideZeroBalances: !preferences.value.hideZeroBalances })
  }

  function setTheme(value: ThemePreference): void {
    update({ theme: normalizeTheme(value) })
  }

  function saveTheme(value: ThemePreference): Promise<void> {
    const selected = normalizeTheme(value)
    const revision = ++themeSyncRevision

    // Local persistence is synchronous so navigation and reload never revert the UI.
    setTheme(selected)
    themeSyncing.value = true
    themeSyncError.value = null

    const operation = themeSyncQueue
      .catch(() => undefined)
      .then(async () => {
        // Do not send an obsolete choice that has not started syncing yet.
        if (revision !== themeSyncRevision) return
        try {
          const remote = await userService.updatePreferences({ theme: selected })
          if (revision !== themeSyncRevision || preferences.value.theme !== selected) return
          preferences.value = mergePreferences({
            ...preferences.value,
            theme: normalizeTheme(remote.theme),
          })
          persist()
        } catch (caught) {
          if (revision !== themeSyncRevision) return
          themeSyncError.value = caught instanceof Error
            ? caught.message
            : 'همگام‌سازی پوسته با حساب انجام نشد.'
          throw caught
        }
      })
      .finally(() => {
        if (revision === themeSyncRevision) themeSyncing.value = false
      })

    themeSyncQueue = operation.catch(() => undefined)
    return operation
  }

  function toggleFavorite(symbol: AssetSymbol): void {
    const current = preferences.value.favoriteAssets
    update({
      favoriteAssets: current.includes(symbol)
        ? current.filter((item) => item !== symbol)
        : [...current, symbol],
    })
  }

  async function saveRemote(input: UserPreferences = preferences.value): Promise<void> {
    loading.value = true
    error.value = null
    try {
      preferences.value = mergePreferences(await userService.updatePreferences(input))
      persist()
    } catch (caught) {
      error.value = caught instanceof Error ? caught.message : 'ذخیره تنظیمات انجام نشد.'
      throw caught
    } finally {
      loading.value = false
    }
  }

  return {
    preferences,
    hydrated,
    loading,
    error,
    themeSyncing,
    themeSyncError,
    hideBalances,
    hideZeroBalances,
    theme,
    favoriteAssets,
    apply: applyDocumentPreferences,
    preview: applyDocumentPreferences,
    hydrate,
    update,
    toggleBalances,
    toggleBalanceVisibility: toggleBalances,
    toggleZeroBalances,
    setTheme,
    saveTheme,
    toggleFavorite,
    isFavorite: (symbol: AssetSymbol) => preferences.value.favoriteAssets.includes(symbol),
    saveRemote,
  }
})
