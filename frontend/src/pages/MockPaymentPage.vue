<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import type { Transaction } from '@/types'
import { walletService } from '@/services/wallet.service'
import { formatToman, toPersianDigits } from '@/utils/formatters'
import AppButton from '@/components/ui/AppButton.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import AppLogo from '@/components/layout/AppLogo.vue'

const route = useRoute()
const paymentId = computed(() => String(route.params.id || ''))
const amount = ref('0')
const seconds = ref(9 * 60 + 59)
const loading = ref(true)
const submitting = ref(false)
const status = ref<'form' | 'success' | 'failed'>('form')
const transaction = ref<Transaction | null>(null)
const error = ref('')

const remaining = computed(() => {
  const minutes = Math.floor(seconds.value / 60).toString().padStart(2, '0')
  const rest = (seconds.value % 60).toString().padStart(2, '0')
  return toPersianDigits(`${minutes}:${rest}`)
})

const timer = window.setInterval(() => {
  if (loading.value || status.value !== 'form') return
  seconds.value -= 1
  if (seconds.value <= 0) {
    status.value = 'failed'
    error.value = 'مهلت پرداخت به پایان رسید. یک درگاه تازه بسازید.'
  }
}, 1000)

async function loadPayment() {
  loading.value = true
  try {
    const intent = await walletService.getTomanDeposit(paymentId.value)
    amount.value = intent.amount
    seconds.value = Math.max(0, Math.floor((Date.parse(intent.expiresAt) - Date.now()) / 1000))
    if (seconds.value <= 0) throw new Error('مهلت پرداخت به پایان رسیده است؛ یک درگاه تازه بسازید.')
  } catch (caught) {
    status.value = 'failed'
    error.value = caught instanceof Error ? caught.message : 'اطلاعات این پرداخت در دسترس نیست.'
  } finally {
    loading.value = false
  }
}

async function pay() {
  if (submitting.value || status.value !== 'form') return
  submitting.value = true
  error.value = ''
  try {
    transaction.value = await walletService.completeTomanDeposit(paymentId.value)
    status.value = 'success'
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : 'پرداخت آزمایشی تکمیل نشد.'
  } finally {
    submitting.value = false
  }
}

function failPayment() {
  status.value = 'failed'
  error.value = 'پرداخت به درخواست شما ناموفق شبیه‌سازی شد؛ هیچ مبلغی جابه‌جا نشده است.'
}

onBeforeUnmount(() => window.clearInterval(timer))
onMounted(loadPayment)
</script>

<template>
  <main class="gateway-page">
    <header class="gateway-header">
      <AppLogo />
      <span><AppIcon name="shield" :size="18" /> درگاه آزمایشی امن</span>
    </header>

    <AppCard class="gateway-card" padding="lg">
      <div v-if="loading" class="gateway-loading" aria-label="در حال دریافت اطلاعات پرداخت"><AppSkeleton height="4rem" /><AppSkeleton height="12rem" /><AppSkeleton height="10rem" /></div>
      <template v-else-if="status === 'form'">
        <div class="bank-heading">
          <span class="bank-mark"><AppIcon name="bank" :size="28" /></span>
          <div><small>شبیه‌ساز درگاه بانکی</small><h1>پرداخت اینترنتی</h1></div>
          <span class="demo-badge">نسخه نمایشی</span>
        </div>

        <div class="merchant">
          <div><span>پذیرنده</span><strong>روشا — دارایی دیجیتال</strong></div>
          <div><span>شناسه پرداخت</span><bdi>{{ paymentId }}</bdi></div>
          <div class="amount"><span>مبلغ قابل پرداخت</span><strong>{{ formatToman(amount) }}</strong></div>
        </div>

        <div class="demo-fields" aria-label="اطلاعات نمایشی کارت">
          <label><span>شماره کارت</span><input value="۶۲۱۹ •••• •••• ۷۸۱۷" disabled /></label>
          <div><label><span>CVV2</span><input value="•••" disabled /></label><label><span>انقضا</span><input value="•• / ••" disabled /></label></div>
          <p><AppIcon name="info" :size="17" /> برای این شبیه‌ساز نیازی به ورود اطلاعات واقعی بانکی نیست.</p>
        </div>

        <div v-if="error" class="gateway-error" role="alert"><AppIcon name="warning" :size="18" />{{ error }}</div>
        <div class="gateway-actions">
          <AppButton size="lg" block :loading="submitting" @click="pay">پرداخت موفق آزمایشی</AppButton>
          <AppButton size="lg" block variant="secondary" :disabled="submitting" @click="failPayment">شبیه‌سازی پرداخت ناموفق</AppButton>
        </div>
        <div class="timer"><AppIcon name="clock" :size="17" /> زمان باقی‌مانده <bdi>{{ remaining }}</bdi></div>
      </template>

      <div v-else class="result-state" :class="status">
        <span class="result-mark"><AppIcon :name="status === 'success' ? 'check' : 'warning'" :size="34" /></span>
        <small>{{ status === 'success' ? 'پرداخت تأیید شد' : 'پرداخت تکمیل نشد' }}</small>
        <h1>{{ status === 'success' ? 'موجودی تومان افزایش یافت' : 'جابه‌جایی وجه انجام نشد' }}</h1>
        <p>{{ status === 'success' ? `${formatToman(amount)} با موفقیت به کیف پول شما افزوده شد.` : error }}</p>
        <div v-if="transaction" class="tracking"><span>شماره پیگیری</span><bdi>{{ transaction.referenceNumber }}</bdi></div>
        <div class="gateway-actions">
          <AppButton v-if="status === 'success'" block size="lg" :to="transaction ? `/app/transactions?detail=${transaction.id}` : '/app/wallet'">مشاهده تراکنش</AppButton>
          <AppButton v-else block size="lg" to="/app/deposit/toman">ساخت پرداخت تازه</AppButton>
          <AppButton block variant="secondary" to="/app/wallet">بازگشت به کیف پول</AppButton>
        </div>
      </div>
    </AppCard>

    <footer>این صفحه فقط شبیه‌ساز محصول است و هیچ اطلاعات بانکی دریافت نمی‌کند.</footer>
  </main>
