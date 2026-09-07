<script setup lang="ts">
import { computed } from 'vue'
import { formatCrypto } from '@/utils/formatters'

const props = withDefaults(defineProps<{
  value: string | number
  symbol: string
  label?: string
  hidden?: boolean
}>(), {
  label: '',
  hidden: false,
})

const amount = computed(() => props.hidden
  ? '••••••'
  : formatCrypto(props.value))
</script>

<template>
  <span class="crypto-value">
    <strong>
      <bdi dir="ltr">{{ amount }}</bdi>
      <bdi v-if="!hidden" class="crypto-value__unit" dir="ltr">{{ symbol.toUpperCase() }}</bdi>
    </strong>
    <small v-if="label">{{ label }}</small>
  </span>
</template>

<style scoped>
.crypto-value { display: grid; min-width: 0; gap: .12rem; line-height: 1.4; }
.crypto-value strong { display: flex; min-width: 0; flex-wrap: wrap; align-items: baseline; gap: .24rem; font-size: var(--font-size-sm); font-variant-numeric: tabular-nums; font-weight: 600; line-height: 1.5; }
.crypto-value bdi { max-width: 100%; direction: ltr; unicode-bidi: isolate; white-space: nowrap; }
.crypto-value__unit { flex: 0 0 auto; font-size: .78em; font-weight: 550; }
.crypto-value small { min-width: 0; color: var(--color-text-muted); font-size: .68rem; line-height: 1.45; overflow-wrap: break-word; }
</style>
