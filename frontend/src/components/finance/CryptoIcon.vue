<script setup lang="ts">
import { computed } from 'vue'

type CryptoIconSize = 'sm' | 'md' | 'lg' | number

const props = withDefaults(defineProps<{
  symbol: string
  size?: CryptoIconSize
  color?: string
}>(), {
  size: 'md',
  color: '#438bff',
})

const normalizedSymbol = computed(() => props.symbol.trim().toUpperCase())
const pixelSize = computed(() => {
  if (typeof props.size === 'number') return props.size
  return { sm: 32, md: 42, lg: 56 }[props.size]
})
const assetColor = computed(() => ({
  USDT: '#26a17b',
  BTC: '#f7931a',
  ETH: '#627eea',
  TRX: '#ef3340',
  TON: '#0098ea',
  IRT: '#d6a73a',
}[normalizedSymbol.value] ?? props.color))
const isKnown = computed(() => ['USDT', 'BTC', 'ETH', 'TRX', 'TON', 'IRT'].includes(normalizedSymbol.value))
const fallbackText = computed(() => normalizedSymbol.value === 'IRT' ? 'ت' : normalizedSymbol.value.slice(0, 1))
</script>

<template>
  <span
    class="crypto-icon"
    :style="{ '--crypto-color': assetColor, '--crypto-size': `${pixelSize}px` }"
    aria-hidden="true"
  >
    <svg v-if="normalizedSymbol === 'USDT'" viewBox="0 0 40 40" focusable="false">
      <circle cx="20" cy="20" r="20" fill="var(--crypto-color)" />
      <path fill="#fff" d="M22.7 18.1v-3h6.8v-4.5H10.6v4.5h6.8v3c-5.5.3-9.6 1.3-9.6 2.6s4.1 2.3 9.6 2.6v9.4h5.3v-9.4c5.5-.3 9.5-1.3 9.5-2.6s-4-2.3-9.5-2.6Zm0 4v-.1h-5.3v.1c-4.3-.2-7.4-.8-7.4-1.5s3.1-1.2 7.4-1.5v2.4h5.3v-2.4c4.2.2 7.3.8 7.3 1.5s-3.1 1.3-7.3 1.5Z" />
    </svg>

    <svg v-else-if="normalizedSymbol === 'BTC'" viewBox="0 0 40 40" focusable="false">
      <circle cx="20" cy="20" r="20" fill="var(--crypto-color)" />
      <path fill="#fff" d="m25.8 18.8c2.4-1.2 3.5-3.2 2.5-5.8-1.2-3.1-4.4-3.5-7.9-2.9l-.7-3-2.4.6.7 2.9-1.9.5-.7-2.9-2.4.6.7 3-4.8 1.2.7 2.7s1.8-.5 1.8-.4c1-.3 1.5.3 1.7.9l1.9 8.1c.1.4 0 1.1-.8 1.3.1 0-1.8.4-1.8.4l.2 3.2 4.8-1.2.7 3 2.4-.6-.7-3 1.9-.5.7 3 2.4-.6-.7-3.1c4.1-1.2 6.8-3.1 6.2-7-.4-3.1-2.2-4.1-4.5-4.4Zm-8.4-4.5c1.7-.4 7-1.8 7.7 1.6.7 3.2-4.4 4-6.2 4.4l-1.5-6Zm3 10.7-1.7-7.1c2.1-.5 8.4-2.3 9.2 1.4.9 3.6-5.4 5.2-7.5 5.7Z" transform="scale(.82) translate(4.2 4.2)" />
    </svg>

    <svg v-else-if="normalizedSymbol === 'ETH'" viewBox="0 0 40 40" focusable="false">
      <circle cx="20" cy="20" r="20" fill="var(--crypto-color)" />
      <path fill="#fff" fill-opacity=".96" d="m20 5 9.2 15.2L20 25.6l-9.2-5.4L20 5Z" />
      <path fill="#dbe4ff" d="m20 27.2 9.2-5.4L20 35l-9.2-13.2 9.2 5.4Z" />
      <path fill="#c6d3ff" d="M20 5v20.6l-9.2-5.4L20 5Z" />
    </svg>

    <svg v-else-if="normalizedSymbol === 'TRX'" viewBox="0 0 40 40" focusable="false">
      <circle cx="20" cy="20" r="20" fill="var(--crypto-color)" />
      <path d="m8.5 9.2 22.8 4-13.9 18.4L8.5 9.2Zm3.2 2.8 5.9 15 2-10.4-7.9-4.6Zm2.1-1 7 4 6.8-.9-13.8-3.1Zm7.6 6.1-2 10.3 8.3-11.1-6.3.8Z" fill="none" stroke="#fff" stroke-width="1.7" stroke-linejoin="round" />
    </svg>

    <svg v-else-if="normalizedSymbol === 'TON'" viewBox="0 0 40 40" focusable="false">
      <circle cx="20" cy="20" r="20" fill="var(--crypto-color)" />
      <path d="M10.3 12.6c.8-1.5 2.2-2.4 3.9-2.4h11.6c1.7 0 3.1.9 3.9 2.4.5 1 .4 2.2-.3 3.1L21.8 28c-.8 1.3-2.8 1.3-3.6 0l-7.6-12.3c-.7-.9-.8-2.1-.3-3.1Z" fill="none" stroke="#fff" stroke-width="2" />
      <path d="M13 13.8h14L20 26 13 13.8Zm7 .3v11.3" fill="none" stroke="#fff" stroke-width="1.7" stroke-linejoin="round" />
    </svg>

    <span v-else class="crypto-icon__fallback" :class="{ 'is-known': isKnown }">{{ fallbackText }}</span>
  </span>
</template>

<style scoped>
.crypto-icon {
  display: inline-grid;
  width: var(--crypto-size);
  height: var(--crypto-size);
  flex: 0 0 auto;
  overflow: hidden;
  border: 1px solid color-mix(in srgb, var(--crypto-color), white 18%);
  border-radius: 50%;
  background: color-mix(in srgb, var(--crypto-color), transparent 80%);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, .12);
  direction: ltr;
  place-items: center;
}
.crypto-icon svg { display: block; width: 100%; height: 100%; }
.crypto-icon__fallback {
  display: grid;
  width: 100%;
  height: 100%;
  background: color-mix(in srgb, var(--crypto-color), transparent 82%);
  color: color-mix(in srgb, var(--crypto-color), white 34%);
  font-size: calc(var(--crypto-size) * .32);
  font-weight: 750;
  place-items: center;
}
</style>