</template>

<style scoped>
.gateway-page { min-height: 100dvh; padding: var(--space-6); background: radial-gradient(circle at 50% 0, rgba(67,139,255,.15), transparent 30rem), var(--color-bg-app); }
.gateway-header { display: flex; width: min(100%, 38rem); align-items: center; justify-content: space-between; margin: 0 auto var(--space-6); }
.gateway-header > span { display: inline-flex; align-items: center; gap: var(--space-2); color: var(--color-success); font-size: var(--font-size-xs); }
.gateway-card { width: min(100%, 38rem); margin-inline: auto; }
.gateway-loading { display: grid; gap: var(--space-4); }
.bank-heading { display: grid; grid-template-columns: auto 1fr auto; align-items: center; gap: var(--space-3); }
.bank-mark { display: grid; width: 3.5rem; height: 3.5rem; border-radius: 1rem; background: var(--color-primary-soft); color: var(--color-primary); place-items: center; }
.bank-heading small { color: var(--color-text-muted); }.bank-heading h1 { margin: .1rem 0 0; font-size: var(--font-size-xl); }
.demo-badge { padding: .3rem .65rem; border-radius: var(--radius-pill); background: var(--color-warning-soft); color: var(--color-warning); font-size: var(--font-size-xs); }
.merchant { display: grid; gap: var(--space-3); margin-block: var(--space-6); padding: var(--space-4); border: 1px solid var(--color-border-soft); border-radius: var(--radius-lg); background: var(--color-surface-2); }
.merchant > div { display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); }.merchant span { color: var(--color-text-muted); }.merchant bdi { direction: ltr; font-weight: 600; }.merchant .amount { padding-top: var(--space-3); border-block-start: 1px dashed var(--color-border); }.merchant .amount strong { color: var(--color-primary); font-size: var(--font-size-lg); }
.demo-fields { display: grid; gap: var(--space-3); }.demo-fields label { display: grid; gap: var(--space-2); color: var(--color-text-secondary); font-size: var(--font-size-xs); }.demo-fields > div { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-3); }.demo-fields input { min-height: var(--control-height); padding-inline: var(--space-3); border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface-3); color: var(--color-text-secondary); direction: ltr; text-align: center; -webkit-text-fill-color: var(--color-text-secondary); opacity: 1; }.demo-fields p { display: flex; gap: var(--space-2); margin: 0; padding: var(--space-3); border-radius: var(--radius-md); background: var(--color-info-soft); color: var(--color-info); font-size: var(--font-size-xs); }
.gateway-actions { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-2); margin-top: var(--space-5); }.timer { display: flex; align-items: center; justify-content: center; gap: var(--space-2); margin-top: var(--space-4); color: var(--color-text-muted); font-size: var(--font-size-xs); }.timer bdi { color: var(--color-text-primary); font-weight: 700; direction: ltr; }
.gateway-error { display: flex; gap: var(--space-2); margin-top: var(--space-4); padding: var(--space-3); border-radius: var(--radius-md); background: var(--color-danger-soft); color: var(--color-danger); }
.result-state { display: grid; justify-items: center; padding-block: var(--space-6); text-align: center; }.result-mark { display: grid; width: 4.75rem; height: 4.75rem; border-radius: 1.4rem; place-items: center; }.result-state.success .result-mark { background: var(--color-success-soft); color: var(--color-success); }.result-state.failed .result-mark { background: var(--color-danger-soft); color: var(--color-danger); }.result-state > small { margin-top: var(--space-4); color: var(--color-text-muted); }.result-state h1 { margin: var(--space-1) 0; font-size: var(--font-size-2xl); }.result-state > p { max-width: 28rem; margin: 0; color: var(--color-text-secondary); }.result-state .gateway-actions { width: 100%; }.tracking { display: grid; width: 100%; margin-top: var(--space-5); padding: var(--space-3); border: 1px dashed var(--color-border); border-radius: var(--radius-md); }.tracking span { color: var(--color-text-muted); font-size: var(--font-size-xs); }.tracking bdi { direction: ltr; font-weight: 700; }
.gateway-page > footer { width: min(100%, 38rem); margin: var(--space-5) auto 0; color: var(--color-text-muted); font-size: var(--font-size-xs); text-align: center; }
@media (max-width: 600px) { .gateway-page { padding: var(--space-4); }.gateway-header { margin-bottom: var(--space-4); }.gateway-header > span { font-size: .68rem; }.bank-heading { grid-template-columns: auto 1fr; }.demo-badge { grid-column: 1 / -1; justify-self: start; }.gateway-actions { grid-template-columns: 1fr; } }
</style>
