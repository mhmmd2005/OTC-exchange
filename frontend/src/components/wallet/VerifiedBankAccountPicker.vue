<script setup lang="ts">
import {computed} from 'vue'
import type {BankAccount} from '@/types'

import {formatMaskedCardOverview, formatMaskedIbanOverview,} from '@/utils/formatters'

import BankLogo from '@/components/finance/BankLogo.vue'
import AppIcon from '@/components/ui/AppIcon.vue'

const props = defineProps<{
  accounts: BankAccount[]
  modelValue: string
  label?: string
  error?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  'manage-accounts': []
}>()

const availableAccounts = computed(() =>
    props.accounts.filter(
        (account) =>
            account.status === 'verified' &&
            !account.isTemporarilyDisabled &&
            account.isUsable !== false,
    ),
)

const selectedDisabled = computed(() =>
    props.accounts.some(
        (account) =>
            account.id === props.modelValue &&
            account.isTemporarilyDisabled,
    ),
)

function chooseAlternativeAccount() {
  const alternative =
      availableAccounts.value.find(
          (account) => account.preferred,
      ) ?? availableAccounts.value[0]

  if (alternative) {
    emit('update:modelValue', alternative.id)
    return
  }

  emit('manage-accounts')
}
</script>

<template>
  <fieldset class="bank-picker">
    <legend>
      {{ label || 'حساب بانکی تأییدشده' }}
    </legend>

    <div class="bank-picker__list">
      <div
          v-for="account in accounts"
          :key="account.id"
          class="bank-option-card"
          :class="{
          selected: modelValue === account.id,
          'temporarily-disabled':
            modelValue === account.id &&
            account.isTemporarilyDisabled,
        }"
      >
        <!-- اطلاعات و انتخاب کارت -->
        <label class="bank-option">
          <input
              type="radio"
              name="verified-bank-account"
              :value="account.id"
              :checked="modelValue === account.id"
              @change="$emit('update:modelValue', account.id)"
          >

          <BankLogo
              :bank="account.bank"
              size="md"
          />

          <span class="bank-copy">
            <span class="bank-copy__title">
              <strong>
                {{ account.bank.nameFa }}
              </strong>

              <em v-if="account.preferred">
                منتخب
              </em>
            </span>

            <bdi dir="ltr">
              {{
                formatMaskedCardOverview(
                    account.cardNumber,
                    {usePersianDigits: true},
                )
              }}
            </bdi>

            <small dir="ltr">
              {{
                formatMaskedIbanOverview(
                    account.iban,
                    {usePersianDigits: true},
                )
              }}
            </small>
          </span>

          <span
              class="check"
              aria-hidden="true"
          >
            <AppIcon
                name="check"
                :size="16"
            />
          </span>
        </label>

        <!-- هشدار داخل همان کارت انتخاب‌شده -->
        <div
            v-if="
            modelValue === account.id &&
            account.isTemporarilyDisabled
          "
            class="bank-disabled-panel"
            role="alert"
        >
          <div class="bank-disabled-panel__icon">
            <AppIcon
                name="shield"
                :size="23"
            />
          </div>

          <div class="bank-disabled-panel__content">
            <div class="bank-disabled-panel__heading">
              <strong>
                این کارت فعلاً امکان واریز ندارد
              </strong>

              <span class="bank-disabled-panel__badge">
                <span class="bank-disabled-panel__dot"></span>
                توقف موقت
              </span>
            </div>

            <p>
              این کارت موقتاً غیرفعال است.

              برای ادامه فرایند واریز، ابتدا کارت را فعال کنید یا یک کارت بانکی فعال دیگر انتخاب کنید.
            </p>

            <div class="bank-disabled-panel__footer">
              <span class="bank-disabled-panel__hint">
                <AppIcon
                    name="info"
                    :size="15"
                />

                پرداخت با این کارت مجاز نیست.
              </span>

              <button
                  type="button"
                  class="bank-disabled-panel__action"
                  @click="chooseAlternativeAccount"
              >
                {{
                  availableAccounts.length
                      ? 'انتخاب کارت فعال'
                      : 'مدیریت کارت‌ها'
                }}

                <AppIcon
                    name="arrow-left"
                    :size="16"
                />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- خطاهای عمومی انتخاب کارت -->
    <p
        v-if="error && !selectedDisabled"
        class="bank-picker__error"
        role="alert"
    >
      {{ error }}
    </p>
  </fieldset>
</template>

<style scoped>
.bank-picker {
  display: block;
  box-sizing: border-box;
  width: 100%;
  min-width: 0;
  margin: 0;
  padding: 0;

  border: none !important;
  outline: none !important;
  box-shadow: none !important;

  background: transparent;
}

.bank-picker legend {
  margin-bottom: var(--space-2);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 500;
}

.bank-picker__list {
  display: grid;
  gap: var(--space-3);
}

/* کادر یکپارچه کارت و هشدار */
.bank-option-card {
  min-width: 0;
  overflow: hidden;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface-2);

  transition: border-color var(--transition-fast),
  background var(--transition-fast),
  box-shadow var(--transition-fast);
}

.bank-option-card:not(.selected):hover {
  border-color: var(--color-border-hover);
  background: var(--color-surface-3);
}

.bank-option-card.selected {
  border-color: var(--color-primary);
  background: var(--color-primary-soft);
  box-shadow: inset 0 0 0 1px rgba(67, 139, 255, 0.1);
}


/* ردیف کارت بانکی */
.bank-option {
  position: relative;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: var(--space-3);

  min-height: 5.4rem;
  padding: var(--space-3) var(--space-4);

  cursor: pointer;
}

