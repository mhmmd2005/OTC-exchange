<script lang="ts">
export interface AssetSelectAsset {
  symbol: string
  nameFa: string
  nameEn: string
  color: string
}
</script>

<script setup lang="ts">
import { computed } from 'vue'
import { formatCrypto } from '@/utils/formatters'
import AppSelect from '@/components/ui/AppSelect.vue'
import CryptoIcon from './CryptoIcon.vue'

interface AssetSelectOptionView {
  value: string
  label: string
  description?: string
  raw?: unknown
}

const props = withDefaults(defineProps<{
  modelValue: string
  assets: AssetSelectAsset[]
  balances?: Record<string, string | undefined>
  disabledSymbols?: string[]
  disabledDescriptions?: Record<string, string | undefined>
  isOptionDisabled?: (asset: AssetSelectAsset) => boolean
  disabledDescription?: (asset: AssetSelectAsset) => string | undefined
  label?: string
  ariaLabel?: string
  hint?: string
  error?: string
  loadError?: string
  disabled?: boolean
  loading?: boolean
  required?: boolean
  showBalance?: boolean
  balanceLabel?: string
}>(), {
  balances: () => ({}),
  disabledSymbols: () => [],
  disabledDescriptions: () => ({}),
  label: 'ارز مورد نظر',
  disabled: false,
  loading: false,
  required: false,
  showBalance: false,
  balanceLabel: 'موجودی',
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  change: [value: string]
  retry: []
}>()

const options = computed(() => props.assets.map((asset) => {
  const reason = disabledReason(asset)
  return {
    value: asset.symbol,
    label: asset.nameFa,
    description: reason || asset.symbol,
    keywords: `${asset.nameFa} ${asset.nameEn} ${asset.symbol}`,
    disabled: props.disabledSymbols.includes(asset.symbol) || Boolean(props.isOptionDisabled?.(asset)) || Boolean(reason),
    raw: asset,
  }
}))

function assetFor(option: AssetSelectOptionView): AssetSelectAsset | undefined {
  return option.raw as AssetSelectAsset | undefined
}

function disabledReason(asset: AssetSelectAsset): string {
  return props.disabledDescriptions[asset.symbol] || props.disabledDescription?.(asset) || ''
}

function colorFor(option: AssetSelectOptionView): string {
  return assetFor(option)?.color || '#438bff'
}

function balanceFor(symbol: string): string {
  const balance = props.balances[symbol]
  return balance === undefined ? '' : formatCrypto(balance, { symbol })
}

function disabledReasonFor(option: AssetSelectOptionView): string {
  const asset = assetFor(option)
  return asset ? disabledReason(asset) : ''
}
</script>

<template>
  <AppSelect
    :model-value="modelValue"
    :options="options"
    :label="label"
    :aria-label="ariaLabel"
    :hint="hint"
    :error="error"
    :load-error="loadError"
    :disabled="disabled"
    :loading="loading"
    :required="required"
    searchable
    search-placeholder="جست‌وجوی نام یا نماد ارز"
    empty-text="ارزی با این نام یا نماد پیدا نشد."
    @update:model-value="$emit('update:modelValue', $event)"
    @change="$emit('change', $event)"
    @retry="$emit('retry')"
  >
    <template #selected="{ option }">
      <span class="asset-select__selected">
        <CryptoIcon :symbol="option.value" :color="colorFor(option)" :size="30" />
        <span class="asset-select__identity"><strong>{{ option.label }}</strong><small dir="ltr">{{ option.value }}</small></span>
        <span v-if="showBalance && balanceFor(option.value)" class="asset-select__balance"><small>{{ balanceLabel }}</small><bdi dir="ltr">{{ balanceFor(option.value) }}</bdi></span>
      </span>
    </template>
    <template #option="{ option }">
      <span class="asset-select__option">
        <CryptoIcon :symbol="option.value" :color="colorFor(option)" size="sm" />
        <span class="asset-select__identity"><strong>{{ option.label }}</strong><small dir="ltr">{{ option.value }}</small><small v-if="disabledReasonFor(option)" class="asset-select__disabled-reason">{{ disabledReasonFor(option) }}</small></span>
        <span v-if="showBalance && balanceFor(option.value)" class="asset-select__balance"><small>{{ balanceLabel }}</small><bdi dir="ltr">{{ balanceFor(option.value) }}</bdi></span>
      </span>
    </template>
  </AppSelect>
</template>

<style scoped>
.asset-select__selected,
.asset-select__option { display: flex; width: 100%; min-width: 0; align-items: center; gap: var(--space-3); }
.asset-select__identity { display: grid; min-width: 0; flex: 1; align-content: center; gap: .05rem; line-height: 1.25; }
.asset-select__identity strong { overflow: hidden; color: var(--color-text-primary); font-size: var(--font-size-sm); font-weight: 600; text-overflow: ellipsis; white-space: nowrap; }
.asset-select__identity small { color: var(--color-text-muted); font-size: .68rem; text-align: start; }
.asset-select__identity .asset-select__disabled-reason { color: var(--color-warning); direction: rtl; font-size: .67rem; }
.asset-select__balance { display: grid; min-width: 0; max-width: 48%; justify-items: end; gap: .05rem; color: var(--color-text-secondary); text-align: end; }
.asset-select__balance small { color: var(--color-text-muted); font-size: .65rem; }
.asset-select__balance bdi { max-width: 100%; font-size: var(--font-size-xs); font-weight: 500; font-variant-numeric: tabular-nums; overflow-wrap: anywhere; }
.asset-select__option { min-height: 2.55rem; }

@media (max-width: 359px) {
  .asset-select__selected .asset-select__balance { display: none; }
  .asset-select__balance { max-width: 42%; }
}
</style>
