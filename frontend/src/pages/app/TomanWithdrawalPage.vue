<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { BankAccount, Transaction, VerificationSummary, WithdrawalEstimate } from '@/types'
import { ApiError } from '@/services/api'
import { bankService } from '@/services/bank.service'
import { verificationService } from '@/services/verification.service'
import { walletService } from '@/services/wallet.service'
import { useWalletStore } from '@/stores/wallet'
import { compareDecimal, divideDecimal, multiplyDecimal, subtractDecimal } from '@/utils/decimal'
import { formatCardNumber, formatPersianDateTime, formatToman, toPersianDigits } from '@/utils/formatters'
import AppAmountInput from '@/components/ui/AppAmountInput.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import AppModal from '@/components/ui/AppModal.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import VerifiedBankAccountPicker from '@/components/wallet/VerifiedBankAccountPicker.vue'

const walletStore = useWalletStore()
const accounts = ref<BankAccount[]>([])
const verification = ref<VerificationSummary | null>(null)
const amount = ref('')
const bankAccountId = ref('')
const amountError = ref('')
const bankError = ref('')
const requestError = ref('')
const estimate = ref<WithdrawalEstimate | null>(null)
const idempotencyKey = ref('')
const result = ref<Transaction | null>(null)
const loading = ref(true)
const estimating = ref(false)
const submitting = ref(false)
const reviewOpen = ref(false)
const nowMs = ref(Date.now())
const resultHeading = ref<HTMLElement | null>(null)
const reviewSubmitButton = ref<InstanceType<typeof AppButton> | null>(null)
const reviewBackButton = ref<InstanceType<typeof AppButton> | null>(null)
let estimateSequence = 0
let clockTimer: number | undefined

const verifiedAccounts = computed(() => accounts.value.filter((account) => account.status === 'verified'))
const selectedAccount = computed(() => verifiedAccounts.value.find((account) => account.id === bankAccountId.value))
const estimatedAccount = computed(() => verifiedAccounts.value.find((account) => account.id === estimate.value?.bankAccountId))
const estimateExpired = computed(() => !estimate.value || Date.parse(estimate.value.expiresAt) <= nowMs.value)
const estimateSecondsRemaining = computed(() => estimate.value
  ? Math.max(0, Math.ceil((Date.parse(estimate.value.expiresAt) - nowMs.value) / 1_000))
  : 0)
const availableBalance = computed(() => walletStore.summary?.availableToman || '0')
const dailyRemaining = computed(() => {
  if (!verification.value) return ''
  const remaining = subtractDecimal(
    verification.value.limits.dailyTomanWithdrawal,
    verification.value.limits.usedTomanWithdrawal,
  )
  return compareDecimal(remaining, '0') > 0 ? remaining : '0'
})
const maximumAmount = computed(() => {
  if (!dailyRemaining.value) return availableBalance.value
  return compareDecimal(availableBalance.value, dailyRemaining.value) <= 0
    ? availableBalance.value
    : dailyRemaining.value
})
const availablePercent = computed(() => {
  const total = walletStore.summary?.tomanBalance || '0'
  if (compareDecimal(total, '0') <= 0) return 0
  const ratio = divideDecimal(multiplyDecimal(availableBalance.value, '100'), total, 2, 'down')
  return Math.max(0, Math.min(100, Number(ratio)))
})

function createIdempotencyKey(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') return crypto.randomUUID()
  return `withdrawal_${Date.now().toString(36)}_${Math.random().toString(36).slice(2)}`
}

function invalidateEstimate() {
  estimateSequence += 1
  estimating.value = false
  estimate.value = null
  idempotencyKey.value = ''
  if (reviewOpen.value && !submitting.value) reviewOpen.value = false
}

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
      walletStore.fetchWallet(),
    ])
    accounts.value = bankAccounts
    verification.value = verificationSummary
    selectDefaultAccount()
  } catch (caught) {
    requestError.value = caught instanceof Error ? caught.message : 'اطلاعات برداشت دریافت نشد.'
  } finally {
    loading.value = false
  }
}

