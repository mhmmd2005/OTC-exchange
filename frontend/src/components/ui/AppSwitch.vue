<script setup lang="ts">
defineProps<{ modelValue: boolean; label?: string; description?: string; disabled?: boolean }>()
defineEmits<{ 'update:modelValue': [value: boolean] }>()
</script>

<template>
  <label class="switch-row" :class="{ disabled }">
    <span v-if="label || description" class="switch-copy">
      <strong v-if="label">{{ label }}</strong>
      <small v-if="description">{{ description }}</small>
    </span>
    <input class="sr-only" type="checkbox" :checked="modelValue" :disabled="disabled" @change="$emit('update:modelValue', ($event.target as HTMLInputElement).checked)" />
    <span class="switch" aria-hidden="true"><span /></span>
  </label>
</template>

<style scoped>
.switch-row { display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); cursor: pointer; }
.switch-row.disabled { opacity: .5; cursor: not-allowed; }
.switch-copy { display: grid; gap: var(--space-1); }
.switch-copy strong { font-size: var(--font-size-md); font-weight: 500; }
.switch-copy small { color: var(--color-text-muted); font-size: var(--font-size-sm); }
.switch { position: relative; display: block; width: 3rem; height: 1.75rem; flex: 0 0 auto; border: 1px solid var(--color-border); border-radius: var(--radius-pill); background: var(--color-surface-3); transition: background var(--transition-fast), border-color var(--transition-fast); }
.switch span { position: absolute; inset-block-start: .2rem; inset-inline-start: .22rem; width: 1.25rem; height: 1.25rem; border-radius: 50%; background: var(--color-text-muted); transition: transform var(--transition-base), background var(--transition-fast); }
input:checked + .switch { border-color: var(--color-primary); background: var(--color-primary); }
input:checked + .switch span { transform: translateX(-1.2rem); background: white; }
input:focus-visible + .switch { outline: 2px solid var(--color-border-focus); outline-offset: 3px; }
</style>
