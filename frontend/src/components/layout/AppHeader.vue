<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useMarketStore } from '@/stores/markets'
import { useNotificationsStore } from '@/stores/notifications'
import { accountLevelLabel } from '@/utils/account'
import { formatRelativeTime, toPersianDigits } from '@/utils/formatters'
import AppIcon from '@/components/ui/AppIcon.vue'
import ThemeQuickToggle from '@/components/ui/ThemeQuickToggle.vue'
import AppLogo from './AppLogo.vue'

const router = useRouter()
const auth = useAuthStore()
const markets = useMarketStore()
const notifications = useNotificationsStore()
const search = ref('')
const searchInput = ref<HTMLInputElement | null>(null)
const profileTrigger = ref<HTMLButtonElement | null>(null)
const profileOpen = ref(false)
const logoutError = ref('')
const fullName = computed(() => auth.user?.fullName || '')
const firstName = computed(() => auth.user?.firstName || '')
const initials = computed(() => auth.user
  ? `${auth.user.firstName.slice(0, 1)}${auth.user.lastName.slice(0, 1)}`
  : '')
const level = computed(() => accountLevelLabel(auth.user?.accountLevel))
const ratesUpdated = computed(() => markets.lastUpdated
  ? `آخرین به‌روزرسانی نرخ‌ها: ${formatRelativeTime(markets.lastUpdated)}`
  : '')
const mobile = computed(() => {
  const value = auth.user?.mobile
  return value ? `${value.slice(0, 4)}•••${value.slice(-4)}` : ''
})
const notificationLabel = computed(() => notifications.unreadCount
  ? `${toPersianDigits(notifications.unreadCount)} اعلان خوانده‌نشده`
  : 'اعلان‌ها')
const submitSearch = () => {
  const value = search.value.trim()
  if (value) router.push({ path: '/app/markets', query: { q: value } })
}
const logout = async () => {
  profileOpen.value = false
  logoutError.value = ''
  try {
    await auth.logout()
  } catch (error) {
    logoutError.value = error instanceof Error
      ? error.message
      : 'خروج کامل نشد. اتصال را بررسی و دوباره تلاش کنید.'
    profileOpen.value = true
    return
  }
  await router.push('/auth/login')
}
const closeProfile = (event: MouseEvent) => {
  if (!(event.target as Element).closest('.profile-menu')) profileOpen.value = false
}
const onShortcut = (event: KeyboardEvent) => {
  if (
    event.key === 'Escape'
    && profileOpen.value
    && event.target instanceof Element
    && event.target.closest('.profile-menu')
  ) {
    event.preventDefault()
    profileOpen.value = false
    void nextTick(() => profileTrigger.value?.focus({ preventScroll: true }))
    return
  }
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
    event.preventDefault()
    searchInput.value?.focus()
  }
}
window.addEventListener('click', closeProfile)
onMounted(() => {
  window.addEventListener('keydown', onShortcut)
  void notifications.fetchUnreadCount().catch(() => undefined)
})
onBeforeUnmount(() => {
  window.removeEventListener('click', closeProfile)
  window.removeEventListener('keydown', onShortcut)
})
</script>