function validateAmount(): boolean {
  amountError.value = ''
  if (!amount.value || compareDecimal(amount.value, '0') <= 0) {
    amountError.value = 'مبلغ برداشت را وارد کنید.'
  } else if (compareDecimal(amount.value, '50000') < 0) {
    amountError.value = 'حداقل مبلغ برداشت ۵۰ هزار تومان است.'
  } else if (compareDecimal(amount.value, availableBalance.value) > 0) {
    amountError.value = 'موجودی قابل برداشت تومان کافی نیست.'
  } else if (dailyRemaining.value && compareDecimal(amount.value, dailyRemaining.value) > 0) {
    amountError.value = 'مبلغ واردشده بیشتر از سقف باقی‌مانده امروز است.'
  }
  return !amountError.value
}

function validate(): boolean {
  bankError.value = ''
  requestError.value = ''
  const validAmount = validateAmount()
  if (!selectedAccount.value) bankError.value = 'یک حساب بانکی تأییدشده انتخاب کنید.'
  return validAmount && !bankError.value
}

async function requestEstimate(showErrors = true): Promise<WithdrawalEstimate | null> {
  const requestId = ++estimateSequence
  estimate.value = null
  idempotencyKey.value = ''
  if (!amount.value || compareDecimal(amount.value, '50000') < 0) {
    if (showErrors) validateAmount()
    return null
  }
  if (!validateAmount()) return null
  if (!selectedAccount.value) {
    if (showErrors) bankError.value = 'یک حساب بانکی تأییدشده انتخاب کنید.'
    return null
  }
  estimating.value = true
  try {
    const response = await walletService.estimateTomanWithdrawal({
      amount: amount.value,
      bankAccountId: selectedAccount.value.id,
    })
    if (requestId !== estimateSequence) return null
    estimate.value = response
    idempotencyKey.value = createIdempotencyKey()
    nowMs.value = Date.now()
    return response
  } catch (caught) {
    if (requestId === estimateSequence && showErrors) {
      amountError.value = caught instanceof Error ? caught.message : 'محاسبه مبلغ تسویه انجام نشد.'
    }
    return null
  } finally {
    if (requestId === estimateSequence) estimating.value = false
  }
}

async function openReview() {
  if (!validate()) return
  const response = estimate.value?.amount === amount.value
    && estimate.value.bankAccountId === bankAccountId.value
    && !estimateExpired.value
    ? estimate.value
    : await requestEstimate()
  if (response) reviewOpen.value = true
}

async function createWithdrawal() {
  if (submitting.value) return
  if (!estimate.value || !idempotencyKey.value) {
    reviewOpen.value = false
    return
  }
  if (estimateExpired.value) {
    reviewOpen.value = false
    invalidateEstimate()
    requestError.value = 'مهلت برآورد برداشت تمام شده است؛ دوباره ادامه دهید.'
    return
  }
  submitting.value = true
  requestError.value = ''
  try {
    result.value = await walletService.createTomanWithdrawal({
      estimateToken: estimate.value.estimateToken,
      estimateVersion: estimate.value.estimateVersion,
      idempotencyKey: idempotencyKey.value,
    })
    reviewOpen.value = false
    await walletStore.refresh()
  } catch (caught) {
    if (caught instanceof ApiError) {
      amountError.value = caught.details?.fields?.amount || ''
      bankError.value = caught.details?.fields?.bankAccountId || ''
      if (caught.code === 'QUOTE_EXPIRED') invalidateEstimate()
    }
    requestError.value = caught instanceof Error ? caught.message : 'ثبت درخواست برداشت انجام نشد.'
    reviewOpen.value = false
  } finally {
    submitting.value = false
  }
}

function useMaximum() {
  amount.value = maximumAmount.value
}

watch(amount, () => {
  invalidateEstimate()
  amountError.value = ''
  requestError.value = ''
})
watch(bankAccountId, () => {
  invalidateEstimate()
  bankError.value = ''
  requestError.value = ''
})
watch(result, async (value) => {
  if (!value) return
  await nextTick()
  resultHeading.value?.focus({ preventScroll: true })
}, { flush: 'post' })
watch(estimateExpired, async (expired, wasExpired) => {
  if (!expired || wasExpired || !reviewOpen.value) return
  const submitElement = reviewSubmitButton.value?.$el as HTMLElement | undefined
  const submitHadFocus = document.activeElement === submitElement
  await nextTick()
  if (submitHadFocus) {
    const backElement = reviewBackButton.value?.$el as HTMLElement | undefined
    backElement?.focus({ preventScroll: true })
  }
})
onMounted(() => {
  clockTimer = window.setInterval(() => { nowMs.value = Date.now() }, 1_000)
  void load()
})
onBeforeUnmount(() => {
  estimateSequence += 1
  if (clockTimer !== undefined) window.clearInterval(clockTimer)
})
</script>

