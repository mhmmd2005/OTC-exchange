<script setup lang="ts">
import AppIcon from './AppIcon.vue'
defineProps<{ icon?: string; title: string; description?: string }>()
</script>

<template><div class="empty"><span class="empty__icon"><AppIcon :name="icon || 'info'" :size="28" /></span><h3>{{ title }}</h3><p v-if="description">{{ description }}</p><div v-if="$slots.default" class="empty__action"><slot /></div></div></template>

<style scoped>
.empty { display: grid; justify-items: center; padding: var(--space-10) var(--space-5); text-align: center; }
.empty__icon { display: grid; width: 3.5rem; height: 3.5rem; border-radius: 1rem; background: var(--color-primary-soft); color: var(--color-primary); place-items: center; }
h3 { margin: var(--space-4) 0 var(--space-1); font-size: var(--font-size-lg); }
p { max-width: 30rem; margin: 0; color: var(--color-text-muted); }
.empty__action { margin-top: var(--space-5); }
</style>
