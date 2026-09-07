<script setup lang="ts">
import AppIcon from './AppIcon.vue'
defineProps<{ title: string; description?: string; backTo?: string }>()
</script>

<template>
  <header class="page-header" :class="{ 'page-header--contextual': Boolean(backTo) }">
    <RouterLink v-if="backTo" :to="backTo" class="back" aria-label="بازگشت"><AppIcon name="chevronRight" :size="20" /></RouterLink>
    <div class="page-header__copy">
      <h1>{{ title }}</h1>
      <p v-if="description">{{ description }}</p>
    </div>
    <div v-if="$slots.actions" class="page-header__actions"><slot name="actions" /></div>
  </header>
</template>

<style scoped>
.page-header { display: flex; align-items: center; gap: var(--space-4); margin-bottom: var(--space-6); }
.page-header__copy { min-width: 0; flex: 1; }
h1 { margin: 0; font-size: clamp(1.4rem, 2vw, var(--font-size-3xl)); font-weight: 700; letter-spacing: -.025em; }
p { margin: var(--space-1) 0 0; color: var(--color-text-muted); font-size: var(--font-size-sm); }
.page-header__actions { display: flex; align-items: center; gap: var(--space-2); }
.back { display: grid; width: 2.75rem; height: 2.75rem; flex: 0 0 auto; border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface-1); color: var(--color-text-secondary); place-items: center; }
@media (max-width: 1199px) {
  .page-header--contextual {
    position: sticky;
    z-index: var(--z-header);
    inset-block-start: 0;
    min-height: calc(var(--header-height) + var(--safe-top));
    margin-block-start: calc(0px - var(--space-6));
    margin-block-end: var(--space-6);
    margin-inline-start: calc(0px - var(--page-gutter) - var(--safe-right));
    margin-inline-end: calc(0px - var(--page-gutter) - var(--safe-left));
    padding-block: var(--safe-top) 0;
    padding-inline-start: calc(var(--page-gutter) + var(--safe-right));
    padding-inline-end: calc(var(--page-gutter) + var(--safe-left));
    border-block-end: 1px solid var(--color-border-soft);
    background: var(--color-bg-header);
    backdrop-filter: blur(16px);
  }
  .page-header--contextual .page-header__copy p { display: none; }
  .page-header--contextual h1 { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
}
@media (max-width: 767px) {
  .page-header:not(.page-header--contextual) { margin-block: var(--space-1) var(--space-5); }
  .page-header--contextual { min-height: calc(4rem + var(--safe-top)); margin-block-start: calc(0px - var(--space-4)); margin-block-end: var(--space-5); }
  h1 { font-size: var(--font-size-xl); }
  .page-header__actions :deep(.app-button > span:last-child) {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip-path: inset(50%);
    white-space: nowrap;
  }
}
</style>