<template>
  <header class="app-header">
    <AppLogo class="mobile-logo" compact />
    <div class="header-greeting desktop-only">
      <strong v-if="firstName">سلام {{ firstName }}، روزت روشن</strong>
      <small v-if="ratesUpdated"><span class="live-dot" /> {{ ratesUpdated }}</small>
    </div>
    <form class="header-search desktop-only" role="search" @submit.prevent="submitSearch">
      <AppIcon name="search" :size="19" />
      <input ref="searchInput" v-model="search" type="search" placeholder="جست‌وجوی نام یا نماد ارز…" aria-label="جست‌وجوی ارز" />
      <kbd>⌘ K</kbd>
    </form>
    <div class="header-actions">
      <ThemeQuickToggle />
      <RouterLink to="/app/notifications" class="header-icon" :aria-label="notificationLabel">
        <AppIcon name="bell" :size="21" /><span v-if="notifications.unreadCount" class="notification-dot">{{ notifications.unreadCount.toLocaleString('fa-IR') }}</span>
      </RouterLink>
      <div v-if="auth.user" class="profile-menu">
        <button ref="profileTrigger" type="button" class="profile-trigger" aria-label="منوی حساب کاربری" aria-controls="profile-dropdown" :aria-expanded="profileOpen" @click.stop="profileOpen = !profileOpen">
          <span class="avatar">{{ initials }}</span>
          <span class="profile-copy desktop-only"><strong>{{ fullName }}</strong><small v-if="level">{{ level }}</small></span>
          <AppIcon class="desktop-only" name="chevronDown" :size="16" />
        </button>
        <Transition name="drop">
          <div v-if="profileOpen" id="profile-dropdown" class="profile-dropdown">
            <div class="profile-summary"><span class="avatar large">{{ initials }}</span><span><strong>{{ fullName }}</strong><small class="ltr">{{ mobile }}</small></span></div>
            <p v-if="logoutError" class="logout-error" role="alert">{{ logoutError }}</p>
            <RouterLink to="/app/profile" @click="profileOpen = false"><AppIcon name="profile" :size="19" /> حساب کاربری</RouterLink>
            <RouterLink to="/app/security" @click="profileOpen = false"><AppIcon name="shield" :size="19" /> امنیت حساب</RouterLink>
            <button type="button" class="logout" @click="logout"><AppIcon name="logout" :size="19" /> خروج از حساب</button>
          </div>
        </Transition>
      </div>
    </div>
  </header>
</template>

