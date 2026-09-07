<script setup lang="ts">
import { ref } from 'vue'
import AppIcon from './AppIcon.vue'
const props = defineProps<{ value: string; label?: string }>()
const copied = ref(false)
const copy = async () => {
  try {
    await navigator.clipboard.writeText(props.value)
    copied.value = true
    window.setTimeout(() => { copied.value = false }, 1800)
  } catch { copied.value = false }
}
</script>

<template><button type="button" class="copy-button" :aria-label="copied ? 'کپی شد' : (label || 'کپی')" @click="copy"><AppIcon :name="copied ? 'check' : 'copy'" :size="18" /><span>{{ copied ? 'کپی شد' : (label || 'کپی') }}</span></button></template>

<style scoped>
.copy-button { display: inline-flex; align-items: center; gap: var(--space-1); min-height: 2.5rem; padding-inline: var(--space-3); border: 0; border-radius: var(--radius-sm); background: var(--color-primary-soft); color: var(--color-primary); font-size: var(--font-size-sm); font-weight: 600; }
</style>
