<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import type { BankAccount, TomanDepositResult, VerificationSummary } from '@/types'
import { ApiError, isMockApiEnabled } from '@/services/api'
import { bankService } from '@/services/bank.service'
import { verificationService } from '@/services/verification.service'
import { walletService } from '@/services/wallet.service'
import { compareDecimal, subtractDecimal } from '@/utils/decimal'
import { formatCardNumber, formatPersianDateTime, formatToman } from '@/utils/formatters'
import { resolvePaymentRedirect } from '@/utils/paymentRedirect'
import AppAmountInput from '@/components/ui/AppAmountInput.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import AppModal from '@/components/ui/AppModal.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import VerifiedBankAccountPicker from '@/components/wallet/VerifiedBankAccountPicker.vue'

const amountPresets = ['1000000', '5000000', '10000000', '25000000', '50000000']
const approvedPaymentHosts = new Set(
  String(import.meta.env.VITE_PAYMENT_ALLOWED_HOSTS ?? '')
    .split(',')
    .map((host) => host.trim().toLowerCase())
    .filter(Boolean),
)
const router = useRouter()
const accounts = ref<BankAccount[]>([])
const verification = ref<VerificationSummary | null>(null)
const amount = ref('')
const bankAccountId = ref('')
const amountError = ref('')
const bankError = ref('')
const requestError = ref('')
const loading = ref(true)
const submitting = ref(false)
const reviewOpen = ref(false)
const result = ref<TomanDepositResult | null>(null)
const resultHeading = ref<HTMLElement | null>(null)

const verifiedAccounts = computed(() => accounts.value.filter((account) => account.status === 'verified'))
const selectedAccount = computed(() => verifiedAccounts.value.find((account) => account.id === bankAccountId.value))
const dailyRemaining = computed(() => {
  if (!verification.value) return ''
  const remaining = subtractDecimal(
    verification.value.limits.dailyTomanDeposit,
    verification.value.limits.usedTomanDeposit,
  )
  return compareDecimal(remaining, '0') > 0 ? remaining : '0'
})

function selectDefaultAccount() {
  if (bankAccountId.value && verifiedAccounts.value.some((account) => account.id === bankAccountId.value)) return
  bankAccountId.value = verifiedAccounts.value.find((account) => account.preferred)?.id
    || verifiedAccounts.value[0]?.id
    || ''
}

async function load() {
  loading.value = true
  requestError.value = ''
  try {
    const [bankAccounts, verificationSummary] = await Promise.all([
      bankService.listAccounts(),
      verificationService.getSummary(),
    ])
    accounts.value = bankAccounts
    verification.value = verificationSummary
    selectDefaultAccount()
  } catch (caught) {
    requestError.value = caught instanceof Error ? caught.message : 'اطلاعات واریز دریافت نشد.'
  } finally {
    loading.value = false
  }
}

function validate(): boolean {
  amountError.value = ''
  bankError.value = ''
  requestError.value = ''
  if (!amount.value || compareDecimal(amount.value, '0') <= 0) {
    amountError.value = 'مبلغ واریز را وارد کنید.'
  } else if (compareDecimal(amount.value, '100000') < 0) {
    amountError.value = 'حداقل مبلغ واریز ۱۰۰ هزار تومان است.'
  } else if (dailyRemaining.value && compareDecimal(amount.value, dailyRemaining.value) > 0) {
    amountError.value = 'مبلغ واردشده بیشتر از سقف باقی‌مانده امروز است.'
  }
  if (!selectedAccount.value) bankError.value = 'یک کارت بانکی تأییدشده انتخاب کنید.'
  return !amountError.value && !bankError.value
}

function openReview() {
  if (validate()) reviewOpen.value = true
}

async function createDeposit() {
  if (!validate()) {
    reviewOpen.value = false
    return
  }
  submitting.value = true
  requestError.value = ''
  try {
    result.value = await walletService.createTomanDeposit({
      amount: amount.value,
      bankAccountId: bankAccountId.value,
    })
    reviewOpen.value = false
  } catch (caught) {
    if (caught instanceof ApiError) {
      amountError.value = caught.details?.fields?.amount || ''
      bankError.value = caught.details?.fields?.bankAccountId || ''
    }
    requestError.value = caught instanceof Error ? caught.message : 'ساخت پرداخت انجام نشد.'
    reviewOpen.value = false
  } finally {
    submitting.value = false
  }
}

