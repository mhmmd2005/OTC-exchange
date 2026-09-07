<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppIcon from '@/components/ui/AppIcon.vue'
defineProps<{ moreOpen: boolean }>()
defineEmits<{ 'update:moreOpen': [value: boolean] }>()

const route = useRoute()
const activeItem = computed(() => route.meta.mobileNav)
</script>

<template>
  <nav class="mobile-nav" aria-label="ناوبری موبایل">
    <RouterLink to="/app/dashboard" class="mobile-nav__item" :class="{ active: activeItem === 'home' }" :aria-current="activeItem === 'home' ? 'page' : undefined"><AppIcon name="home" :size="22" /><span>خانه</span></RouterLink>
    <RouterLink to="/app/trade" class="mobile-nav__item mobile-nav__trade" :class="{ active: activeItem === 'trade' }" :aria-current="activeItem === 'trade' ? 'page' : undefined"><AppIcon name="trade" :size="23" /><span>خرید/فروش</span></RouterLink>
    <RouterLink to="/app/wallet" class="mobile-nav__item" :class="{ active: activeItem === 'wallet' }" :aria-current="activeItem === 'wallet' ? 'page' : undefined"><AppIcon name="wallet" :size="22" /><span>کیف پول</span></RouterLink>
    <RouterLink to="/app/orders" class="mobile-nav__item" :class="{ active: activeItem === 'orders' }" :aria-current="activeItem === 'orders' ? 'page' : undefined"><AppIcon name="orders" :size="22" /><span>سفارش‌ها</span></RouterLink>
    <button type="button" class="mobile-nav__item" :class="{ active: moreOpen || activeItem === 'more' }" :aria-current="activeItem === 'more' ? 'page' : undefined" :aria-expanded="moreOpen" aria-haspopup="dialog" @click="$emit('update:moreOpen', true)"><AppIcon name="more" :size="23" /><span>بیشتر</span></button>
  </nav>
</template>

<style scoped>
.mobile-nav { position: fixed; z-index: var(--z-nav); inset-block-end: 0; inset-inline: 0; display: none; height: calc(var(--mobile-nav-height) + var(--safe-bottom)); padding: .45rem max(.55rem, env(safe-area-inset-right)) var(--safe-bottom) max(.55rem, env(safe-area-inset-left)); border-block-start: 1px solid var(--color-border); background: rgba(9, 21, 34, .96); backdrop-filter: blur(16px); grid-template-columns: repeat(5, 1fr); }
.mobile-nav__item { display: flex; min-width: 0; min-height: 3.25rem; flex-direction: column; align-items: center; justify-content: center; gap: .2rem; border: 0; border-radius: var(--radius-sm); background: transparent; color: var(--color-text-muted); font-size: .65rem; }
.mobile-nav__item.active { color: var(--color-primary); }
.mobile-nav__item.active::before { position: absolute; inset-block-start: -.45rem; width: 1.8rem; height: .16rem; border-radius: var(--radius-pill); background: var(--action-primary); box-shadow: 0 0 12px color-mix(in srgb, var(--action-primary) 55%, transparent); content: ''; }
.mobile-nav__item { position: relative; }
.mobile-nav__trade { color: var(--color-text-secondary); }
.mobile-nav__trade.active { color: var(--color-primary); }
@media (max-width: 1199px) { .mobile-nav { display: grid; } }
</style>