.bank-option input {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
}

.bank-option:has(input:focus-visible) {
  outline: 2px solid var(--color-border-focus);
  outline-offset: -3px;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-focus);
}

.bank-copy {
  display: grid;
  min-width: 0;
  line-height: 1.5;
}

.bank-copy__title {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.bank-copy strong {
  font-size: var(--font-size-sm);
  font-weight: 600;
}

.bank-copy em {
  padding: 0.05rem 0.45rem;
  border-radius: var(--radius-pill);
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-size: 0.65rem;
  font-style: normal;
}

.bank-copy bdi {
  margin-top: 0.15rem;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-variant-numeric: tabular-nums;
}

.bank-copy small {
  overflow: hidden;
  color: var(--color-text-muted);
  font-size: 0.68rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.check {
  display: grid;
  width: 1.5rem;
  height: 1.5rem;
  border: 1px solid var(--color-border-hover);
  border-radius: 50%;
  color: transparent;
  place-items: center;
  flex-shrink: 0;
}

.selected .check {
  border-color: var(--action-primary);
  background: var(--action-primary);
  color: var(--on-primary);
}

/* پنل هشدار، متصل به همان کارت */
.bank-disabled-panel {
  display: grid;
  grid-template-columns: 2.65rem minmax(0, 1fr);
  align-items: start;
  gap: 0.85rem;

  padding: 1rem;

  border-top: 1px solid rgba(255, 135, 146, 0.2);

  background: radial-gradient(
      circle at 100% 0%,
      rgba(240, 86, 105, 0.11),
      transparent 48%
  ),
  linear-gradient(
      135deg,
      rgba(240, 86, 105, 0.045),
      rgba(12, 24, 39, 0.2)
  );

  animation: bank-disabled-enter 220ms ease-out;
}

.bank-disabled-panel__icon {
  display: grid;
  width: 2.65rem;
  height: 2.65rem;
  place-items: center;

  border: 1px solid rgba(255, 113, 128, 0.2);
  border-radius: 0.85rem;

  background: rgba(240, 86, 105, 0.11);
  color: #ff929d;
}

.bank-disabled-panel__content {
  min-width: 0;
}

.bank-disabled-panel__heading {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.55rem;
}

.bank-disabled-panel__heading strong {
  color: #fff0f1;
  font-size: var(--font-size-sm);
  font-weight: 750;
  line-height: 1.8;
}

.bank-disabled-panel__badge {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;

  padding: 0.25rem 0.5rem;

  border: 1px solid rgba(255, 113, 128, 0.2);
  border-radius: var(--radius-pill);

  background: rgba(240, 86, 105, 0.1);
  color: #ff9ca5;

  font-size: 0.68rem;
  font-weight: 650;
  white-space: nowrap;
}

.bank-disabled-panel__dot {
  width: 6px;
  height: 6px;
  flex: 0 0 6px;
  border-radius: 50%;
  background: #ff8792;
  box-shadow: 0 0 9px rgba(255, 135, 146, 0.4);
}

.bank-disabled-panel__content > p {
  margin: 0.55rem 0 0.9rem;
  color: #aabbd0;
  font-size: var(--font-size-xs);
  line-height: 1.95;
}

.bank-disabled-panel__footer {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;

  padding-top: 0.75rem;
  border-top: 1px solid rgba(255, 255, 255, 0.065);
}

.bank-disabled-panel__hint {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  color: #8fa5bd;
  font-size: 0.69rem;
  line-height: 1.8;
}

.bank-disabled-panel__hint :deep(svg) {
  flex: 0 0 auto;
  color: #7ea9ff;
}

.bank-disabled-panel__action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;

  min-height: 2.4rem;
  padding: 0.5rem 0.75rem;

  border: 1px solid rgba(98, 153, 255, 0.35);
  border-radius: 0.75rem;

  background: rgba(57, 119, 219, 0.15);
  color: #a9c8ff;

  font-family: inherit;
  font-size: var(--font-size-xs);
  font-weight: 700;

  cursor: pointer;

  transition: background 180ms ease,
  border-color 180ms ease,
  transform 180ms ease;
}

.bank-disabled-panel__action:hover {
  border-color: rgba(115, 165, 255, 0.75);
  background: rgba(57, 119, 219, 0.28);
  transform: translateY(-1px);
}

.bank-disabled-panel__action:focus-visible {
  outline: 2px solid #80adff;
  outline-offset: 3px;
}

/* خطای عمومی انتخاب کارت */
.bank-picker__error {
  margin: var(--space-2) 0 0;
  color: var(--color-danger);
  font-size: var(--font-size-xs);
}

@keyframes bank-disabled-enter {
  from {
    opacity: 0;
    transform: translateY(4px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 480px) {
  .bank-option {
    padding-inline: var(--space-3);
  }

  .bank-copy small {
    max-width: 14rem;
  }

  .bank-disabled-panel {
    grid-template-columns: 2.25rem minmax(0, 1fr);
    gap: 0.65rem;
    padding: 0.8rem;
  }

  .bank-disabled-panel__icon {
    width: 2.25rem;
    height: 2.25rem;
    border-radius: 0.7rem;
  }

  .bank-disabled-panel__footer {
    align-items: stretch;
    flex-direction: column;
  }

  .bank-disabled-panel__action {
    width: 100%;
  }
}

@media (prefers-reduced-motion: reduce) {
  .bank-disabled-panel {
    animation: none;
  }

  .bank-disabled-panel__action {
    transition: none;
  }
}
</style>