<template>
  <div class="page page--mobile-cta withdrawal-page">
    <PageHeader title="برداشت تومان" description="تسویه موجودی به حساب بانکی تأییدشده شما" back-to="/app/wallet" />

    <div v-if="loading" class="withdraw-layout">
      <AppSkeleton height="35rem" radius="var(--radius-xl)" />
      <AppSkeleton height="20rem" radius="var(--radius-xl)" />
    </div>

    <AppCard v-else-if="requestError && !accounts.length" class="state-card">
      <EmptyState icon="warning" title="اطلاعات برداشت آماده نشد" :description="requestError"><AppButton @click="load">تلاش دوباره</AppButton></EmptyState>
    </AppCard>

    <AppCard v-else-if="!verifiedAccounts.length" class="state-card">
      <EmptyState icon="bank" title="حساب بانکی تأییدشده لازم است" description="برای برداشت تومان ابتدا یک حساب بانکی تأییدشده اضافه کنید.">
        <AppButton to="/app/bank-accounts">افزودن حساب بانکی</AppButton>
      </EmptyState>
    </AppCard>

    <div v-else-if="result" class="success-wrap">
      <AppCard class="success-card" padding="lg">
        <span class="success-icon"><AppIcon name="check" :size="31" /></span>
        <span class="eyebrow">درخواست برداشت ثبت شد</span>
        <h2 ref="resultHeading" tabindex="-1"><span class="sr-only">درخواست برداشت ثبت شد، مبلغ </span>{{ formatToman(result.amount) }}</h2>
        <p>درخواست شما در صف تسویه بانکی قرار گرفت. تغییر وضعیت از بخش تراکنش‌ها قابل پیگیری است.</p>
        <StatusBadge domain="transaction" :status="result.status" />
        <dl>
          <div><dt>شماره پیگیری</dt><dd dir="ltr">{{ result.referenceNumber }}</dd></div>
          <div><dt>مبلغ دریافتی</dt><dd>{{ formatToman(result.tomanAmount || result.amount) }}</dd></div>
          <div><dt>کارمزد</dt><dd>{{ formatToman(result.fee || '0') }}</dd></div>
          <div><dt>زمان ثبت</dt><dd>{{ formatPersianDateTime(result.createdAt) }}</dd></div>
        </dl>
        <div class="success-actions"><AppButton block to="/app/transactions">پیگیری تراکنش</AppButton><AppButton block variant="secondary" to="/app/wallet">بازگشت به کیف پول</AppButton></div>
      </AppCard>
    </div>

    <div v-else class="withdraw-layout">
      <AppCard class="withdraw-card" padding="lg">
        <div class="form-heading"><span><AppIcon name="upload" :size="24" /></span><div><h2>مبلغ و مقصد تسویه</h2><p>حساب مقصد باید به نام صاحب حساب روشا باشد.</p></div></div>
        <form class="withdraw-form" @submit.prevent="openReview">
          <div>
            <AppAmountInput
              v-model="amount"
              label="مبلغ برداشت"
              suffix="تومان"
              :balance="availableBalance"
              balance-label="قابل برداشت"
              :error="amountError"
              @blur="requestEstimate(false)"
            />
            <button type="button" class="max-button" @click="useMaximum">برداشت حداکثر مبلغ مجاز</button>
          </div>
          <VerifiedBankAccountPicker v-model="bankAccountId" :accounts="verifiedAccounts" label="حساب مقصد" :error="bankError" />

          <div class="settlement-preview" :class="{ loading: estimating }">
            <div><span>کارمزد بانکی</span><strong>{{ estimate ? formatToman(estimate.fee) : 'پس از ورود مبلغ' }}</strong></div>
            <div><span>مبلغ واریزی به حساب</span><strong>{{ estimate ? formatToman(estimate.receivable) : '—' }}</strong></div>
            <div><span>زمان تقریبی تسویه</span><strong>{{ estimate?.estimatedSettlement || 'چرخه پایا' }}</strong></div>
          </div>
          <div v-if="requestError" class="form-error" role="alert"><AppIcon name="warning" :size="18" /><span>{{ requestError }}</span></div>
          <div class="mobile-cta"><AppButton block size="lg" type="submit" :loading="estimating">ثبت درخواست برداشت</AppButton></div>
        </form>
      </AppCard>

      <aside class="withdraw-aside">
        <AppCard class="available-card">
          <span class="available-label">موجودی قابل برداشت</span>
          <strong>{{ formatToman(availableBalance) }}</strong>
          <span class="locked" v-if="walletStore.summary">{{ formatToman(walletStore.summary.lockedToman) }} مسدود</span>
          <div class="balance-bar"><i :style="{ width: `${availablePercent}%` }" /></div>
        </AppCard>
        <AppCard>
          <div class="aside-heading"><AppIcon name="clock" :size="20" /><h3>زمان‌بندی تسویه</h3></div>
          <p class="aside-copy">درخواست‌های تأییدشده در چرخه‌های پایا پردازش می‌شوند. تعطیلات رسمی ممکن است زمان واریز را جابه‌جا کند.</p>
          <dl class="limits">
            <div><dt>حداقل برداشت</dt><dd>{{ formatToman('50000') }}</dd></div>
            <div v-if="dailyRemaining"><dt>سقف باقی‌مانده امروز</dt><dd>{{ formatToman(dailyRemaining) }}</dd></div>
          </dl>
        </AppCard>
      </aside>
    </div>

    <AppModal v-model="reviewOpen" title="بررسی برداشت تومان" description="پس از ثبت، درخواست وارد صف تسویه می‌شود." size="sm" :dismissible="!submitting">
      <div v-if="estimate" class="review">
        <div class="review-total"><span>مبلغ واریزی به حساب</span><strong>{{ formatToman(estimate.receivable) }}</strong></div>
        <dl>
          <div><dt>مبلغ برداشت</dt><dd>{{ formatToman(estimate.amount) }}</dd></div>
          <div><dt>کارمزد</dt><dd>{{ formatToman(estimate.fee) }}</dd></div>
          <div v-if="estimatedAccount"><dt>حساب مقصد</dt><dd>{{ estimatedAccount.bank.nameFa }} · <bdi dir="ltr">{{ formatCardNumber(estimatedAccount.cardNumber, { masked: true, usePersianDigits: true }) }}</bdi></dd></div>
          <div><dt>زمان تسویه</dt><dd>{{ estimate.estimatedSettlement }}</dd></div>
          <div><dt>اعتبار برآورد</dt><dd>{{ toPersianDigits(estimateSecondsRemaining) }} ثانیه</dd></div>
        </dl>
        <div v-if="estimateExpired" class="review-note expired" role="status" aria-atomic="true"><AppIcon name="warning" :size="17" /> اعتبار برآورد تمام شده است؛ دوباره ادامه دهید.</div>
        <div v-else class="review-note"><AppIcon name="info" :size="17" /> اطلاعات حساب مقصد و مبلغ را یک‌بار دیگر بررسی کنید.</div>
      </div>
      <template #footer>
        <AppButton ref="reviewSubmitButton" block :loading="submitting" :disabled="estimateExpired" @click="createWithdrawal">تأیید و ثبت درخواست</AppButton>
        <AppButton ref="reviewBackButton" block variant="secondary" :disabled="submitting" @click="reviewOpen = false">بازگشت</AppButton>
      </template>
    </AppModal>
  </div>
