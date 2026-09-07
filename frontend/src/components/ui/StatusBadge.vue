<script setup lang="ts">
import { computed } from 'vue'
import { getStatusDefinition, type StatusDomain } from '@/constants/statuses'
const props = defineProps<{ domain: StatusDomain; status: string; label?: string }>()
const definition = computed(() => getStatusDefinition(props.domain, props.status))
</script>
<template><span class="status" :class="`status--${definition.tone}`"><i aria-hidden="true" /><span>{{ label || definition.label }}</span></span></template>
<style scoped>
.status { display: inline-flex; width: max-content; max-width: 100%; align-items: center; gap: .4rem; min-height: 1.7rem; padding: .18rem .58rem; border: 1px solid transparent; border-radius: var(--radius-pill); font-size: var(--font-size-xs); font-weight: 600; line-height: 1.35; white-space: nowrap; }
.status i { width: .38rem; height: .38rem; border-radius: 50%; background: currentColor; }
.status--neutral { border-color: var(--border-default); background: var(--surface-secondary); color: var(--text-muted); }
.status--info { border-color: rgba(99,179,237,.18); background: var(--color-info-soft); color: var(--color-info); }
.status--warning { border-color: rgba(242,184,75,.18); background: var(--color-warning-soft); color: var(--color-warning); }
.status--success { border-color: rgba(53,201,149,.18); background: var(--color-success-soft); color: var(--color-success); }
.status--danger { border-color: rgba(240,108,117,.18); background: var(--color-danger-soft); color: var(--color-danger); }
</style>
