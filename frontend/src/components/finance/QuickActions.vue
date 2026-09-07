<script setup lang="ts">
import AppIcon from '@/components/ui/AppIcon.vue'
const actions = [
  { label: 'خرید ارز', description: 'از روشا', icon: 'download', to: '/app/trade?side=buy&asset=USDT', tone: 'blue' },
  { label: 'فروش ارز', description: 'به روشا', icon: 'upload', to: '/app/trade?side=sell&asset=USDT', tone: 'green' },
  { label: 'واریز تومان', description: 'افزایش موجودی', icon: 'arrowDown', to: '/app/deposit/toman', tone: 'gold' },
  { label: 'برداشت تومان', description: 'به حساب بانکی', icon: 'arrowUp', to: '/app/withdraw/toman', tone: 'purple' },
]
</script>
<template>
  <div class="quick-actions">
    <RouterLink v-for="item in actions" :key="item.to" :to="item.to" :class="`tone-${item.tone}`">
      <span class="action-icon"><AppIcon :name="item.icon" :size="21" /></span>
      <span class="action-copy"><strong>{{ item.label }}</strong><small>{{ item.description }}</small></span>
      <AppIcon class="action-chevron" name="chevronLeft" :size="16" />
    </RouterLink>
  </div>
</template>
<style scoped>
.quick-actions { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: var(--space-3); }
a { display: flex; min-width: 0; min-height: 5rem; align-items: center; gap: var(--space-3); padding: var(--space-3); border: 1px solid var(--color-border); border-radius: var(--radius-lg); background: linear-gradient(145deg, var(--color-surface-1), var(--color-surface-2)); transition: border-color var(--transition-fast), transform var(--transition-fast), background var(--transition-fast); }
a:hover { border-color: var(--color-border-hover); background: var(--color-surface-2); transform: translateY(-1px); }
a > span { display: grid; width: 2.75rem; height: 2.75rem; flex: 0 0 auto; border-radius: .85rem; place-items: center; }
a .action-copy { display: grid; width: auto; height: auto; min-width: 0; flex: 1; align-content: center; justify-items: start; border-radius: 0; }
.action-copy strong { overflow: hidden; max-width: 100%; font-size: var(--font-size-sm); font-weight: 600; text-overflow: ellipsis; white-space: nowrap; }
.action-copy small { overflow: hidden; max-width: 100%; margin-top: .1rem; color: var(--color-text-muted); font-size: .68rem; text-overflow: ellipsis; white-space: nowrap; }
.action-chevron { flex: 0 0 auto; color: var(--color-text-muted); transition: color var(--transition-fast), translate var(--transition-fast); }
a:hover .action-chevron { color: var(--color-text-secondary); translate: -2px 0; }
.tone-blue .action-icon { background: var(--color-primary-soft); color: var(--color-primary); }
.tone-green .action-icon { background: var(--color-success-soft); color: var(--color-success); }
.tone-gold .action-icon { background: var(--color-gold-soft); color: var(--color-gold); }
.tone-purple .action-icon { background: rgba(154, 112, 255, .12); color: #b396ff; }
@media (max-width: 1180px) and (min-width: 768px) { .quick-actions { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 767px) {
  .quick-actions { gap: var(--space-2); }
  a { min-height: 5.35rem; flex-direction: column; justify-content: center; gap: .4rem; padding: var(--space-2); }
  a > span { width: 2.55rem; height: 2.55rem; }
  a .action-copy { display: block; width: 100%; flex: 0 0 auto; text-align: center; }
  .action-copy strong { display: block; font-size: .72rem; }
  .action-copy small, .action-chevron { display: none; }
}
@media (max-width: 420px) { .quick-actions { grid-template-columns: repeat(2, minmax(0, 1fr)); } a { min-height: 4.7rem; flex-direction: row; } a .action-copy { width: auto; flex: 1; text-align: start; } }
</style>
