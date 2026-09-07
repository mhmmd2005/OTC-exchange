<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import AppIcon from './AppIcon.vue'

const props = withDefaults(defineProps<{
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'gold' | 'success'
  size?: 'sm' | 'md' | 'lg'
  block?: boolean
  loading?: boolean
  disabled?: boolean
  to?: string | Record<string, unknown>
  icon?: string
  type?: 'button' | 'submit' | 'reset'
}>(), {
  variant: 'primary',
  size: 'md',
  block: false,
  loading: false,
  disabled: false,
  type: 'button',
})

const component = computed(() => props.to && !props.disabled ? RouterLink : 'button')
</script>

<template>
  <component
    :is="component"
    :to="to"
    :type="component === 'button' ? type : undefined"
    :disabled="component === 'button' ? disabled || loading : undefined"
    class="app-button"
    :class="[`app-button--${variant}`, `app-button--${size}`, { 'app-button--block': block, 'is-loading': loading }]"
    :aria-busy="loading || undefined"
  >
    <span v-if="loading" class="button-spinner" aria-hidden="true" />
    <AppIcon v-else-if="icon" :name="icon" :size="size === 'sm' ? 18 : 20" />
    <span><slot /></span>
  </component>
</template>

<style scoped>
.app-button {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  min-width: 0;
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  font-weight: 600;
  line-height: 1.4;
  text-align: center;
  white-space: normal;
  user-select: none;
  transition: background var(--transition-fast), border-color var(--transition-fast), color var(--transition-fast), box-shadow var(--transition-fast), transform var(--transition-fast);
}
.app-button > span:last-child { min-width: 0; overflow-wrap: anywhere; }
.app-button:not(:disabled):active { transform: translateY(1px) scale(.995); }
.app-button:disabled { cursor: not-allowed; opacity: 0.52; }
.app-button--block { width: 100%; }
.app-button--sm { min-height: var(--control-height-sm); padding-inline: var(--space-4); border-radius: var(--radius-sm); font-size: var(--font-size-sm); }
.app-button--md { min-height: var(--control-height); padding-inline: var(--space-5); font-size: var(--font-size-md); }
.app-button--lg { min-height: var(--control-height-lg); padding-inline: var(--space-6); font-size: 1rem; }
.app-button--primary { border-color: color-mix(in srgb, var(--on-primary) 18%, transparent); background: linear-gradient(180deg, var(--action-primary-hover), var(--action-primary)); color: var(--on-primary); box-shadow: 0 9px 24px var(--color-primary-shadow); }
.app-button--secondary { border-color: var(--control-border); background: var(--surface-secondary); color: var(--text-primary); box-shadow: var(--shadow-xs); }
.app-button--ghost { background: transparent; color: var(--text-secondary); }
.app-button--danger { border-color: color-mix(in srgb, var(--color-danger) 34%, transparent); background: var(--color-danger-soft); color: var(--color-danger); }
.app-button--gold { border-color: color-mix(in srgb, var(--on-gold) 18%, transparent); background: linear-gradient(180deg, var(--color-gold-hover), var(--color-gold)); color: var(--on-gold); box-shadow: 0 8px 22px rgba(141, 99, 24, .18); }
.app-button--success { border-color: color-mix(in srgb, var(--on-success) 18%, transparent); background: linear-gradient(180deg, var(--color-success-hover), var(--color-success)); color: var(--on-success); box-shadow: 0 8px 22px rgba(31, 151, 111, .2); }
.app-button:focus-visible { outline: 2px solid var(--color-border-focus); outline-offset: 2px; box-shadow: var(--shadow-focus); }
.button-spinner { width: 1.15rem; height: 1.15rem; border: 2px solid currentColor; border-inline-end-color: transparent; border-radius: 50%; animation: spin .7s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

@media (hover: hover) {
  .app-button--primary:hover:not(:disabled) { background: var(--action-primary-hover); box-shadow: 0 11px 28px var(--color-primary-shadow); }
  .app-button--secondary:hover:not(:disabled), .app-button--ghost:hover:not(:disabled) { border-color: var(--color-border-hover); background: var(--surface-tertiary); color: var(--text-primary); }
  .app-button--danger:hover:not(:disabled) { border-color: rgba(239, 116, 125, .4); background: rgba(239, 116, 125, .17); }
  .app-button--gold:hover:not(:disabled) { background: var(--color-gold-hover); }
  .app-button--success:hover:not(:disabled) { background: var(--color-success-hover); }
}
@media (hover: none), (pointer: coarse), (max-width: 767px) {
  .app-button--sm { min-height: 2.75rem; }
}
</style>
