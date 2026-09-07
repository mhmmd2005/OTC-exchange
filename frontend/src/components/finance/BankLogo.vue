<script setup lang="ts">
import { computed } from 'vue'
import { getBankIdentity } from '@/constants/banks'
import type { IranianBank } from '@/types'

const props = withDefaults(defineProps<{
  bank: Pick<IranianBank, 'id' | 'nameFa' | 'nameEn'>
  size?: 'sm' | 'md' | 'lg'
}>(), {
  size: 'md',
})

const identity = computed(() => getBankIdentity(props.bank))
const logoStyle = computed(() => ({
  '--bank-primary': identity.value.primary,
  '--bank-secondary': identity.value.secondary,
}))
</script>

<template>
  <span
    class="bank-logo"
    :class="[`bank-logo--${size}`, `bank-logo--${identity.mark}`]"
    :style="logoStyle"
    aria-hidden="true"
  >
    <svg v-if="identity.mark === 'saman'" viewBox="0 0 48 48" fill="none">
      <path d="M24 6c5 0 7.5 5.5 4.6 9.2 4.5-1.7 9.2 1.9 7.8 6.7-1 3.7-5.4 5.3-8.5 3.1 2.4 3.5.5 8.5-3.5 9.3-4.7.9-8-3.6-6-7.7-4.4 1.4-8.8-2.1-7.7-6.7.9-4 5.4-5.9 8.7-3.6C15.8 11.8 18.9 6 24 6Z" fill="currentColor" opacity=".92"/>
      <circle cx="24" cy="21.5" r="5.2" fill="white" opacity=".94"/>
      <path d="M19.7 38.4c1.5 2.3 7.3 2.3 8.8 0" stroke="var(--bank-secondary)" stroke-width="3" stroke-linecap="round"/>
    </svg>

    <svg v-else-if="identity.mark === 'mellat'" viewBox="0 0 48 48" fill="none">
      <path d="m24 5 8 8-8 8-8-8 8-8Z" fill="currentColor"/>
      <path d="m14.5 15 7.7 7.7-7.7 7.8L6.8 22.7l7.7-7.7Zm19 0 7.7 7.7-7.7 7.8-7.7-7.8 7.7-7.7ZM24 24.5l8 8-8 8-8-8 8-8Z" fill="currentColor" opacity=".82"/>
      <circle cx="24" cy="22.7" r="4.1" fill="var(--bank-secondary)"/>
    </svg>

    <svg v-else-if="identity.mark === 'pasargad'" viewBox="0 0 48 48" fill="none">
      <path d="M10 37h28M14 33h20" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
      <path d="M17 31V17l7-9 7 9v14" stroke="currentColor" stroke-width="3.2" stroke-linejoin="round"/>
      <path d="M24 10v21M12 18l5-3m19 3-5-3" stroke="var(--bank-secondary)" stroke-width="2.4" stroke-linecap="round"/>
    </svg>

    <svg v-else-if="identity.mark === 'melli'" viewBox="0 0 48 48" fill="none">
      <circle cx="24" cy="24" r="17" stroke="currentColor" stroke-width="3"/>
      <path d="M14 29c3-8 7-12 10-12s7 4 10 12M18 31c1.7-5.4 3.8-8 6-8s4.3 2.6 6 8" stroke="currentColor" stroke-width="2.8" stroke-linecap="round"/>
      <path d="m24 12 3 4-3 4-3-4 3-4Z" fill="var(--bank-secondary)"/>
      <path d="M16 34h16" stroke="var(--bank-secondary)" stroke-width="2.8" stroke-linecap="round"/>
    </svg>

    <span v-else class="bank-logo__fallback">{{ identity.monogram }}</span>
  </span>
</template>

<style scoped>
.bank-logo {
  display: grid;
  flex: 0 0 auto;
  border: 1px solid color-mix(in srgb, var(--bank-primary) 34%, transparent);
  border-radius: 1rem;
  background:
    radial-gradient(circle at 28% 18%, color-mix(in srgb, var(--bank-secondary) 34%, transparent), transparent 48%),
    color-mix(in srgb, var(--bank-primary) 17%, var(--surface-secondary));
  box-shadow: inset 0 1px 0 rgba(255,255,255,.08), 0 8px 24px color-mix(in srgb, var(--bank-primary) 13%, transparent);
  color: var(--bank-primary);
  place-items: center;
}
.bank-logo--sm { width: 2.5rem; height: 2.5rem; border-radius: .75rem; }
.bank-logo--md { width: 3rem; height: 3rem; }
.bank-logo--lg { width: 3.75rem; height: 3.75rem; border-radius: 1.15rem; }
.bank-logo svg { width: 72%; height: 72%; overflow: visible; }
.bank-logo__fallback { color: var(--bank-primary); font-size: 1.05rem; font-weight: 800; line-height: 1; }
.bank-logo--lg .bank-logo__fallback { font-size: 1.3rem; }
</style>
