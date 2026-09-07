<script setup lang="ts">
import { nextTick, ref } from 'vue'

const props = withDefaults(defineProps<{ modelValue: string; items: Array<{ label: string; value: string; disabled?: boolean }>; ariaLabel?: string }>(), { ariaLabel: 'انتخاب نما' })
const emit = defineEmits<{ 'update:modelValue': [value: string] }>()
const buttonGroup = ref<HTMLElement | null>(null)

async function onKeydown(event: KeyboardEvent): Promise<void> {
  if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return
  const enabled = props.items.filter((item) => !item.disabled)
  if (!enabled.length) return
  const current = Math.max(0, enabled.findIndex((item) => item.value === props.modelValue))
  let index = current
  if (event.key === 'Home') index = 0
  else if (event.key === 'End') index = enabled.length - 1
  else if (event.key === 'ArrowLeft') index = (current + 1) % enabled.length
  else index = (current - 1 + enabled.length) % enabled.length
  event.preventDefault()
  emit('update:modelValue', enabled[index]!.value)
  await nextTick()
  buttonGroup.value?.querySelector<HTMLElement>('button[aria-pressed="true"]:not(:disabled)')?.focus()
}
</script>

<template>
  <div ref="buttonGroup" class="tabs" role="group" :aria-label="ariaLabel" @keydown="onKeydown">
    <button
      v-for="item in items"
      :key="item.value"
      type="button"
      :aria-pressed="modelValue === item.value"
      :disabled="item.disabled"
      :class="{ active: modelValue === item.value }"
      @click="emit('update:modelValue', item.value)"
    >
      {{ item.label }}
    </button>
  </div>
</template>

<style scoped>
.tabs { display: grid; max-width: 100%; grid-auto-flow: column; grid-auto-columns: minmax(max-content, 1fr); gap: var(--space-1); padding: .3rem; overflow-x: auto; border: 1px solid var(--control-border); border-radius: var(--radius-md); background: var(--surface-secondary); scrollbar-width: none; }
.tabs::-webkit-scrollbar { display: none; }
button { min-height: 2.65rem; padding-inline: var(--space-4); border: 0; border-radius: calc(var(--radius-md) - .2rem); background: transparent; color: var(--text-muted); font-weight: 600; white-space: nowrap; transition: background var(--transition-fast), color var(--transition-fast), box-shadow var(--transition-fast); }
button:hover:not(:disabled) { color: var(--text-primary); }
button.active { background: var(--surface-hover); box-shadow: var(--shadow-xs); color: var(--text-primary); }
button:disabled { opacity: .45; cursor: not-allowed; }
button:focus-visible { outline-offset: -2px; }

@media (max-width: 767px) {
  .tabs { grid-auto-columns: minmax(5rem, 1fr); }
  button { min-height: 2.75rem; padding-inline: var(--space-3); }
}
</style>
