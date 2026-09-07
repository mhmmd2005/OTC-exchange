<script setup lang="ts">
withDefaults(defineProps<{
  label?: string
  value?: string
  tone?: 'muted' | 'danger' | 'success' | 'warning'
  id?: string
}>(), {
  label: '',
  value: '',
  tone: 'muted',
})
</script>

<template>
  <span :id="id" class="financial-field-meta" :class="`is-${tone}`">
    <span v-if="label" class="financial-field-meta__label">{{ label }}</span>
    <bdi v-if="value" class="financial-field-meta__value" dir="auto">{{ value }}</bdi>
    <span v-if="$slots.default" class="financial-field-meta__content"><slot /></span>
  </span>
</template>

<style scoped>
.financial-field-meta {
  display: flex;
  min-width: 0;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-2) var(--space-3);
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  line-height: 1.65;
}
.financial-field-meta__label,
.financial-field-meta__content { min-width: 0; overflow-wrap: anywhere; }
.financial-field-meta__value {
  min-width: 0;
  max-width: 100%;
  color: inherit;
  font-weight: 500;
  font-variant-numeric: tabular-nums;
  overflow-wrap: anywhere;
  text-align: end;
}
.financial-field-meta.is-danger { color: var(--color-danger); }
.financial-field-meta.is-success { color: var(--color-success); }
.financial-field-meta.is-warning { color: var(--color-warning); }

@media (max-width: 359px) {
  .financial-field-meta { display: grid; gap: var(--space-1); }
  .financial-field-meta__value { text-align: start; }
}
</style>