function resetForm() {
  amount.value = ''
  result.value = null
  requestError.value = ''
  selectDefaultAccount()
}

async function goToPayment() {
  if (!result.value || typeof window === 'undefined') return
  requestError.value = ''
  const decision = resolvePaymentRedirect(
    result.value.paymentUrl,
    window.location.origin,
    isMockApiEnabled,
    approvedPaymentHosts,
  )
  if (decision.kind === 'internal-mock') {
    await router.push(decision.target)
    return
  }
  if (decision.kind === 'blocked') {
    requestError.value = decision.reason === 'invalid'
      ? 'نشانی درگاه معتبر نیست. پرداخت تازه‌ای بسازید یا با پشتیبانی تماس بگیرید.'
      : decision.reason === 'mock-disabled'
        ? 'درگاه آزمایشی در نسخه انتشار قابل استفاده نیست.'
        : 'نشانی درگاه مورد تأیید نیست. برای امنیت حساب، به این مقصد هدایت نشدید.'
    return
  }
  window.location.assign(decision.href)
}

watch(amount, () => { amountError.value = ''; requestError.value = '' })
watch(bankAccountId, () => { bankError.value = ''; requestError.value = '' })
watch(result, async (value) => {
  if (!value) return
  await nextTick()
  resultHeading.value?.focus({ preventScroll: true })
}, { flush: 'post' })
onMounted(load)
</script>

