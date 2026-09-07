<script setup lang="ts">withDefaults(defineProps<{ compact?: boolean; inverse?: boolean; to?: string }>(), { compact: false, inverse: false, to: '/app/dashboard' })</script>
<template>
  <RouterLink :to="to" class="brand" :class="{ compact, inverse }" aria-label="روشا، صفحه اصلی">
    <img src="/icons/rosha-mark.svg" alt="" width="40" height="40" />
    <span v-if="!compact" class="brand__copy"><strong>روشا</strong><small>دارایی دیجیتال</small></span>
  </RouterLink>
</template>
<style scoped>
.brand { display: inline-flex; align-items: center; gap: .75rem; min-width: 0; }
img { width: 2.5rem; height: 2.5rem; flex: 0 0 auto; filter: drop-shadow(0 8px 15px rgba(67,139,255,.18)); }
.brand__copy { display: grid; line-height: 1.25; white-space: nowrap; }
.brand__copy strong { font-size: 1.25rem; font-weight: 700; letter-spacing: -.04em; }
.brand__copy small { color: var(--color-text-muted); font-size: .66rem; letter-spacing: .02em; }
.compact img { width: 2.4rem; height: 2.4rem; }
</style>
