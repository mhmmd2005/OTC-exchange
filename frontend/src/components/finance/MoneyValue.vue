<script setup lang="ts">
import { computed } from 'vue'
import { formatToman } from '@/utils/formatters'

const props = withDefaults(defineProps<{
  value: string | number
  label?: string
  hidden?: boolean
}>(), {
  label: '',
  hidden: false,
})

const amount = computed(() => props.hidden
  ? '••••••'
  : formatToman(props.value, { showCurrency: false }))
</script>

<template>
  <span class="money-value">
    <strong>
      <bdi dir="ltr">{{ amount }}</bdi>
      <span v-if="!hidden" class="money-value__unit">تومان</span>
    </strong>
    <small v-if="label">{{ label }}</small>
  </span>
</template>

<style scoped>
.money-value { display: grid; min-width: 0; gap: .12rem; line-height: 1.4; }
.money-value strong { display: flex; min-width: 0; flex-wrap: wrap; align-items: baseline; gap: .2rem; font-size: var(--font-size-sm); font-variant-numeric: tabular-nums; font-weight: 600; line-height: 1.5; }
.money-value bdi { max-width: 100%; direction: ltr; unicode-bidi: isolate; white-space: nowrap; }
.money-value__unit { flex: 0 0 auto; font-size: .82em; font-weight: 500; }
.money-value small { min-width: 0; color: var(--color-text-muted); font-size: .68rem; line-height: 1.45; overflow-wrap: break-word; }
</style>
