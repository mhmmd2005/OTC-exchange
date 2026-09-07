<script setup lang="ts">
import { computed } from 'vue'
import AppIcon from './AppIcon.vue'
const props = defineProps<{ modelValue: number; totalPages: number }>()
defineEmits<{ 'update:modelValue': [value: number] }>()
const pages = computed(() => {
  const max = Math.min(props.totalPages, 5)
  const start = Math.max(1, Math.min(props.modelValue - 2, props.totalPages - max + 1))
  return Array.from({ length: max }, (_, index) => start + index)
})
</script>
<template>
  <nav v-if="totalPages > 1" class="pagination pagination--desktop desktop-only" aria-label="صفحه‌بندی">
    <button type="button" :disabled="modelValue <= 1" aria-label="صفحه قبل" @click="$emit('update:modelValue', modelValue - 1)"><AppIcon name="chevronRight" :size="17" /></button>
    <button v-for="page in pages" :key="page" type="button" :class="{ active: page === modelValue }" :aria-current="page === modelValue ? 'page' : undefined" @click="$emit('update:modelValue', page)">{{ page.toLocaleString('fa-IR') }}</button>
    <button type="button" :disabled="modelValue >= totalPages" aria-label="صفحه بعد" class="next" @click="$emit('update:modelValue', modelValue + 1)"><AppIcon name="chevronLeft" :size="17" /></button>
  </nav>
  <nav v-if="totalPages > 1" class="pagination pagination--mobile mobile-only" aria-label="صفحه‌بندی موبایل">
    <button type="button" :disabled="modelValue <= 1" @click="$emit('update:modelValue', modelValue - 1)"><AppIcon name="chevronRight" :size="17" /><span>قبلی</span></button>
    <span class="pagination__summary" aria-live="polite">صفحه {{ modelValue.toLocaleString('fa-IR') }} از {{ totalPages.toLocaleString('fa-IR') }}</span>
    <button type="button" :disabled="modelValue >= totalPages" class="next" @click="$emit('update:modelValue', modelValue + 1)"><span>بعدی</span><AppIcon name="chevronLeft" :size="17" /></button>
  </nav>
</template>
<style scoped>
.pagination { display: flex; flex-wrap: wrap; align-items: center; justify-content: center; gap: var(--space-2); padding: var(--space-4); border-block-start: 1px solid var(--color-border-soft); }
.pagination button { display: grid; min-width: 2.5rem; height: 2.5rem; padding-inline: .5rem; border: 1px solid var(--control-border); border-radius: var(--radius-sm); background: var(--color-surface-2); color: var(--color-text-secondary); place-items: center; transition: border-color var(--transition-fast), background var(--transition-fast), color var(--transition-fast), box-shadow var(--transition-fast); }
.pagination button.active { border-color: var(--action-primary); background: var(--action-primary); color: var(--on-primary); }
.pagination button:focus-visible { outline: 2px solid var(--color-border-focus); outline-offset: 2px; box-shadow: var(--shadow-focus); }
.pagination button:disabled { opacity: .42; cursor: not-allowed; }
.pagination--mobile { display: none !important; }
@media (hover: hover) {
  .pagination button:hover:not(:disabled, .active) { border-color: var(--color-border-hover); background: var(--color-surface-3); color: var(--color-text-primary); }
  .pagination button.active:hover { background: var(--action-primary-hover); }
}
@media (hover: none), (pointer: coarse), (max-width: 767px) {
  .pagination button { min-width: 2.75rem; height: 2.75rem; }
}
@media (max-width: 380px) {
  .pagination { gap: var(--space-1); padding-inline: var(--space-3); }
}
@media (max-width: 767px) {
  .pagination--mobile.mobile-only { display: grid !important; grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr); }
  .pagination--mobile button { display: inline-flex; width: 100%; min-width: 0; align-items: center; justify-content: center; gap: var(--space-1); }
  .pagination__summary { align-self: center; padding-inline: var(--space-2); color: var(--color-text-muted); font-size: var(--font-size-xs); white-space: nowrap; }
}
</style>
