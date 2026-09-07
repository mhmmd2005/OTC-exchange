<script setup lang="ts">
import { computed, defineAsyncComponent, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type {
  AssetNetwork,
  CryptoWithdrawalEstimate,
  SecurityOverview,
  Transaction,
  VerificationSummary,
  WithdrawalOtpChallenge,
} from '@/types'
import { ApiError } from '@/services/api'
import { securityService } from '@/services/security.service'
import { transactionService } from '@/services/transaction.service'
import { verificationService } from '@/services/verification.service'
import { walletService } from '@/services/wallet.service'
import { useWalletStore } from '@/stores/wallet'
import { compareDecimal } from '@/utils/decimal'
import { formatCrypto, formatPersianDateTime, formatToman, normalizeDigits, toPersianDigits } from '@/utils/formatters'
import AppAmountInput from '@/components/ui/AppAmountInput.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import AppInput from '@/components/ui/AppInput.vue'
import AppModal from '@/components/ui/AppModal.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import OtpInput from '@/components/ui/OtpInput.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import AssetSelect from '@/components/finance/AssetSelect.vue'
import TransactionList from '@/components/transactions/TransactionList.vue'
import NetworkSelector from '@/components/wallet/NetworkSelector.vue'

const DemoCodeHint = import.meta.env.DEV && import.meta.env.VITE_USE_MOCK_API === 'true'
  ? defineAsyncComponent(() => import('@/components/ui/DemoCodeHint.vue'))
  : null

type ConfirmationStage = 'review' | 'security'

const route = useRoute()
const router = useRouter()
const walletStore = useWalletStore()
const verification = ref<VerificationSummary | null>(null)
const security = ref<SecurityOverview | null>(null)
const selectedSymbol = ref('')
const networks = ref<AssetNetwork[]>([])
const networkCode = ref('')
const address = ref('')
const memo = ref('')
const amount = ref('')
const otp = ref('')
const twoFactorCode = ref('')
const transactions = ref<Transaction[]>([])
const estimate = ref<CryptoWithdrawalEstimate | null>(null)
const otpChallenge = ref<WithdrawalOtpChallenge | null>(null)
const idempotencyKey = ref('')
const result = ref<Transaction | null>(null)
const loading = ref(true)
const estimating = ref(false)
const requestingOtp = ref(false)
const resendingOtp = ref(false)
const submitting = ref(false)
const confirmationOpen = ref(false)
const confirmationStage = ref<ConfirmationStage>('review')
const error = ref('')
const addressError = ref('')
const memoError = ref('')
const amountError = ref('')
const networkError = ref('')
const otpError = ref('')
const twoFactorError = ref('')
const securityMessage = ref('')
const historyError = ref('')
const otpRateLimitUntil = ref('')
const nowMs = ref(Date.now())
const resultHeading = ref<HTMLElement | null>(null)
const confirmationPrimaryButton = ref<InstanceType<typeof AppButton> | null>(null)
const confirmationBackButton = ref<InstanceType<typeof AppButton> | null>(null)
let loadSequence = 0
let estimateSequence = 0
let clockTimer: number | undefined

const cryptoAssets = computed(() => walletStore.assets.filter((asset) => asset.symbol !== 'IRT'))
const assetBalances = computed<Record<string, string>>(() => Object.fromEntries(
  cryptoAssets.value.map((asset) => [asset.symbol, asset.available]),
))
const disabledAssetSymbols = computed(() => cryptoAssets.value
  .filter((asset) => !asset.withdrawalEnabled)
  .map((asset) => asset.symbol))
const disabledAssetDescriptions = computed<Record<string, string>>(() => Object.fromEntries(
  disabledAssetSymbols.value.map((symbol) => [symbol, 'برداشت این ارز موقتاً غیرفعال است']),
))
const selectedAsset = computed(() => cryptoAssets.value.find((asset) => asset.symbol === selectedSymbol.value))
const selectedNetwork = computed(() => networks.value.find((network) => network.code === networkCode.value))
const canWithdraw = computed(() => verification.value
  ? verification.value.status === 'verified' && !['level_0', 'level_1'].includes(verification.value.currentLevel)
  : true)
const hasActiveNetwork = computed(() => networks.value.some((network) => network.withdrawalEnabled && network.status === 'active'))
const estimateExpired = computed(() => !estimate.value || Date.parse(estimate.value.expiresAt) <= nowMs.value)
const estimateSecondsRemaining = computed(() => estimate.value
  ? Math.max(0, Math.ceil((Date.parse(estimate.value.expiresAt) - nowMs.value) / 1_000))
  : 0)
const otpChallengeExpired = computed(() => !otpChallenge.value
  || Date.parse(otpChallenge.value.expiresAt) <= nowMs.value)
const otpSecondsRemaining = computed(() => otpChallenge.value
  ? Math.max(0, Math.ceil((Date.parse(otpChallenge.value.expiresAt) - nowMs.value) / 1_000))
  : 0)
const otpResendDelay = computed(() => otpChallenge.value
  ? Math.max(0, Math.ceil((Date.parse(otpChallenge.value.resendAvailableAt) - Date.now()) / 1_000))
  : 0)
const otpRateLimitSeconds = computed(() => otpRateLimitUntil.value
  ? Math.max(0, Math.ceil((Date.parse(otpRateLimitUntil.value) - nowMs.value) / 1_000))
  : 0)

function createIdempotencyKey(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') return crypto.randomUUID()
  const randomPart = Math.random().toString(36).slice(2)
  return `withdrawal_${Date.now().toString(36)}_${randomPart}`
}

function invalidateEstimate(closeConfirmation = true) {
  estimateSequence += 1
  estimating.value = false
  estimate.value = null
  otpChallenge.value = null
  idempotencyKey.value = ''
  otp.value = ''
  twoFactorCode.value = ''
  securityMessage.value = ''
  otpRateLimitUntil.value = ''
  if (closeConfirmation && confirmationOpen.value && !submitting.value) confirmationOpen.value = false
}

function applyOtpRateLimit(error: unknown) {
  if (!(error instanceof ApiError) || error.code !== 'RATE_LIMITED') return
  const retryAfterSeconds = Number(error.details?.retryAfterSeconds)
  if (!Number.isFinite(retryAfterSeconds) || retryAfterSeconds <= 0) return
  otpRateLimitUntil.value = new Date(Date.now() + retryAfterSeconds * 1_000).toISOString()
  if (otpChallenge.value) {
    otpChallenge.value = {
      ...otpChallenge.value,
      resendAvailableAt: otpRateLimitUntil.value,
    }
  }
}

function chooseNetwork(code: string) {
  if (networkCode.value === code) return
  invalidateEstimate()
  networkCode.value = code
  memo.value = ''
  historyError.value = ''
  networkError.value = ''
  addressError.value = ''
  memoError.value = ''
}

async function loadAssetData() {
  const symbol = selectedSymbol.value
  const requestId = ++loadSequence
  networks.value = []
  networkCode.value = ''
  transactions.value = []
  invalidateEstimate()
  address.value = ''
  memo.value = ''
  if (!symbol) return
  loading.value = true
  error.value = ''
  try {
    const [networkResult, historyResult] = await Promise.allSettled([
      walletService.getNetworks(symbol),
      transactionService.list({ type: 'crypto_withdrawal', assetSymbol: symbol, pageSize: 5 }),
    ])
    if (requestId !== loadSequence) return
    if (networkResult.status === 'rejected') throw networkResult.reason
    networks.value = networkResult.value
    if (historyResult.status === 'fulfilled') transactions.value = historyResult.value.items
    else historyError.value = historyResult.reason instanceof Error ? historyResult.reason.message : 'سابقه برداشت‌ها دریافت نشد.'
    networkCode.value = networkResult.value.find((network) => network.withdrawalEnabled && network.status === 'active')?.code || ''
  } catch (caught) {
    if (requestId === loadSequence) error.value = caught instanceof Error ? caught.message : 'اطلاعات برداشت رمزارز دریافت نشد.'
  } finally {
    if (requestId === loadSequence) loading.value = false
  }
}

function syncAssetFromRoute() {
  if (!cryptoAssets.value.length) return
  const routeSymbol = String(route.params.symbol || '').toUpperCase()
  const requestedAsset = cryptoAssets.value.find((asset) => asset.symbol.toUpperCase() === routeSymbol)
  const fallbackAsset = cryptoAssets.value.find((asset) => asset.withdrawalEnabled) || cryptoAssets.value[0]
  const nextSymbol = requestedAsset?.symbol || fallbackAsset?.symbol || ''
  if (nextSymbol && selectedSymbol.value !== nextSymbol) selectedSymbol.value = nextSymbol
  if (nextSymbol && routeSymbol !== nextSymbol.toUpperCase()) {
    void router.replace({ name: 'crypto-withdrawal', params: { symbol: nextSymbol } })
  }
}

async function initialize() {
  loading.value = true
  error.value = ''
  try {
    const [, verificationSummary, securityOverview] = await Promise.all([
      walletStore.fetchWallet(),
      verificationService.getSummary(),
      securityService.getOverview(),
    ])
    verification.value = verificationSummary
    security.value = securityOverview
    syncAssetFromRoute()
    if (!selectedSymbol.value) loading.value = false
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : 'برداشت رمزارز آماده نشد.'
    loading.value = false
  }
}

function validateAddress(): boolean {
  addressError.value = ''
  const value = address.value.trim()
  const network = selectedNetwork.value
  if (!value) {
    addressError.value = 'آدرس مقصد را وارد کنید.'
    return false
  }
  if (/\s/.test(value)) {
    addressError.value = 'آدرس مقصد نباید فاصله داشته باشد.'
    return false
  }
  if (network?.addressRegex) {
    try {
      if (!new RegExp(network.addressRegex).test(value)) {
        addressError.value = `ساختار آدرس با شبکه ${network.code} هم‌خوانی ندارد.`
        return false
      }
    } catch {
      if (value.length < 12) {
        addressError.value = 'آدرس مقصد کوتاه‌تر از مقدار معتبر است.'
        return false
      }
    }
  } else if (value.length < 12) {
    addressError.value = 'آدرس مقصد کوتاه‌تر از مقدار معتبر است.'
    return false
  }
  return true
}

function validateAmount(): boolean {
  amountError.value = ''
  const network = selectedNetwork.value
  const asset = selectedAsset.value
  if (!amount.value || compareDecimal(amount.value, '0') <= 0) {
    amountError.value = 'مقدار برداشت را وارد کنید.'
  } else if (network && compareDecimal(amount.value, network.minimumWithdrawal) < 0) {
    amountError.value = `حداقل برداشت ${formatCrypto(network.minimumWithdrawal, { symbol: asset?.symbol })} است.`
  } else if (asset && compareDecimal(amount.value, asset.available) > 0) {
    amountError.value = 'موجودی قابل برداشت این ارز کافی نیست.'
  }
  return !amountError.value
}

function validateForm(): boolean {
  networkError.value = ''
  memoError.value = ''
  error.value = ''
  if (!selectedNetwork.value || !selectedNetwork.value.withdrawalEnabled || selectedNetwork.value.status !== 'active') {
    networkError.value = 'یک شبکه فعال برای برداشت انتخاب کنید.'
  }
  if (selectedNetwork.value?.memoRequired && !memo.value.trim()) {
    memoError.value = 'وارد کردن ممو یا تگ برای این شبکه الزامی است.'
  }
  const validAddress = validateAddress()
  const validAmount = validateAmount()
  return !networkError.value && !memoError.value && validAddress && validAmount
}

async function requestEstimate(showErrors = true): Promise<CryptoWithdrawalEstimate | null> {
  const requestId = ++estimateSequence
  estimate.value = null
  otpChallenge.value = null
  idempotencyKey.value = ''
  if (!selectedAsset.value || !selectedNetwork.value || !amount.value) return null
  if (!validateAmount()) {
    if (!showErrors) amountError.value = ''
    return null
  }
  estimating.value = true
  try {
    const response = await walletService.estimateCryptoWithdrawal({
      assetSymbol: selectedAsset.value.symbol,
      networkCode: selectedNetwork.value.code,
      address: address.value.trim(),
      memo: memo.value.trim() || undefined,
      amount: amount.value,
    })
    if (requestId !== estimateSequence) return null
    estimate.value = response
    idempotencyKey.value = createIdempotencyKey()
    nowMs.value = Date.now()
    return response
  } catch (caught) {
    if (requestId === estimateSequence && showErrors) {
      if (caught instanceof ApiError) {
        addressError.value = caught.details?.fields?.address || ''
        memoError.value = caught.details?.fields?.memo || ''
        networkError.value = caught.details?.fields?.networkCode || ''
        amountError.value = caught.details?.fields?.amount || ''
      }
      if (!addressError.value && !memoError.value && !networkError.value && !amountError.value) {
        amountError.value = caught instanceof Error ? caught.message : 'محاسبه کارمزد برداشت انجام نشد.'
      }
    }
    return null
  } finally {
    if (requestId === estimateSequence) estimating.value = false
  }
}

async function prepareReview() {
  if (!validateForm()) return
  const normalizedAddress = address.value.trim()
  const normalizedMemo = memo.value.trim() || undefined
  const reusableEstimate = estimate.value
    && !estimateExpired.value
    && estimate.value.assetSymbol === selectedSymbol.value
    && estimate.value.networkCode === networkCode.value
    && estimate.value.amount === amount.value
    && estimate.value.address === normalizedAddress
    && estimate.value.memo === normalizedMemo
  const response = reusableEstimate
    ? estimate.value
    : await requestEstimate()
  if (!response) return
  confirmationStage.value = 'review'
  otp.value = ''
  twoFactorCode.value = ''
  otpError.value = ''
  twoFactorError.value = ''
  securityMessage.value = ''
  confirmationOpen.value = true
}

async function continueToSecurity() {
  if (requestingOtp.value || !estimate.value) return
  if (otpRateLimitSeconds.value > 0) return
  if (estimateExpired.value) {
    otpError.value = 'مهلت این برآورد تمام شده است؛ مبلغ را دوباره بررسی کنید.'
    return
  }
  const estimateToken = estimate.value.estimateToken
  requestingOtp.value = true
  otpError.value = ''
  securityMessage.value = ''
  try {
    const response = await walletService.requestCryptoWithdrawalOtp(
      estimate.value.estimateToken,
      estimate.value.estimateVersion,
    )
    if (!confirmationOpen.value || estimate.value?.estimateToken !== estimateToken) return
    otpChallenge.value = response
    otpRateLimitUntil.value = ''
    otp.value = ''
    nowMs.value = Date.now()
    confirmationStage.value = 'security'
  } catch (caught) {
    applyOtpRateLimit(caught)
    otpError.value = caught instanceof Error ? caught.message : 'ارسال کد تأیید برداشت انجام نشد.'
    if (caught instanceof ApiError && caught.code === 'QUOTE_EXPIRED') {
      invalidateEstimate(false)
      amountError.value = caught.message
    }
  } finally {
    requestingOtp.value = false
  }
}

async function submitWithdrawal() {
  if (submitting.value) return
  otpError.value = ''
  twoFactorError.value = ''
  if (otp.value.length !== 6) {
    otpError.value = 'کد تأیید شش‌رقمی را کامل وارد کنید.'
    return
  }
  const normalizedTwoFactorCode = normalizeDigits(twoFactorCode.value).replace(/\D/g, '')
  if (security.value?.twoFactorEnabled && normalizedTwoFactorCode.length !== 6) {
    twoFactorError.value = 'کد برنامه تأییدکننده را کامل وارد کنید.'
    return
  }
  if (!estimate.value || !otpChallenge.value || !idempotencyKey.value) {
    otpError.value = 'نشست تأیید برداشت کامل نیست؛ از مرحله بررسی دوباره ادامه دهید.'
    return
  }
  if (estimateExpired.value) {
    confirmationOpen.value = false
    invalidateEstimate(false)
    amountError.value = 'مهلت برآورد برداشت تمام شده است؛ دوباره ادامه دهید.'
    return
  }
  if (otpChallengeExpired.value) {
    otpError.value = 'مهلت کد تأیید تمام شده است؛ کد تازه‌ای دریافت کنید.'
    return
  }
  submitting.value = true
  error.value = ''
  try {
    result.value = await walletService.createCryptoWithdrawal({
      estimateToken: estimate.value.estimateToken,
      estimateVersion: estimate.value.estimateVersion,
      otpChallengeToken: otpChallenge.value.challengeToken,
      otp: otp.value,
      twoFactorCode: security.value?.twoFactorEnabled ? normalizedTwoFactorCode : undefined,
      idempotencyKey: idempotencyKey.value,
    })
    confirmationOpen.value = false
    await walletStore.refresh()
  } catch (caught) {
    if (caught instanceof ApiError) {
      otpError.value = caught.details?.fields?.otp || ''
      twoFactorError.value = caught.details?.fields?.twoFactorCode || ''
      addressError.value = caught.details?.fields?.address || ''
      memoError.value = caught.details?.fields?.memo || ''
      networkError.value = caught.details?.fields?.networkCode || ''
      amountError.value = caught.details?.fields?.amount || ''
      if (addressError.value || memoError.value || networkError.value || amountError.value) {
        error.value = caught.message
        confirmationOpen.value = false
      }
      if (caught.code === 'QUOTE_EXPIRED') {
        confirmationOpen.value = false
        invalidateEstimate(false)
        amountError.value = caught.message
      }
    }
    if (!otpError.value && !twoFactorError.value && confirmationOpen.value) {
      otpError.value = caught instanceof Error ? caught.message : 'تأیید برداشت انجام نشد.'
    }
  } finally {
    submitting.value = false
  }
}

async function resendOtp() {
  if (resendingOtp.value || !otpChallenge.value) return
  otpError.value = ''
  securityMessage.value = ''
  resendingOtp.value = true
  try {
    const challengeToken = otpChallenge.value.challengeToken
    const response = await walletService.resendCryptoWithdrawalOtp(challengeToken)
    if (otpChallenge.value?.challengeToken !== challengeToken) return
    otpChallenge.value = response
    otpRateLimitUntil.value = ''
    otp.value = ''
    nowMs.value = Date.now()
    securityMessage.value = 'کد تأیید دوباره ارسال شد.'
  } catch (caught) {
    applyOtpRateLimit(caught)
    otpError.value = caught instanceof Error ? caught.message : 'ارسال دوباره کد انجام نشد.'
    if (caught instanceof ApiError && caught.code === 'QUOTE_EXPIRED') {
      confirmationOpen.value = false
      invalidateEstimate(false)
      amountError.value = caught.message
    }
  } finally {
    resendingOtp.value = false
  }
}

function useMaximum() {
  if (selectedAsset.value) amount.value = selectedAsset.value.available
}

watch(selectedSymbol, (symbol, previousSymbol) => {
  if (previousSymbol && previousSymbol !== symbol) amount.value = ''
  result.value = null
  void loadAssetData()
  const routeSymbol = String(route.params.symbol || '').toUpperCase()
  if (symbol && routeSymbol !== symbol.toUpperCase()) {
    void router.replace({ name: 'crypto-withdrawal', params: { symbol } })
  }
})
watch(() => route.params.symbol, syncAssetFromRoute)
watch(amount, () => { invalidateEstimate(); amountError.value = '' })
watch(address, () => { invalidateEstimate(); addressError.value = '' })
watch(memo, () => { invalidateEstimate(); memoError.value = '' })
watch(result, async (value) => {
  if (!value) return
  await nextTick()
  resultHeading.value?.focus({ preventScroll: true })
}, { flush: 'post' })
watch(estimateExpired, async (expired, wasExpired) => {
  if (!expired || wasExpired || !confirmationOpen.value) return
  const primaryElement = confirmationPrimaryButton.value?.$el as HTMLElement | undefined
  const primaryHadFocus = document.activeElement === primaryElement
  await nextTick()
  if (primaryHadFocus) {
    const backElement = confirmationBackButton.value?.$el as HTMLElement | undefined
    backElement?.focus({ preventScroll: true })
  }
})
watch(otpChallengeExpired, async (expired, wasExpired) => {
  if (!expired || wasExpired || !confirmationOpen.value || confirmationStage.value !== 'security') return
  const primaryElement = confirmationPrimaryButton.value?.$el as HTMLElement | undefined
  const primaryHadFocus = document.activeElement === primaryElement
  await nextTick()
  if (primaryHadFocus) {
    const backElement = confirmationBackButton.value?.$el as HTMLElement | undefined
    backElement?.focus({ preventScroll: true })
  }
})
watch(confirmationOpen, (open) => {
  if (!open && !submitting.value) {
    confirmationStage.value = 'review'
    otpChallenge.value = null
    otp.value = ''
    twoFactorCode.value = ''
  }
})
onMounted(() => {
  clockTimer = window.setInterval(() => { nowMs.value = Date.now() }, 1_000)
  void initialize()
})
onBeforeUnmount(() => {
  loadSequence += 1
  estimateSequence += 1
  if (clockTimer !== undefined) window.clearInterval(clockTimer)
})
</script>

<template>
  <div class="page page--mobile-cta crypto-withdrawal-page">
    <PageHeader title="برداشت رمزارز" description="ارسال امن دارایی به کیف پول خارج از روشا" back-to="/app/wallet" />

    <div v-if="loading && !selectedAsset" class="withdraw-skeleton">
      <AppSkeleton height="42rem" radius="var(--radius-xl)" />
      <AppSkeleton height="25rem" radius="var(--radius-xl)" />
    </div>

    <AppCard v-else-if="error && !selectedAsset" class="state-card">
      <EmptyState icon="warning" title="برداشت رمزارز آماده نشد" :description="error"><AppButton @click="initialize">تلاش دوباره</AppButton></EmptyState>
    </AppCard>

    <AppCard v-else-if="!selectedAsset" class="state-card">
      <EmptyState icon="wallet" title="رمزارزی برای برداشت وجود ندارد" description="در حال حاضر هیچ کیف پول رمزارزی در حساب شما فعال نیست."><AppButton to="/app/wallet">بازگشت به کیف پول</AppButton></EmptyState>
    </AppCard>

    <AppCard v-else-if="!canWithdraw" class="state-card">
      <EmptyState icon="verify" title="احراز هویت سطح دو لازم است" description="برای برداشت رمزارز باید احراز هویت سطح ۲ را تکمیل کنید.">
        <AppButton to="/app/verification">تکمیل احراز هویت</AppButton>
      </EmptyState>
    </AppCard>

    <div v-else-if="result && selectedAsset" class="success-wrap">
      <AppCard class="success-card" padding="lg">
        <span class="success-icon"><AppIcon name="check" :size="31" /></span>
        <span class="eyebrow">برداشت با موفقیت ثبت شد</span>
        <h2 ref="resultHeading" tabindex="-1"><span class="sr-only">برداشت با موفقیت ثبت شد، مقدار </span>{{ formatCrypto(result.amount, { symbol: result.assetSymbol }) }}</h2>
        <p>درخواست وارد بررسی امنیتی و سپس صف ارسال شبکه شد. وضعیت آن را از تراکنش‌ها پیگیری کنید.</p>
        <StatusBadge domain="transaction" :status="result.status" />
        <dl>
          <div><dt>شماره پیگیری</dt><dd dir="ltr">{{ result.referenceNumber }}</dd></div>
          <div><dt>شبکه</dt><dd dir="ltr">{{ result.networkCode }}</dd></div>
          <div><dt>کارمزد شبکه</dt><dd>{{ formatCrypto(result.fee || '0', { symbol: result.assetSymbol }) }}</dd></div>
          <div><dt>زمان ثبت</dt><dd>{{ formatPersianDateTime(result.createdAt) }}</dd></div>
        </dl>
        <div class="success-address"><span>آدرس مقصد</span><bdi dir="ltr">{{ result.address }}</bdi></div>
        <div class="success-actions"><AppButton block to="/app/transactions">پیگیری تراکنش</AppButton><AppButton block variant="secondary" to="/app/wallet">بازگشت به کیف پول</AppButton></div>
      </AppCard>
    </div>

    <div v-else-if="selectedAsset" class="withdraw-layout">
      <section aria-label="فرم برداشت رمزارز">
        <AppCard padding="lg">
          <div class="flow-heading"><span><AppIcon name="upload" :size="24" /></span><div><h2>مشخصات برداشت</h2><p>آدرس و شبکه را با دقت بررسی کنید؛ تراکنش شبکه برگشت‌پذیر نیست.</p></div></div>
          <form class="withdraw-form" @submit.prevent="prepareReview">
            <AssetSelect
              v-model="selectedSymbol"
              :assets="cryptoAssets"
              :balances="assetBalances"
              :disabled-symbols="disabledAssetSymbols"
              :disabled-descriptions="disabledAssetDescriptions"
              label="ارز مورد نظر"
              balance-label="قابل برداشت"
              show-balance
              required
            />
            <NetworkSelector
              :model-value="networkCode"
              :networks="networks"
              mode="withdrawal"
              label="شبکه انتقال"
              :error="networkError"
              @update:model-value="chooseNetwork"
            />
            <AppInput v-model="address" label="آدرس کیف پول مقصد" placeholder="آدرس را وارد یا جای‌گذاری کنید" :error="addressError" ltr autocomplete="off" icon="wallet" />
            <AppInput v-if="selectedNetwork?.memoRequired" v-model="memo" label="ممو / تگ مقصد" placeholder="ممو یا تگ را دقیقاً وارد کنید" :error="memoError" ltr autocomplete="off" />
            <div>
              <AppAmountInput
                v-model="amount"
                label="مقدار برداشت"
                :suffix="selectedAsset.symbol"
                type="crypto"
                :balance="selectedAsset.available"
                balance-label="قابل برداشت"
                :error="amountError"
                @blur="requestEstimate(false)"
              />
              <button type="button" class="max-button" @click="useMaximum">حداکثر</button>
            </div>

            <div v-if="selectedNetwork" class="fee-preview" :class="{ loading: estimating }">
              <div><span>حداقل برداشت</span><strong>{{ formatCrypto(selectedNetwork.minimumWithdrawal, { symbol: selectedAsset.symbol }) }}</strong></div>
              <div><span>کارمزد شبکه</span><strong>{{ formatCrypto(estimate?.fee || selectedNetwork.withdrawalFee, { symbol: selectedAsset.symbol }) }}</strong></div>
              <div><span>مبلغ دریافتی مقصد</span><strong class="receivable">{{ estimate ? formatCrypto(estimate.receivable, { symbol: selectedAsset.symbol }) : 'پس از ورود مقدار' }}</strong></div>
              <div><span>زمان تقریبی</span><strong>{{ toPersianDigits(estimate?.estimatedArrivalMinutes || selectedNetwork.estimatedArrivalMinutes) }} دقیقه</strong></div>
            </div>

            <div v-if="error" class="form-error" role="alert"><AppIcon name="warning" :size="18" /><span>{{ error }}</span></div>
            <div class="mobile-cta"><AppButton block size="lg" type="submit" :disabled="!hasActiveNetwork" :loading="estimating">بررسی و ادامه</AppButton></div>
          </form>
        </AppCard>
      </section>

      <aside class="withdraw-aside">
        <AppCard class="balance-card">
          <span>موجودی قابل برداشت {{ selectedAsset.nameFa }}</span>
          <strong>{{ formatCrypto(selectedAsset.available, { symbol: selectedAsset.symbol }) }}</strong>
          <small>{{ formatCrypto(selectedAsset.locked, { symbol: selectedAsset.symbol }) }} در سفارش یا برداشت مسدود است</small>
        </AppCard>
        <div class="danger-note"><AppIcon name="warning" :size="21" /><span><strong>شبکه مقصد را تطبیق دهید</strong><small>ارسال به شبکه یا آدرس اشتباه قابل بازگشت نیست.</small></span></div>
        <AppCard>
          <div class="security-title"><AppIcon name="shield" :size="21" /><div><h3>تأیید امنیتی برداشت</h3><p>برای ثبت نهایی، کد پیامکی{{ security?.twoFactorEnabled ? ' و کد تأیید دومرحله‌ای' : '' }} لازم است.</p></div></div>
          <RouterLink to="/app/security">تنظیمات امنیتی <AppIcon name="chevronLeft" :size="16" /></RouterLink>
        </AppCard>
      </aside>
    </div>

    <AppCard v-if="selectedAsset && !result" class="history-card" padding="none">
      <div class="card-heading"><div><h2>برداشت‌های اخیر {{ selectedAsset.nameFa }}</h2><p>وضعیت ارسال و تأییدهای شبکه</p></div><RouterLink :to="{ path: '/app/transactions', query: { type: 'crypto_withdrawal', asset: selectedAsset.symbol } }">همه برداشت‌ها <AppIcon name="chevronLeft" :size="16" /></RouterLink></div>
      <TransactionList v-if="transactions.length" :transactions="transactions" compact />
      <EmptyState v-else-if="historyError" icon="warning" title="سابقه برداشت‌ها دریافت نشد" :description="historyError"><AppButton variant="secondary" size="sm" @click="loadAssetData">تلاش دوباره</AppButton></EmptyState>
      <EmptyState v-else icon="upload" title="برداشتی ثبت نشده" description="درخواست‌های برداشت این ارز در این بخش نمایش داده می‌شوند." />
    </AppCard>

    <AppModal v-model="confirmationOpen" :title="confirmationStage === 'review' ? 'بررسی برداشت رمزارز' : 'تأیید امنیتی'" :description="confirmationStage === 'review' ? 'مقصد و مبلغ را پیش از تأیید نهایی بررسی کنید.' : 'کد ارسال‌شده را برای ثبت برداشت وارد کنید.'" size="sm" :dismissible="!submitting">
      <div v-if="confirmationStage === 'review' && estimate" class="review">
        <div class="review-total"><span>مبلغ دریافتی مقصد</span><strong>{{ formatCrypto(estimate.receivable, { symbol: estimate.assetSymbol }) }}</strong></div>
        <dl>
          <div><dt>مقدار برداشت</dt><dd>{{ formatCrypto(estimate.amount, { symbol: estimate.assetSymbol }) }}</dd></div>
          <div><dt>معادل تقریبی</dt><dd>{{ formatToman(estimate.tomanEquivalent) }}</dd></div>
          <div><dt>کارمزد شبکه</dt><dd>{{ formatCrypto(estimate.fee, { symbol: estimate.assetSymbol }) }}</dd></div>
          <div><dt>شبکه</dt><dd dir="ltr">{{ estimate.networkCode }}</dd></div>
          <div><dt>زمان تقریبی</dt><dd>{{ toPersianDigits(estimate.estimatedArrivalMinutes) }} دقیقه</dd></div>
          <div><dt>اعتبار برآورد</dt><dd>{{ toPersianDigits(estimateSecondsRemaining) }} ثانیه</dd></div>
        </dl>
        <div class="review-address"><span>آدرس مقصد</span><bdi dir="ltr">{{ estimate.address }}</bdi><small v-if="estimate.memo">Memo: {{ estimate.memo }}</small></div>
        <p v-if="estimateExpired" class="challenge-expiry expired" role="status" aria-atomic="true">اعتبار برآورد برداشت تمام شده است؛ اطلاعات را دوباره بررسی کنید.</p>
        <div class="review-warning"><AppIcon name="warning" :size="18" /> تراکنش رمزارزی پس از ارسال قابل لغو یا بازگشت نیست.</div>
        <div v-if="otpError" class="form-error" role="alert"><AppIcon name="warning" :size="18" /><span>{{ otpError }}</span></div>
        <p v-if="otpRateLimitSeconds" class="rate-limit-message">امکان ارسال کد تا {{ toPersianDigits(otpRateLimitSeconds) }} ثانیه دیگر فعال می‌شود.</p>
        <p v-else-if="otpRateLimitUntil" class="sr-only" role="status">اکنون امکان ارسال کد تأیید فعال است.</p>
      </div>
      <div v-else class="security-step">
        <div class="phone-mark"><AppIcon name="phone" :size="25" /></div>
        <p>کد این برداشت به شماره {{ otpChallenge?.destinationHint || 'ثبت‌شده شما' }} ارسال شد.</p>
        <OtpInput
          :key="otpChallenge?.resendAvailableAt"
          v-model="otp"
          label="کد تأیید برداشت"
          :error="otpError"
          :loading="submitting"
          :resend-loading="resendingOtp"
          :countdown-seconds="otpResendDelay"
          @resend="resendOtp"
        />
        <DemoCodeHint v-if="DemoCodeHint" context="withdrawal" />
        <p v-if="estimateExpired" class="challenge-expiry expired" role="status" aria-atomic="true">اعتبار برآورد برداشت تمام شده است؛ اطلاعات را دوباره بررسی کنید.</p>
        <p v-else-if="otpChallengeExpired" class="challenge-expiry expired" role="status" aria-atomic="true">اعتبار کد تمام شده است؛ ارسال مجدد را بزنید.</p>
        <p v-else-if="otpChallenge" class="challenge-expiry">اعتبار کد: {{ toPersianDigits(otpSecondsRemaining) }} ثانیه</p>
        <p v-if="securityMessage" class="security-message" role="status">{{ securityMessage }}</p>
        <AppInput v-if="security?.twoFactorEnabled" v-model="twoFactorCode" label="کد برنامه تأییدکننده" inputmode="numeric" autocomplete="one-time-code" :error="twoFactorError" ltr />
      </div>
      <template #footer>
        <template v-if="confirmationStage === 'review'">
          <AppButton ref="confirmationPrimaryButton" block :loading="requestingOtp" :disabled="estimateExpired || otpRateLimitSeconds > 0" @click="continueToSecurity">تأیید مقصد و ارسال کد</AppButton>
          <AppButton ref="confirmationBackButton" block variant="secondary" :disabled="requestingOtp" @click="confirmationOpen = false">ویرایش اطلاعات</AppButton>
        </template>
        <template v-else>
          <AppButton ref="confirmationPrimaryButton" block :loading="submitting" :disabled="estimateExpired || otpChallengeExpired" @click="submitWithdrawal">تأیید و ثبت برداشت</AppButton>
          <AppButton ref="confirmationBackButton" block variant="secondary" :disabled="submitting" @click="confirmationStage = 'review'">بازگشت</AppButton>
        </template>
      </template>
    </AppModal>
  </div>
</template>

<style scoped>
.crypto-withdrawal-page { max-width: 78rem; }
.withdraw-layout, .withdraw-skeleton { display: grid; grid-template-columns: minmax(29rem, 1.18fr) minmax(19rem, .62fr); align-items: start; gap: var(--space-5); }
.flow-heading { display: flex; align-items: center; gap: var(--space-3); }
.flow-heading > span { display: grid; width: 3rem; height: 3rem; border-radius: .9rem; background: var(--color-gold-soft); color: var(--color-gold); place-items: center; }
.flow-heading h2 { margin: 0; font-size: var(--font-size-lg); }
.flow-heading p { margin: .1rem 0 0; color: var(--color-text-muted); font-size: var(--font-size-xs); }
.withdraw-form { display: grid; gap: var(--space-5); margin-top: var(--space-6); }
.max-button { margin-top: var(--space-2); padding: 0; border: 0; background: transparent; color: var(--color-primary); font-size: var(--font-size-xs); font-weight: 600; }
.fee-preview { display: grid; gap: var(--space-3); padding: var(--space-4); border: 1px solid var(--color-border-soft); border-radius: var(--radius-lg); background: var(--color-surface-2); transition: opacity var(--transition-fast); }
.fee-preview.loading { opacity: .55; }
.fee-preview div { display: flex; justify-content: space-between; gap: var(--space-4); }
.fee-preview span { color: var(--color-text-muted); font-size: var(--font-size-sm); }
.fee-preview strong { font-size: var(--font-size-sm); text-align: end; }
.fee-preview .receivable { color: var(--color-success); }
.withdraw-aside { display: grid; gap: var(--space-4); }
.balance-card { background: linear-gradient(145deg, var(--color-surface-1), rgba(67,139,255,.08)); }
.balance-card > span { color: var(--color-text-muted); font-size: var(--font-size-xs); }
.balance-card > strong { display: block; margin-top: var(--space-2); font-size: var(--font-size-xl); }
.balance-card > small { display: block; margin-top: .2rem; color: var(--color-text-muted); font-size: var(--font-size-xs); }
.danger-note { display: flex; gap: var(--space-3); padding: var(--space-4); border: 1px solid rgba(240,108,117,.18); border-radius: var(--radius-lg); background: var(--color-danger-soft); color: var(--color-danger); }
.danger-note > span { display: grid; }
.danger-note strong { color: var(--color-text-primary); font-size: var(--font-size-sm); }
.danger-note small { color: var(--color-text-secondary); font-size: var(--font-size-xs); }
.security-title { display: flex; align-items: center; gap: var(--space-3); }
.security-title :deep(svg) { color: var(--color-success); }
.security-title h3 { margin: 0; font-size: var(--font-size-md); }
.security-title p { margin: .1rem 0 0; color: var(--color-text-muted); font-size: var(--font-size-xs); }
.withdraw-aside .app-card > a { display: inline-flex; align-items: center; gap: .2rem; margin-top: var(--space-5); color: var(--color-primary); font-size: var(--font-size-xs); font-weight: 600; }
.form-error { display: flex; align-items: center; gap: var(--space-2); padding: var(--space-3); border: 1px solid rgba(240,108,117,.2); border-radius: var(--radius-md); background: var(--color-danger-soft); color: var(--color-danger); }
.history-card { margin-top: var(--space-5); overflow: hidden; }
.card-heading { display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); padding: var(--space-5); border-block-end: 1px solid var(--color-border-soft); }
.card-heading h2 { margin: 0; font-size: var(--font-size-lg); }
.card-heading p { margin: .1rem 0 0; color: var(--color-text-muted); font-size: var(--font-size-xs); }
.card-heading a { display: inline-flex; align-items: center; color: var(--color-primary); font-size: var(--font-size-xs); font-weight: 600; }
.review { display: grid; gap: var(--space-5); }
.review-total { display: grid; justify-items: center; padding: var(--space-5); border-radius: var(--radius-lg); background: var(--color-success-soft); }
.review-total span { color: var(--color-text-muted); font-size: var(--font-size-xs); }
.review-total strong { margin-top: .2rem; color: var(--color-success); font-size: var(--font-size-xl); }
.review dl, .success-card dl { display: grid; gap: var(--space-3); margin: 0; }
.review dl div, .success-card dl div { display: flex; justify-content: space-between; gap: var(--space-4); padding-bottom: var(--space-3); border-block-end: 1px solid var(--color-border-soft); }
.review dt, .success-card dt { color: var(--color-text-muted); }
.review dd, .success-card dd { margin: 0; font-weight: 600; text-align: end; }
.review-address, .success-address { display: grid; gap: var(--space-1); min-width: 0; padding: var(--space-3); border-radius: var(--radius-md); background: var(--color-surface-2); text-align: start; }
.review-address span, .success-address span { color: var(--color-text-muted); font-size: var(--font-size-xs); }
.review-address bdi, .success-address bdi { overflow-wrap: anywhere; color: var(--color-text-secondary); font-family: ui-monospace, monospace; font-size: var(--font-size-xs); }
.review-address small { color: var(--color-warning); }
.review-warning, .demo-hint { display: flex; align-items: center; gap: var(--space-2); padding: var(--space-3); border-radius: var(--radius-md); background: var(--color-danger-soft); color: var(--color-danger); font-size: var(--font-size-xs); }
.rate-limit-message { margin: 0; color: var(--color-warning); font-size: var(--font-size-xs); text-align: center; }
.security-step { display: grid; gap: var(--space-4); justify-items: stretch; }
.phone-mark { display: grid; width: 3.5rem; height: 3.5rem; margin-inline: auto; border-radius: 1rem; background: var(--color-primary-soft); color: var(--color-primary); place-items: center; }
.security-step > p { margin: 0; color: var(--color-text-muted); text-align: center; }
.security-step .demo-hint { justify-content: center; background: var(--color-info-soft); color: var(--color-info); }
.security-step .security-message { color: var(--color-success); font-size: var(--font-size-xs); }
.challenge-expiry { font-size: var(--font-size-xs); }
.security-step .challenge-expiry.expired { color: var(--color-danger); }
.success-wrap, .state-card { width: min(100%, 42rem); margin-inline: auto; }
.success-card { display: grid; justify-items: center; text-align: center; }
.success-icon { display: grid; width: 4.5rem; height: 4.5rem; border-radius: 1.35rem; background: var(--color-success-soft); color: var(--color-success); place-items: center; }
.eyebrow { margin-top: var(--space-4); color: var(--color-success); font-weight: 600; }
.success-card h2 { margin: var(--space-1) 0; font-size: var(--font-size-2xl); }
.success-card > p { max-width: 31rem; margin: 0 0 var(--space-3); color: var(--color-text-muted); }
.success-card dl, .success-address { width: 100%; margin-top: var(--space-6); text-align: start; }
.success-actions { display: grid; width: 100%; gap: var(--space-2); margin-top: var(--space-6); }
@media (max-width: 920px) { .withdraw-layout, .withdraw-skeleton { grid-template-columns: 1fr; } .withdraw-aside { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 767px) {
  .withdraw-aside { grid-template-columns: 1fr; }
  .card-heading { padding: var(--space-4); }
  .card-heading p { display: none; }
}
</style>
