<script setup lang="ts">
import { computed, ref, useId, useSlots, watch } from 'vue'
import { formatCrypto, formatToman, parseFinancialInput } from '@/utils/formatters'
import FinancialFieldMeta from './FinancialFieldMeta.vue'

const props = withDefaults(defineProps<{
  modelValue: string
  label: string
  suffix: string
  type?: 'toman' | 'crypto'
  balance?: string
  balanceLabel?: string
  error?: string
  disabled?: boolean
  maxFractionDigits?: number
}>(), { type: 'toman', balanceLabel: 'موجودی', maxFractionDigits: 8, disabled: false })

const emit = defineEmits<{ 'update:modelValue': [value: string]; focus: []; blur: [] }>()
const slots = useSlots()
const focused = ref(false)
const local = ref('')
const controlId = `amount-${useId().replace(/:/g, '')}`
const metaId = `${controlId}-meta`
const messageId = `${controlId}-message`

const formatted = computed(() => {
  if (!props.modelValue) return ''
  return props.type === 'toman'
    ? formatToman(props.modelValue, { showCurrency: false, usePersianDigits: true })
    : formatCrypto(props.modelValue, { maximumFractionDigits: props.maxFractionDigits, usePersianDigits: true })
})

const formattedBalance = computed(() => props.balance === undefined
  ? ''
  : props.type === 'toman'
    ? formatToman(props.balance)
    : formatCrypto(props.balance, { symbol: props.suffix }))

const describedBy = computed(() => [
  props.balance !== undefined ? metaId : '',
  props.error || slots.hint ? messageId : '',
].filter(Boolean).join(' ') || undefined)

watch(() => props.modelValue, () => { if (!focused.value) local.value = formatted.value }, { immediate: true })

const onInput = (event: Event) => {
  const raw = (event.target as HTMLInputElement).value
  local.value = raw
  emit('update:modelValue', parseFinancialInput(raw, { allowNegative: false, maxFractionDigits: props.type === 'toman' ? 0 : props.maxFractionDigits }))
}

const onFocus = () => {
  focused.value = true
  local.value = props.modelValue
  emit('focus')
}

const onBlur = () => {
  focused.value = false
  local.value = formatted.value
  emit('blur')
}
</script>

<template>
  <div class="amount-field">
    <label class="amount-field__label" :for="controlId">{{ label }}</label>
    <span class="amount-field__control" :class="{ error, disabled }">
      <input
        :id="controlId"
        :value="focused ? local : formatted"
        type="text"
        inputmode="decimal"
        autocomplete="off"
        :placeholder="type === 'toman' ? '۰' : '۰٫۰۰'"
        :disabled="disabled"
        :aria-label="label"
        :aria-invalid="!!error"
        :aria-describedby="describedBy"
        dir="ltr"
        @input="onInput"
        @focus="onFocus"
        @blur="onBlur"
      />
      <strong>{{ suffix }}</strong>
    </span>
    <div v-if="balance !== undefined || error || $slots.hint" class="amount-field__meta">
      <FinancialFieldMeta v-if="balance !== undefined" :id="metaId" :label="balanceLabel" :value="formattedBalance" />
      <FinancialFieldMeta v-if="error" :id="messageId" :label="error" tone="danger" role="alert" />
      <FinancialFieldMeta v-else-if="$slots.hint" :id="messageId"><slot name="hint" /></FinancialFieldMeta>
    </div>
  </div>
</template>

<style scoped>
.amount-field { display: grid; gap: var(--space-2); }
.amount-field__label { color: var(--color-text-secondary); font-size: var(--font-size-sm); }
.amount-field__control { display: flex; align-items: center; min-height: 4.35rem; gap: var(--space-3); padding-inline: var(--space-4); border: 1px solid var(--color-border); border-radius: var(--radius-lg); background: var(--color-surface-2); transition: border-color var(--transition-fast), box-shadow var(--transition-fast), background var(--transition-fast); }
.amount-field__control:focus-within { border-color: var(--color-border-focus); background: var(--color-surface-1); box-shadow: var(--shadow-focus); }
.amount-field__control.error { border-color: var(--color-danger); }
.amount-field__control.disabled { opacity: .55; }
input { width: 100%; min-width: 0; border: 0; outline: 0; background: transparent; color: var(--color-text-primary); font-size: clamp(1.25rem, 3vw, 1.65rem); font-weight: 600; text-align: left; caret-color: var(--color-primary); font-variant-numeric: tabular-nums; }
input::placeholder { color: var(--color-text-muted); }
.amount-field__control strong { flex: 0 0 auto; color: var(--color-text-secondary); font-size: var(--font-size-md); font-weight: 600; direction: ltr; }
.amount-field__meta { display: grid; min-width: 0; gap: var(--space-1); }
@media (max-width: 767px) { .amount-field__control { min-height: 4rem; } }
</style>