</template>

<style scoped>
.withdrawal-page { max-width: 72rem; }
.withdraw-layout { display: grid; grid-template-columns: minmax(28rem, 1.12fr) minmax(19rem, .68fr); align-items: start; gap: var(--space-5); }
.form-heading { display: flex; align-items: center; gap: var(--space-3); }
.form-heading > span { display: grid; width: 3rem; height: 3rem; border-radius: .9rem; background: var(--color-gold-soft); color: var(--color-gold); place-items: center; }
.form-heading h2 { margin: 0; font-size: var(--font-size-lg); }
.form-heading p { margin: .1rem 0 0; color: var(--color-text-muted); font-size: var(--font-size-xs); }
.withdraw-form { display: grid; gap: var(--space-5); margin-top: var(--space-7); }
.max-button { margin-top: var(--space-2); padding: 0; border: 0; background: transparent; color: var(--color-primary); font-size: var(--font-size-xs); font-weight: 600; }
.settlement-preview { display: grid; gap: var(--space-3); padding: var(--space-4); border: 1px solid var(--color-border-soft); border-radius: var(--radius-lg); background: var(--color-surface-2); transition: opacity var(--transition-fast); }
.settlement-preview.loading { opacity: .55; }
.settlement-preview div { display: flex; justify-content: space-between; gap: var(--space-4); }
.settlement-preview span { color: var(--color-text-muted); font-size: var(--font-size-sm); }
.settlement-preview strong { font-size: var(--font-size-sm); text-align: end; }
.settlement-preview div:nth-child(2) { padding-block: var(--space-3); border-block: 1px solid var(--color-border-soft); }
.settlement-preview div:nth-child(2) strong { color: var(--color-success); }
.withdraw-aside { display: grid; gap: var(--space-4); }
.available-card { overflow: hidden; background: linear-gradient(145deg, var(--color-surface-1), rgba(221,183,110,.08)); }
.available-label { color: var(--color-text-muted); font-size: var(--font-size-xs); }
.available-card > strong { display: block; margin-top: var(--space-2); font-size: var(--font-size-xl); }
.locked { display: block; margin-top: .15rem; color: var(--color-text-muted); font-size: var(--font-size-xs); }
.balance-bar { height: .3rem; margin-top: var(--space-5); overflow: hidden; border-radius: var(--radius-pill); background: var(--color-surface-3); }
.balance-bar i { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg, var(--color-gold), var(--color-primary)); }
.aside-heading { display: flex; align-items: center; gap: var(--space-2); color: var(--color-info); }
.aside-heading h3 { margin: 0; color: var(--color-text-primary); font-size: var(--font-size-md); }
.aside-copy { margin: var(--space-3) 0 0; color: var(--color-text-muted); font-size: var(--font-size-sm); }
.limits { display: grid; gap: var(--space-3); margin: var(--space-5) 0 0; }
.limits div { display: flex; justify-content: space-between; gap: var(--space-3); padding-top: var(--space-3); border-block-start: 1px solid var(--color-border-soft); }
.limits dt { color: var(--color-text-muted); font-size: var(--font-size-xs); }
.limits dd { margin: 0; font-size: var(--font-size-xs); font-weight: 600; }
.form-error { display: flex; align-items: center; gap: var(--space-2); padding: var(--space-3); border: 1px solid rgba(240,108,117,.2); border-radius: var(--radius-md); background: var(--color-danger-soft); color: var(--color-danger); }
.review { display: grid; gap: var(--space-5); }
.review-total { display: grid; justify-items: center; padding: var(--space-5); border-radius: var(--radius-lg); background: var(--color-success-soft); }
.review-total span { color: var(--color-text-muted); font-size: var(--font-size-xs); }
.review-total strong { margin-top: .2rem; color: var(--color-success); font-size: var(--font-size-2xl); }
.review dl, .success-card dl { display: grid; gap: var(--space-3); margin: 0; }
.review dl div, .success-card dl div { display: flex; justify-content: space-between; gap: var(--space-4); padding-bottom: var(--space-3); border-block-end: 1px solid var(--color-border-soft); }
.review dt, .success-card dt { color: var(--color-text-muted); }
.review dd, .success-card dd { margin: 0; font-weight: 600; text-align: end; }
.review-note { display: flex; align-items: center; gap: var(--space-2); padding: var(--space-3); border-radius: var(--radius-md); background: var(--color-info-soft); color: var(--color-info); font-size: var(--font-size-xs); }
.review-note.expired { background: var(--color-danger-soft); color: var(--color-danger); }
.success-wrap, .state-card { width: min(100%, 40rem); margin-inline: auto; }
.success-card { display: grid; justify-items: center; text-align: center; }
.success-icon { display: grid; width: 4.5rem; height: 4.5rem; border-radius: 1.35rem; background: var(--color-success-soft); color: var(--color-success); place-items: center; }
.eyebrow { margin-top: var(--space-4); color: var(--color-success); font-weight: 600; }
.success-card h2 { margin: var(--space-1) 0; font-size: var(--font-size-2xl); }
.success-card > p { max-width: 30rem; margin: 0 0 var(--space-3); color: var(--color-text-muted); }
.success-card dl { width: 100%; margin-top: var(--space-6); text-align: start; }
.success-actions { display: grid; width: 100%; gap: var(--space-2); margin-top: var(--space-6); }
@media (max-width: 900px) { .withdraw-layout { grid-template-columns: 1fr; } .withdraw-aside { grid-template-columns: 1fr 1fr; } }
@media (max-width: 767px) {
  .withdraw-aside { grid-template-columns: 1fr; }
}
</style>
