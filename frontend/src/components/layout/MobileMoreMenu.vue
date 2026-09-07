<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useNotificationsStore } from '@/stores/notifications'
import { accountLevelLabel, kycAttentionLabel } from '@/utils/account'
import { toPersianDigits } from '@/utils/formatters'
import AppIcon from '@/components/ui/AppIcon.vue'
import AppModal from '@/components/ui/AppModal.vue'
import ThemeQuickToggle from '@/components/ui/ThemeQuickToggle.vue'
defineProps<{ modelValue: boolean }>()
defineEmits<{ 'update:modelValue': [value: boolean] }>()
const auth = useAuthStore()
const notifications = useNotificationsStore()
const fullName = computed(() => auth.user?.fullName || '')
const initials = computed(() => auth.user
  ? `${auth.user.firstName.slice(0, 1)}${auth.user.lastName.slice(0, 1)}`
  : '')
const level = computed(() => accountLevelLabel(auth.user?.accountLevel))
const items = computed(() => [
  { label: 'ارزها', icon: 'markets', to: '/app/markets', badge: '' },
  { label: 'تراکنش‌ها', icon: 'transactions', to: '/app/transactions', badge: '' },
  { label: 'احراز هویت', icon: 'verify', to: '/app/verification', badge: kycAttentionLabel(auth.user?.kycStatus) },
  { label: 'حساب بانکی', icon: 'bank', to: '/app/bank-accounts', badge: '' },
  { label: 'امنیت', icon: 'shield', to: '/app/security', badge: '' },
  { label: 'اعلان‌ها', icon: 'bell', to: '/app/notifications', badge: notifications.unreadCount ? toPersianDigits(notifications.unreadCount) : '' },
  { label: 'پشتیبانی', icon: 'help', to: '/app/support', badge: '' },
  { label: 'تنظیمات', icon: 'settings', to: '/app/settings', badge: '' },
])
</script>

<template>
  <AppModal :model-value="modelValue" title="خدمات بیشتر" description="همه بخش‌های حساب شما" @update:model-value="$emit('update:modelValue', $event)">
    <div v-if="auth.user" class="more-profile">
      <span class="avatar">{{ initials }}</span><span><strong>{{ fullName }}</strong><small v-if="level">احراز هویت {{ level }}</small></span>
      <RouterLink to="/app/profile" @click="$emit('update:modelValue', false)">مشاهده حساب</RouterLink>
    </div>
    <div class="more-grid">
      <ThemeQuickToggle mode="tile" />
      <RouterLink v-for="item in items" :key="item.to" :to="item.to" @click="$emit('update:modelValue', false)">
        <span class="icon"><AppIcon :name="item.icon" :size="22" /></span>
        <strong>{{ item.label }}</strong>
        <small v-if="item.badge">{{ item.badge }}</small>
      </RouterLink>
    </div>
  </AppModal>
</template>

<style scoped>
.more-profile { display: flex; align-items: center; gap: var(--space-3); margin-bottom: var(--space-5); padding: var(--space-4); border: 1px solid var(--color-border-soft); border-radius: var(--radius-lg); background: var(--color-surface-2); }
.avatar { display: grid; width: 2.8rem; height: 2.8rem; flex: 0 0 auto; border-radius: .9rem; background: linear-gradient(145deg, var(--action-primary-hover), var(--action-primary-active)); color: var(--on-primary); font-size: var(--font-size-sm); font-weight: 700; place-items: center; }
.more-profile > span:nth-child(2) { display: grid; flex: 1; }
.more-profile small { color: var(--color-text-muted); font-size: var(--font-size-xs); }
.more-profile a { color: var(--color-primary); font-size: var(--font-size-xs); font-weight: 600; }
.more-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: var(--space-3); }
.more-grid a { position: relative; display: flex; min-width: 0; min-height: 6.4rem; flex-direction: column; align-items: center; justify-content: center; gap: var(--space-2); border: 1px solid var(--color-border-soft); border-radius: var(--radius-md); background: var(--color-surface-2); text-align: center; }
.more-grid .icon { display: grid; width: 2.6rem; height: 2.6rem; border-radius: .8rem; background: var(--color-primary-soft); color: var(--color-primary); place-items: center; }
.more-grid strong { overflow: hidden; max-width: 100%; font-size: var(--font-size-xs); font-weight: 500; text-overflow: ellipsis; white-space: nowrap; }
.more-grid small { position: absolute; inset-block-start: .4rem; inset-inline-end: .4rem; padding: .08rem .35rem; border-radius: var(--radius-pill); background: var(--color-warning-soft); color: var(--color-warning); font-size: .58rem; }
@media (max-width: 420px) { .more-grid { grid-template-columns: repeat(3, 1fr); } }
</style>
