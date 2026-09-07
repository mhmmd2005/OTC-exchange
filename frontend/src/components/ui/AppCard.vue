<script setup lang="ts">
type CardVariant = 'default' | 'summary' | 'financial' | 'action' | 'data' | 'warning' | 'elevated'

withDefaults(defineProps<{
  padding?: 'none' | 'sm' | 'md' | 'lg'
  variant?: CardVariant
  interactive?: boolean
  as?: string
}>(), {
  padding: 'md',
  variant: 'default',
  interactive: false,
  as: 'section',
})
</script>

<template>
  <component
    :is="as"
    class="app-card"
    :class="[`app-card--${padding}`, `app-card--${variant}`, { 'app-card--interactive': interactive }]"
  >
    <slot />
  </component>
</template>

<style scoped>
.app-card {
  position: relative;
  min-width: 0;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-xl);
  background: var(--surface-primary);
  box-shadow: var(--shadow-xs);
}
.app-card--none { padding: 0; }
.app-card--sm { padding: var(--space-4); }
.app-card--md { padding: var(--space-5); }
.app-card--lg { padding: var(--space-7); }
.app-card--summary { border-color: var(--color-primary-border); background: linear-gradient(145deg, rgba(76, 141, 255, .13), transparent 58%), var(--surface-primary); }
.app-card--financial { border-color: var(--color-gold-border); background: linear-gradient(145deg, rgba(223, 184, 102, .07), transparent 55%), var(--surface-primary); }
.app-card--action { background: var(--surface-secondary); box-shadow: none; }
.app-card--data { border-color: var(--border-subtle); box-shadow: none; }
.app-card--warning { border-color: rgba(239, 182, 75, .24); background: linear-gradient(145deg, var(--color-warning-soft), transparent 60%), var(--surface-primary); }
.app-card--elevated { background: var(--surface-overlay); box-shadow: var(--shadow-md); }
.app-card--interactive { transition: border-color var(--transition-fast), transform var(--transition-fast), background var(--transition-fast), box-shadow var(--transition-fast); }

@media (hover: hover) {
  .app-card--interactive:hover { border-color: var(--color-border-hover); background-color: var(--surface-secondary); box-shadow: var(--shadow-sm); transform: translateY(-2px); }
}

@media (max-width: 767px) {
  .app-card { border-radius: var(--radius-lg); }
  .app-card--lg, .app-card--md { padding: var(--space-4); }
}
</style>
