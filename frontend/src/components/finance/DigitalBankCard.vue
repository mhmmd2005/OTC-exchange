<script setup lang="ts">
import { computed } from 'vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import { getBankIdentity } from '@/constants/banks'
import type { BankAccount } from '@/types'
import {
  formatMaskedCardOverview,
  formatMaskedIbanOverview,
  formatPersianDate,
  toPersianDigits,
} from '@/utils/formatters'
import BankLogo from './BankLogo.vue'

const props = defineProps<{
  account: BankAccount
  preferredLoading?: boolean
}>()

defineEmits<{
  preferred: [account: BankAccount]
  remove: [account: BankAccount]
}>()

const identity = computed(() => getBankIdentity(props.account.bank))
const visualStyle = computed(() => ({
  '--bank-accent': identity.value.primary,
  '--bank-accent-soft': identity.value.secondary,
}))
const maskedCard = computed(() => formatMaskedCardOverview(props.account.cardNumber, { usePersianDigits: true }))
const maskedIban = computed(() => formatMaskedIbanOverview(props.account.iban, { usePersianDigits: true }))
const lastCardDigits = computed(() => toPersianDigits(props.account.cardNumber.replace(/\D/g, '').slice(-4)))
</script>

<template>
  <AppCard as="article" padding="none" class="digital-bank-card" :style="visualStyle">
    <div class="card-face">
      <div class="card-face__glow" aria-hidden="true" />
      <header class="card-header">
        <div class="bank-identity">
          <BankLogo :bank="account.bank" size="lg" />
          <div>
            <h2>{{ account.bank.nameFa }}</h2>
            <bdi dir="ltr">{{ account.bank.nameEn }}</bdi>
          </div>
        </div>
        <div class="card-status">
          <StatusBadge domain="bank" :status="account.status" />
          <span v-if="account.preferred" class="preferred-badge"><AppIcon name="star" :size="13" />حساب پیش‌فرض</span>
        </div>
      </header>

      <div class="card-pan">
        <span>شماره کارت</span>
        <bdi
          class="card-number"
          dir="ltr"
          :aria-label="`شماره کارت با چهار رقم پایانی ${lastCardDigits}`"
        >{{ maskedCard }}</bdi>
      </div>

      <div class="card-details">
        <div class="account-owner">
          <span>صاحب حساب</span>
          <strong>{{ account.ownerName }}</strong>
        </div>
        <div class="account-iban">
          <span>شماره شبا</span>
          <bdi dir="ltr">{{ maskedIban }}</bdi>
        </div>
      </div>
    </div>

    <div v-if="account.rejectionReason" class="correction-note" role="note">
      <AppIcon name="warning" :size="18" />
      <span><strong>نیاز به اصلاح اطلاعات</strong>{{ account.rejectionReason }}</span>
    </div>

    <footer class="card-footer">
      <span class="registered-date"><AppIcon name="calendar" :size="16" />ثبت در {{ formatPersianDate(account.createdAt) }}</span>
      <div class="card-actions">
        <AppButton
          v-if="!account.preferred"
          variant="secondary"
          size="sm"
          icon="star"
          :disabled="account.status !== 'verified'"
          :loading="preferredLoading"
          @click="$emit('preferred', account)"
        >انتخاب برای برداشت</AppButton>
        <span v-else class="preferred-help"><AppIcon name="check" :size="15" />مقصد برداشت تومان</span>
        <AppButton
          variant="danger"
          size="sm"
          icon="trash"
          :disabled="account.preferred"
          @click="$emit('remove', account)"
        >حذف</AppButton>
      </div>
    </footer>
  </AppCard>
</template>