<template>
  <div class="page page--mobile-cta money-flow-page">
    <PageHeader title="واریز تومان" description="افزایش موجودی کیف پول از کارت بانکی تأییدشده" back-to="/app/wallet" />

    <div v-if="loading" class="flow-layout">
      <AppSkeleton height="33rem" radius="var(--radius-xl)" />
      <AppSkeleton height="19rem" radius="var(--radius-xl)" />
    </div>

    <AppCard v-else-if="requestError && !accounts.length" class="load-state">
      <EmptyState icon="warning" title="اطلاعات واریز آماده نشد" :description="requestError">
        <AppButton @click="load">تلاش دوباره</AppButton>
      </EmptyState>
    </AppCard>

    <AppCard v-else-if="!verifiedAccounts.length" class="load-state">
      <EmptyState icon="bank" title="کارت تأییدشده‌ای ندارید" description="برای واریز تومان ابتدا یک کارت بانکی به نام خودتان ثبت و تأیید کنید.">
        <AppButton to="/app/bank-accounts">افزودن حساب بانکی</AppButton>
      </EmptyState>
    </AppCard>

    <div v-else-if="result" class="result-wrap">
      <AppCard class="result-card" padding="lg">
        <span class="result-icon"><AppIcon name="check" :size="31" /></span>
        <span class="eyebrow">درگاه پرداخت آماده است</span>
        <h2 ref="resultHeading" tabindex="-1"><span class="sr-only">درگاه پرداخت آماده است، مبلغ </span>{{ formatToman(result.amount) }}</h2>
        <p>برای تکمیل واریز، وارد درگاه بانکی شوید. مبلغ پس از بازگشت موفق به کیف پول شما اضافه می‌شود.</p>
        <dl>
          <div><dt>شناسه پرداخت</dt><dd dir="ltr">{{ result.id }}</dd></div>
          <div><dt>مهلت پرداخت</dt><dd>{{ formatPersianDateTime(result.expiresAt) }}</dd></div>
          <div v-if="selectedAccount"><dt>کارت پرداخت</dt><dd>{{ selectedAccount.bank.nameFa }}</dd></div>
        </dl>
        <div v-if="requestError" class="form-error result-error" role="alert"><AppIcon name="warning" :size="18" /><span>{{ requestError }}</span></div>
        <div class="result-actions">
          <AppButton block size="lg" icon="bank" @click="goToPayment">ورود به درگاه پرداخت</AppButton>
          <AppButton block variant="secondary" @click="resetForm">تغییر مبلغ</AppButton>
        </div>
        <div class="payment-warning"><AppIcon name="warning" :size="18" /> فقط با کارت انتخاب‌شده و متعلق به صاحب حساب پرداخت کنید.</div>
      </AppCard>
    </div>

    <div v-else class="flow-layout">
      <AppCard class="flow-card" padding="lg">
        <div class="flow-intro"><span><AppIcon name="download" :size="24" /></span><div><h2>مبلغ و کارت پرداخت</h2><p>پرداخت در درگاه امن بانکی تکمیل می‌شود.</p></div></div>

        <form class="deposit-form" @submit.prevent="openReview">
          <AppAmountInput v-model="amount" label="مبلغ واریز" suffix="تومان" :error="amountError" />
          <div class="preset-list" aria-label="مبالغ پیشنهادی">
            <button v-for="preset in amountPresets" :key="preset" type="button" :class="{ active: amount === preset }" @click="amount = preset">{{ formatToman(preset) }}</button>
          </div>
          <VerifiedBankAccountPicker v-model="bankAccountId" :accounts="verifiedAccounts" label="کارت مبدأ" :error="bankError" />
          <div v-if="requestError" class="form-error" role="alert"><AppIcon name="warning" :size="18" /><span>{{ requestError }}</span></div>
          <div class="mobile-cta"><AppButton block size="lg" type="submit">ادامه و پرداخت</AppButton></div>
        </form>
      </AppCard>

      <aside class="flow-aside">
        <AppCard>
          <div class="aside-title"><span><AppIcon name="info" :size="20" /></span><div><h3>سقف واریز امروز</h3><p>بر اساس سطح حساب شما</p></div></div>
          <dl class="limits">
            <div><dt>حداقل واریز</dt><dd>{{ formatToman('100000') }}</dd></div>
            <div v-if="verification"><dt>سقف روزانه</dt><dd>{{ formatToman(verification.limits.dailyTomanDeposit) }}</dd></div>
            <div v-if="dailyRemaining"><dt>باقی‌مانده امروز</dt><dd class="success">{{ formatToman(dailyRemaining) }}</dd></div>
          </dl>
        </AppCard>
        <div class="trust-note"><AppIcon name="shield" :size="20" /><span><strong>پرداخت به نام خودتان</strong><small>واریز از کارت اشخاص دیگر پذیرفته نمی‌شود.</small></span></div>
      </aside>
    </div>

    <AppModal v-model="reviewOpen" title="تأیید و ساخت پرداخت" description="پیش از ورود به درگاه، اطلاعات را بررسی کنید." size="sm" :dismissible="!submitting">
      <div class="review">
        <div class="review-amount"><span>مبلغ پرداخت</span><strong>{{ formatToman(amount) }}</strong></div>
        <dl>
          <div v-if="selectedAccount"><dt>کارت مبدأ</dt><dd>{{ selectedAccount.bank.nameFa }} · <bdi dir="ltr">{{ formatCardNumber(selectedAccount.cardNumber, { masked: true, usePersianDigits: true }) }}</bdi></dd></div>
          <div><dt>کارمزد واریز</dt><dd class="success">رایگان</dd></div>
          <div><dt>افزایش موجودی</dt><dd>{{ formatToman(amount) }}</dd></div>
        </dl>
        <div class="review-note"><AppIcon name="info" :size="17" /> تا ۱۰ دقیقه برای تکمیل پرداخت فرصت دارید.</div>
      </div>
      <template #footer>
        <AppButton block :loading="submitting" @click="createDeposit">تأیید و ساخت درگاه</AppButton>
        <AppButton block variant="secondary" :disabled="submitting" @click="reviewOpen = false">بازگشت</AppButton>
      </template>
    </AppModal>
  </div>
</template>