<style scoped>
.app-header { --header-gutter: var(--space-8); position: sticky; z-index: var(--z-header); inset-block-start: 0; display: flex; align-items: center; min-height: calc(var(--header-height) + var(--safe-top)); gap: var(--space-5); padding-block: var(--safe-top) 0; padding-right: calc(var(--header-gutter) + var(--safe-right)); padding-left: calc(var(--header-gutter) + var(--safe-left)); border-block-end: 1px solid var(--color-border-soft); background: var(--color-bg-header); backdrop-filter: blur(16px); }
.mobile-logo { display: none; }
.header-greeting { display: grid; min-width: 13rem; line-height: 1.35; }
.header-greeting strong { font-size: var(--font-size-md); }
.header-greeting small { display: flex; align-items: center; gap: var(--space-2); margin-top: .2rem; color: var(--color-text-muted); font-size: var(--font-size-xs); }
.live-dot { width: .42rem; height: .42rem; border-radius: 50%; background: var(--color-success); box-shadow: 0 0 0 4px var(--color-success-soft); }
.header-search { display: flex; width: min(29rem, 38vw); min-width: 0; min-height: 2.75rem; align-items: center; margin-inline: auto; gap: var(--space-2); padding-inline: var(--space-3); border: 1px solid var(--control-border); border-radius: var(--radius-md); background: var(--color-surface-1); color: var(--color-text-muted); }
.header-search:focus-within { border-color: var(--color-border-focus); box-shadow: var(--shadow-focus); }
.header-search input { width: 100%; min-width: 0; border: 0; outline: 0; background: transparent; }
.header-search input::placeholder { color: var(--color-text-muted); }
kbd { padding: .1rem .45rem; border: 1px solid var(--color-border); border-radius: .35rem; background: var(--color-surface-2); color: var(--color-text-muted); font-family: inherit; font-size: .65rem; direction: ltr; }
.header-actions { display: flex; flex: 0 0 auto; align-items: center; gap: var(--space-2); }
.header-icon { position: relative; display: grid; width: 2.75rem; height: 2.75rem; border: 1px solid var(--control-border); border-radius: var(--radius-md); background: var(--color-surface-1); color: var(--color-text-secondary); place-items: center; }
.notification-dot { position: absolute; inset-block-start: -.3rem; inset-inline-start: -.25rem; display: grid; min-width: 1.15rem; height: 1.15rem; padding-inline: .2rem; border: 2px solid var(--color-bg-app); border-radius: var(--radius-pill); background: var(--color-danger); color: var(--on-danger); font-size: .58rem; font-weight: 700; place-items: center; }
.profile-menu { position: relative; }
.profile-trigger { display: flex; align-items: center; gap: var(--space-2); min-height: 2.75rem; padding: .25rem .3rem .25rem var(--space-3); border: 1px solid var(--control-border); border-radius: var(--radius-md); background: var(--color-surface-1); }
.avatar { display: grid; width: 2.15rem; height: 2.15rem; flex: 0 0 auto; border-radius: .7rem; background: linear-gradient(145deg, var(--action-primary-hover), var(--action-primary-active)); color: var(--on-primary); font-size: var(--font-size-xs); font-weight: 700; place-items: center; }
.avatar.large { width: 2.75rem; height: 2.75rem; border-radius: .85rem; }
.profile-copy { display: grid; min-width: 6rem; line-height: 1.25; text-align: start; }
.profile-copy strong { font-size: var(--font-size-xs); }
.profile-copy small { color: var(--color-text-muted); font-size: .62rem; }
.profile-dropdown { position: absolute; inset-block-start: calc(100% + .65rem); inset-inline-end: 0; width: 15rem; padding: var(--space-2); border: 1px solid var(--color-border); border-radius: var(--radius-lg); background: var(--color-surface-raised); box-shadow: var(--shadow-md); }
.profile-summary { display: flex; align-items: center; gap: var(--space-3); margin: var(--space-2); padding-bottom: var(--space-3); border-block-end: 1px solid var(--color-border-soft); }
.profile-summary span:last-child { display: grid; }
.profile-summary small { color: var(--color-text-muted); font-size: var(--font-size-xs); }
.logout-error { margin: 0 var(--space-2) var(--space-2); padding: var(--space-2) var(--space-3); border: 1px solid color-mix(in srgb, var(--color-danger) 28%, transparent); border-radius: var(--radius-sm); background: var(--color-danger-soft); color: var(--color-danger); font-size: var(--font-size-xs); line-height: 1.7; }
.profile-dropdown a, .profile-dropdown > button { display: flex; width: 100%; align-items: center; gap: var(--space-3); min-height: 2.75rem; padding-inline: var(--space-3); border: 0; border-radius: var(--radius-sm); background: transparent; color: var(--color-text-secondary); }
.profile-dropdown a:hover, .profile-dropdown > button:hover { background: var(--color-surface-3); color: var(--color-text-primary); }
.profile-dropdown .logout { border-block-start: 1px solid var(--color-border-soft); color: var(--color-danger); }
.drop-enter-active, .drop-leave-active { transition: opacity var(--transition-fast), transform var(--transition-fast); transform-origin: top left; }
.drop-enter-from, .drop-leave-to { opacity: 0; transform: translateY(-.35rem) scale(.97); }
@media (max-width: 1199px) { .app-header { --header-gutter: var(--space-5); } .mobile-logo { display: inline-flex; } .header-greeting { display: none; } .header-search { width: min(31rem,58vw); } .profile-copy,.profile-trigger > svg { display: none; }.profile-trigger { padding: .25rem; } }
@media (max-width: 900px) and (min-width: 768px) { .header-search kbd { display: none; } }
@media (max-width: 767px) { .app-header { --header-gutter: var(--space-4); min-height: calc(4rem + var(--safe-top)); gap: var(--space-3); } .header-actions { margin-inline-start: auto; gap: var(--space-1); } .header-icon { width: 2.6rem; height: 2.6rem; } .profile-trigger { padding: .2rem; border: 0; background: transparent; } .profile-dropdown { position: fixed; inset-block-start: calc(4rem + var(--safe-top)); right: calc(var(--space-4) + var(--safe-right)); left: calc(var(--space-4) + var(--safe-left)); width: auto; } }
</style>