<style scoped>
.digital-bank-card {
  overflow: hidden;
  border-color: color-mix(in srgb, var(--bank-accent) 22%, var(--border-default));
  background: var(--surface-primary);
  box-shadow: var(--shadow-sm);
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast), transform var(--transition-fast);
}
.card-face {
  position: relative;
  display: flex;
  min-height: 17rem;
  flex-direction: column;
  justify-content: space-between;
  overflow: hidden;
  padding: var(--space-6);
  background:
    linear-gradient(128deg, color-mix(in srgb, var(--bank-accent) 15%, transparent), transparent 45%),
    radial-gradient(circle at 2% 110%, color-mix(in srgb, var(--bank-accent-soft) 16%, transparent), transparent 45%),
    linear-gradient(145deg, var(--surface-tertiary), var(--surface-primary) 68%);
}
.card-face::before {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(color-mix(in srgb, var(--bank-accent) 8%, transparent) 1px, transparent 1px),
    linear-gradient(90deg, color-mix(in srgb, var(--bank-accent) 8%, transparent) 1px, transparent 1px);
  background-size: 2.5rem 2.5rem;
  content: '';
  mask-image: linear-gradient(120deg, black, transparent 66%);
  opacity: .34;
  pointer-events: none;
}
.card-face__glow {
  position: absolute;
  width: 10rem;
  height: 10rem;
  inset-block-start: -6.5rem;
  inset-inline-start: -3rem;
  border-radius: 50%;
  background: var(--bank-accent);
  filter: blur(3.5rem);
  opacity: .12;
}
.card-header, .card-pan, .card-details { position: relative; z-index: 1; }
.card-header { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-4); }
.bank-identity { display: flex; min-width: 0; align-items: center; gap: var(--space-3); }
.bank-identity > div:last-child { display: grid; min-width: 0; gap: .1rem; }
.bank-identity h2 { margin: 0; font-size: var(--font-size-lg); font-weight: 700; }
.bank-identity bdi { color: var(--text-muted); font-size: .7rem; letter-spacing: .035em; }
.card-status { display: grid; flex: 0 0 auto; justify-items: end; gap: var(--space-2); }
.preferred-badge { display: inline-flex; align-items: center; gap: .3rem; color: var(--color-gold); font-size: .7rem; font-weight: 600; }
.card-pan { display: grid; gap: var(--space-1); margin-block: var(--space-7) var(--space-6); }
.card-pan > span, .card-details span { color: var(--text-muted); font-size: var(--font-size-xs); }
.card-number {
  min-width: 0;
  color: var(--text-primary);
  font-size: clamp(1.12rem, 1.9vw, 1.42rem);
  font-variant-numeric: tabular-nums;
  font-weight: 600;
  letter-spacing: .075em;
  line-height: 1.5;
  text-align: left;
  white-space: nowrap;
}
.card-details { display: grid; grid-template-columns: minmax(8rem, .85fr) minmax(0, 1.4fr); gap: var(--space-4); }
.account-owner, .account-iban { display: grid; min-width: 0; gap: .2rem; }
.account-owner strong { overflow-wrap: anywhere; font-size: var(--font-size-sm); font-weight: 600; }
.account-iban { text-align: end; }
.account-iban bdi { color: var(--text-secondary); font-size: var(--font-size-xs); font-variant-numeric: tabular-nums; overflow-wrap: anywhere; }
.correction-note { display: flex; align-items: flex-start; gap: var(--space-2); margin: var(--space-4) var(--space-5) 0; padding: var(--space-3); border-radius: var(--radius-md); background: var(--color-warning-soft); color: var(--color-warning); }
.correction-note span { display: grid; gap: .1rem; color: var(--text-secondary); font-size: var(--font-size-xs); }
.correction-note strong { color: var(--color-warning); }
.card-footer { display: flex; min-height: 4.75rem; align-items: center; justify-content: space-between; gap: var(--space-4); padding: var(--space-3) var(--space-5); border-top: 1px solid var(--border-subtle); background: color-mix(in srgb, var(--surface-secondary) 68%, transparent); }
.registered-date, .preferred-help { display: inline-flex; align-items: center; gap: var(--space-2); color: var(--text-muted); font-size: var(--font-size-xs); }
.preferred-help { color: var(--color-success); font-weight: 600; }
.card-actions { display: flex; align-items: center; justify-content: flex-end; gap: var(--space-2); }

@media (hover: hover) {
  .digital-bank-card:hover { border-color: color-mix(in srgb, var(--bank-accent) 45%, var(--border-default)); box-shadow: 0 18px 48px rgba(0,0,0,.23); transform: translateY(-2px); }
}

@media (max-width: 520px) {
  .card-face { min-height: 15.5rem; padding: var(--space-4); }
  .card-header { gap: var(--space-2); }
  .bank-identity { gap: var(--space-2); }
  .bank-identity :deep(.bank-logo--lg) { width: 3rem; height: 3rem; border-radius: .9rem; }
  .bank-identity h2 { font-size: var(--font-size-md); }
  .card-pan { margin-block: var(--space-6) var(--space-5); }
  .card-number { font-size: clamp(.98rem, 4.6vw, 1.2rem); letter-spacing: .045em; }
  .card-details { grid-template-columns: 1fr; gap: var(--space-3); }
  .account-iban { text-align: start; }
  .card-footer { align-items: stretch; flex-direction: column; gap: var(--space-3); padding: var(--space-4); }
  .card-actions { justify-content: stretch; }
  .card-actions :deep(.app-button) { min-height: 2.75rem; flex: 1; }
  .preferred-help { flex: 1; }
  .correction-note { margin-inline: var(--space-4); }
}

@media (max-width: 359px) {
  .card-header { display: grid; }
  .card-status { justify-items: start; }
  .card-status :deep(.status) { position: absolute; inset-block-start: 0; inset-inline-end: 0; }
  .card-status .preferred-badge { margin-top: var(--space-1); }
  .card-number { font-size: .95rem; letter-spacing: .025em; }
  .card-actions { flex-wrap: wrap; }
}
</style>
