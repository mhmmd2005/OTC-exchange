<script setup lang="ts">
import type { BankAccount } from '@/types'
import { formatMaskedCardOverview, formatMaskedIbanOverview } from '@/utils/formatters'
import BankLogo from '@/components/finance/BankLogo.vue'
import AppIcon from '@/components/ui/AppIcon.vue'

defineProps<{
  accounts: BankAccount[]
  modelValue: string
  label?: string
  error?: string
}>()

defineEmits<{ 'update:modelValue': [value: string] }>()
</script>

<template>
  <fieldset class="bank-picker" :aria-invalid="!!error">
    <legend>{{ label || 'حساب بانکی تأییدشده' }}</legend>
    <div class="bank-picker__list">
      <label
        v-for="account in accounts"
        :key="account.id"
        class="bank-option"
        :class="{ selected: modelValue === account.id }"
      >
        <input
          type="radio"
          name="verified-bank-account"
          :value="account.id"
          :checked="modelValue === account.id"
          @change="$emit('update:modelValue', account.id)"
        >
        <BankLogo :bank="account.bank" size="md" />
        <span class="bank-copy">
          <span>
            <strong>{{ account.bank.nameFa }}</strong>
            <em v-if="account.preferred">منتخب</em>
          </span>
          <bdi dir="ltr">{{ formatMaskedCardOverview(account.cardNumber, { usePersianDigits: true }) }}</bdi>
          <small dir="ltr">{{ formatMaskedIbanOverview(account.iban, { usePersianDigits: true }) }}</small>
        </span>
        <span class="check"><AppIcon name="check" :size="16" /></span>
      </label>
    </div>
    <p v-if="error" class="bank-picker__error" role="alert">{{ error }}</p>
  </fieldset>
</template>

<style scoped>
.bank-picker { min-width: 0; margin: 0; padding: 0; border: 0; }
legend { margin-bottom: var(--space-2); color: var(--color-text-secondary); font-size: var(--font-size-sm); font-weight: 500; }
.bank-picker__list { display: grid; gap: var(--space-2); }
.bank-option { position: relative; display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: var(--space-3); min-height: 5.4rem; padding: var(--space-3) var(--space-4); border: 1px solid var(--color-border); border-radius: var(--radius-lg); background: var(--color-surface-2); cursor: pointer; transition: border-color var(--transition-fast), background var(--transition-fast), box-shadow var(--transition-fast); }
.bank-option:hover { border-color: var(--color-border-hover); background: var(--color-surface-3); }
.bank-option.selected { border-color: var(--color-primary); background: var(--color-primary-soft); box-shadow: inset 0 0 0 1px rgba(67, 139, 255, .1); }
.bank-option input { position: absolute; width: 1px; height: 1px; opacity: 0; }
.bank-option:has(input:focus-visible) { outline: 2px solid var(--color-border-focus); outline-offset: 2px; box-shadow: var(--shadow-focus); }
.bank-copy { display: grid; min-width: 0; line-height: 1.45; }
.bank-copy > span { display: flex; align-items: center; gap: var(--space-2); }
.bank-copy strong { font-size: var(--font-size-sm); font-weight: 600; }
.bank-copy em { padding: .05rem .45rem; border-radius: var(--radius-pill); background: var(--color-primary-soft); color: var(--color-primary); font-size: .65rem; font-style: normal; }
.bank-copy bdi { margin-top: .15rem; color: var(--color-text-secondary); font-size: var(--font-size-sm); font-variant-numeric: tabular-nums; }
.bank-copy small { overflow: hidden; color: var(--color-text-muted); font-size: .68rem; text-overflow: ellipsis; white-space: nowrap; }
.check { display: grid; width: 1.5rem; height: 1.5rem; border: 1px solid var(--color-border-hover); border-radius: 50%; color: transparent; place-items: center; }
.selected .check { border-color: var(--action-primary); background: var(--action-primary); color: var(--on-primary); }
.bank-picker__error { margin: var(--space-2) 0 0; color: var(--color-danger); font-size: var(--font-size-xs); }
@media (max-width: 420px) { .bank-option { padding-inline: var(--space-3); } .bank-copy small { max-width: 14rem; } }
</style>