<style scoped>
.money-flow-page { max-width: 72rem; }
.flow-layout { display: grid; grid-template-columns: minmax(28rem, 1.12fr) minmax(19rem, .68fr); align-items: start; gap: var(--space-5); }
.flow-card { overflow: hidden; }
.flow-intro, .aside-title { display: flex; align-items: center; gap: var(--space-3); }
.flow-intro > span, .aside-title > span { display: grid; width: 3rem; height: 3rem; flex: 0 0 auto; border-radius: .9rem; background: var(--color-primary-soft); color: var(--color-primary); place-items: center; }
.flow-intro h2, .aside-title h3 { margin: 0; font-size: var(--font-size-lg); }
.flow-intro p, .aside-title p { margin: .1rem 0 0; color: var(--color-text-muted); font-size: var(--font-size-xs); }
.deposit-form { display: grid; gap: var(--space-5); margin-top: var(--space-7); }
.preset-list { display: flex; flex-wrap: wrap; gap: var(--space-2); margin-top: calc(var(--space-3) * -1); }
.preset-list button { min-height: 2.35rem; padding-inline: var(--space-3); border: 1px solid var(--color-border); border-radius: var(--radius-pill); background: var(--color-surface-2); color: var(--color-text-secondary); font-size: var(--font-size-xs); white-space: nowrap; }
.preset-list button:hover, .preset-list button.active { border-color: var(--color-primary); background: var(--color-primary-soft); color: var(--color-primary); }
.flow-aside { display: grid; gap: var(--space-4); }
.aside-title > span { width: 2.7rem; height: 2.7rem; background: var(--color-info-soft); color: var(--color-info); }
.aside-title h3 { font-size: var(--font-size-md); }
.limits { display: grid; gap: var(--space-3); margin: var(--space-5) 0 0; }
.limits div { display: flex; justify-content: space-between; gap: var(--space-3); padding-bottom: var(--space-3); border-block-end: 1px solid var(--color-border-soft); }
.limits div:last-child { padding-bottom: 0; border: 0; }
.limits dt { color: var(--color-text-muted); font-size: var(--font-size-sm); }
.limits dd { margin: 0; font-size: var(--font-size-sm); font-weight: 600; }
.limits .success, .success { color: var(--color-success); }
.trust-note { display: flex; gap: var(--space-3); padding: var(--space-4); border: 1px solid rgba(53,201,149,.15); border-radius: var(--radius-lg); background: var(--color-success-soft); color: var(--color-success); }
.trust-note > span { display: grid; }
.trust-note strong { color: var(--color-text-primary); font-size: var(--font-size-sm); }
.trust-note small { color: var(--color-text-muted); font-size: var(--font-size-xs); }
.form-error { display: flex; align-items: center; gap: var(--space-2); padding: var(--space-3); border: 1px solid rgba(240,108,117,.2); border-radius: var(--radius-md); background: var(--color-danger-soft); color: var(--color-danger); font-size: var(--font-size-sm); }
.review { display: grid; gap: var(--space-5); }
.review-amount { display: grid; justify-items: center; padding: var(--space-5); border-radius: var(--radius-lg); background: var(--color-primary-soft); }
.review-amount span { color: var(--color-text-muted); font-size: var(--font-size-xs); }
.review-amount strong { margin-top: .2rem; font-size: var(--font-size-2xl); }
.review dl, .result-card dl { display: grid; gap: var(--space-3); margin: 0; }
.review dl div, .result-card dl div { display: flex; justify-content: space-between; gap: var(--space-4); padding-bottom: var(--space-3); border-block-end: 1px solid var(--color-border-soft); }
.review dt, .result-card dt { color: var(--color-text-muted); }
.review dd, .result-card dd { margin: 0; font-weight: 600; text-align: end; }
.review-note, .payment-warning { display: flex; align-items: center; gap: var(--space-2); padding: var(--space-3); border-radius: var(--radius-md); background: var(--color-info-soft); color: var(--color-info); font-size: var(--font-size-xs); }
.result-wrap { width: min(100%, 37rem); margin-inline: auto; }
.result-card { display: grid; justify-items: stretch; text-align: center; }
.result-icon { display: grid; width: 4.5rem; height: 4.5rem; margin-inline: auto; border-radius: 1.35rem; background: var(--color-success-soft); color: var(--color-success); place-items: center; }
.result-card .eyebrow { margin-top: var(--space-4); color: var(--color-success); font-size: var(--font-size-sm); font-weight: 600; }
.result-card h2 { margin: var(--space-1) 0; font-size: var(--font-size-2xl); }
.result-card > p { max-width: 30rem; margin: 0 auto var(--space-6); color: var(--color-text-muted); }
.result-card dl { text-align: start; }
.result-actions { display: grid; gap: var(--space-2); margin-top: var(--space-6); }
.result-error { width: 100%; margin-top: var(--space-4); text-align: start; }
.payment-warning { margin-top: var(--space-4); background: var(--color-warning-soft); color: var(--color-warning); text-align: start; }
.load-state { width: min(100%, 42rem); margin-inline: auto; }
@media (max-width: 900px) { .flow-layout { grid-template-columns: 1fr; } .flow-aside { grid-template-columns: 1fr 1fr; } }
@media (max-width: 767px) {
  .flow-aside { grid-template-columns: 1fr; }
  .deposit-form { gap: var(--space-4); }
}
@media (max-width: 420px) { .preset-list { display: grid; grid-template-columns: repeat(2, 1fr); } .preset-list button:last-child { grid-column: 1 / -1; } }
</style>
