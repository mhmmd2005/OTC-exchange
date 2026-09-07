<script setup lang="ts">
import CryptoIcon from './CryptoIcon.vue'

withDefaults(defineProps<{
  symbol: string
  color?: string
  size?: 'sm' | 'md' | 'lg'
}>(), {
  color: '#438bff',
  size: 'md',
})
</script>

<template>
  <CryptoIcon :symbol="symbol" :color="color" :size="size" />
</template>
