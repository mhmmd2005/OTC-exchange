<script setup>
const props = defineProps({
  type: { type: String, default: 'button' },
  variant: { type: String, default: 'primary' },
  loading: { type: Boolean, default: false },
})
</script>

<template>
  <button :type="type" :class="['btn', variant]" :disabled="loading">
    <span v-if="loading">...</span>
    <slot v-else />
  </button>
</template>

<style scoped>
.btn { border: none; border-radius: 12px; padding: 11px 16px; font-weight: 700; transition: all .2s ease; display: inline-flex; align-items: center; justify-content: center; gap: 8px; }
.btn.primary { background: linear-gradient(135deg, #111827, #1d4ed8); color: white; }
.btn.secondary { background: var(--bg-soft); color: var(--text); }
.btn.ghost { background: transparent; color: var(--text); border: 1px solid var(--border); }
.btn:disabled { opacity: 0.7; cursor: progress; }
</style>
