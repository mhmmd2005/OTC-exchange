<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useNotificationsStore } from '@/stores/notifications'
import { kycAttentionLabel } from '@/utils/account'
import { formatRelativeTime, toPersianDigits } from '@/utils/formatters'
import AppIcon from '@/components/ui/AppIcon.vue'
import AppLogo from './AppLogo.vue'

defineProps<{ collapsed: boolean }>()
defineEmits<{ toggle: [] }>()

const auth = useAuthStore()
const notifications = useNotificationsStore()

const mainItems = [
  { label: 'داشبورد', icon: 'dashboard', to: '/app/dashboard' },
  { label: 'خرید و فروش', icon: 'trade', to: '/app/trade' },
  { label: 'ارزها', icon: 'markets', to: '/app/markets' },
  { label: 'کیف پول', icon: 'wallet', to: '/app/wallet' },
  { label: 'سفارش‌ها', icon: 'orders', to: '/app/orders' },
  { label: 'تراکنش‌ها', icon: 'transactions', to: '/app/transactions' },
]

const accountItems = computed(() => [
  { label: 'حساب کاربری', icon: 'profile', to: '/app/profile', badge: '' },
  { label: 'احراز هویت', icon: 'verify', to: '/app/verification', badge: kycAttentionLabel(auth.user?.kycStatus) },
  { label: 'حساب‌های بانکی', icon: 'bank', to: '/app/bank-accounts', badge: '' },
  { label: 'امنیت', icon: 'shield', to: '/app/security', badge: '' },
  { label: 'اعلان‌ها', icon: 'bell', to: '/app/notifications', badge: notifications.unreadCount ? toPersianDigits(notifications.unreadCount) : '' },
  { label: 'پشتیبانی', icon: 'help', to: '/app/support', badge: '' },
  { label: 'تنظیمات', icon: 'settings', to: '/app/settings', badge: '' },
])

const lastLogin = computed(() => auth.user?.lastLoginAt
  ? formatRelativeTime(auth.user.lastLoginAt)
  : '')
</script>

<template>
  <aside class="sidebar" :class="{ collapsed }">
    <div class="sidebar__top">
      <AppLogo :compact="collapsed" />
      <button class="collapse" type="button" :aria-label="collapsed ? 'باز کردن نوار کناری' : 'جمع کردن نوار کناری'" @click="$emit('toggle')">
        <AppIcon :name="collapsed ? 'chevronLeft' : 'chevronRight'" :size="18" />
      </button>
    </div>

    <nav aria-label="ناوبری اصلی" class="sidebar__nav">
      <div class="nav-group">
        <span v-if="!collapsed" class="nav-label">فضای مالی</span>
        <RouterLink v-for="item in mainItems" :key="item.to" :to="item.to" class="nav-item" :title="collapsed ? item.label : undefined">
          <AppIcon :name="item.icon" :size="21" />
          <span v-if="!collapsed" class="nav-item__label">{{ item.label }}</span>
        </RouterLink>
      </div>
      <div class="nav-group nav-group--account">
        <span v-if="!collapsed" class="nav-label">حساب من</span>
        <RouterLink v-for="item in accountItems" :key="item.to" :to="item.to" class="nav-item" :title="collapsed ? item.label : undefined" :aria-label="item.badge ? `${item.label}، ${item.badge}` : undefined">
          <AppIcon :name="item.icon" :size="21" />
          <span v-if="!collapsed" class="nav-item__label">{{ item.label }}</span>
          <small v-if="item.badge" class="nav-badge" :class="{ dot: collapsed }">{{ collapsed ? '' : item.badge }}</small>
        </RouterLink>
      </div>
    </nav>

    <div class="sidebar__secure" :class="{ compact: collapsed }">
      <AppIcon name="shield" :size="20" />
      <span v-if="!collapsed"><strong>اتصال امن</strong><small v-if="lastLogin">آخرین ورود: {{ lastLogin }}</small></span>
    </div>
  </aside>
</template>

<style scoped>
.sidebar { position: fixed; z-index: var(--z-nav); inset-block: 0; inset-inline-start: 0; display: flex; width: var(--sidebar-width); flex-direction: column; padding: var(--space-5) var(--space-4); border-inline-end: 1px solid var(--color-border-soft); background: var(--color-bg-sidebar); transition: width var(--transition-base); }
.sidebar.collapsed { width: var(--sidebar-collapsed); padding-inline: .75rem; }
.sidebar__top { display: flex; align-items: center; justify-content: space-between; min-height: 2.75rem; padding-inline: .25rem; }
.collapse { display: grid; width: 2.25rem; height: 2.25rem; flex: 0 0 auto; border: 1px solid var(--control-border); border-radius: var(--radius-sm); background: var(--color-surface-1); color: var(--color-text-secondary); place-items: center; }
.collapsed .collapse { position: absolute; inset-block-start: 5.1rem; inset-inline-end: -.85rem; width: 1.75rem; height: 1.75rem; border-radius: 50%; background: var(--color-surface-2); }
.sidebar__nav { display: grid; gap: var(--space-5); min-height: 0; margin-top: var(--space-8); overflow-y: auto; scrollbar-width: none; }
.sidebar__nav::-webkit-scrollbar { display: none; }
.nav-group { display: grid; gap: .3rem; }
.nav-group--account { padding-block-start: var(--space-4); border-block-start: 1px solid var(--color-border-soft); }
.nav-label { padding: 0 var(--space-3) var(--space-2); color: var(--color-text-muted); font-size: .68rem; font-weight: 600; letter-spacing: .04em; }
.nav-item { position: relative; display: flex; align-items: center; min-height: 2.8rem; gap: var(--space-3); padding-inline: var(--space-3); border: 1px solid transparent; border-radius: var(--radius-md); color: var(--color-text-secondary); transition: color var(--transition-fast), background var(--transition-fast), border-color var(--transition-fast); }
.nav-item:hover { background: var(--color-surface-2); color: var(--color-text-primary); }
.nav-item.router-link-active { border-color: var(--color-primary-border); background: var(--color-primary-soft); color: var(--brand-primary); }
.nav-item.router-link-active::before { position: absolute; inset-block: .65rem; inset-inline-start: -.75rem; width: .2rem; border-radius: var(--radius-pill); background: var(--action-primary); content: ''; }
.nav-item__label { flex: 1; white-space: nowrap; }
.nav-badge { min-width: 1.35rem; padding: .12rem .4rem; border-radius: var(--radius-pill); background: var(--color-warning-soft); color: var(--color-warning); font-size: .65rem; text-align: center; }
.nav-badge.dot { position: absolute; inset-block-start: .45rem; inset-inline-end: .4rem; width: .42rem; min-width: 0; height: .42rem; padding: 0; background: var(--color-warning); }
.collapsed .nav-item { justify-content: center; padding-inline: 0; }
.sidebar__secure { display: flex; align-items: center; gap: var(--space-3); margin-top: auto; padding: var(--space-3); border: 1px solid color-mix(in srgb, var(--color-success) 28%, transparent); border-radius: var(--radius-md); background: var(--color-success-soft); color: var(--color-success); }
.sidebar__secure span { display: grid; }
.sidebar__secure strong { font-size: var(--font-size-xs); }
.sidebar__secure small { color: var(--color-text-muted); font-size: .62rem; white-space: nowrap; }
.sidebar__secure.compact { justify-content: center; }
@media (max-width: 1199px) { .sidebar { display: none; } }
</style>
