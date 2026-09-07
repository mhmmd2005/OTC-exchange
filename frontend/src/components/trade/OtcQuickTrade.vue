<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import type { ComponentPublicInstance } from 'vue'
import { useRouter } from 'vue-router'
import type { MarketAsset, OtcOrder, TradeQuote, TradeSide, WalletSummary } from '@/types'
import { ApiError } from '@/services/api'
import { tradeService } from '@/services/trade.service'
import { useNotificationsStore } from '@/stores/notifications'
import { useWalletStore } from '@/stores/wallet'
import { addDecimal, calculatePercentageAmount, calculateQuoteTotal, compareDecimal, subtractDecimal } from '@/utils/financial'
import { formatCrypto, formatToman, toPersianDigits } from '@/utils/formatters'
import AppAmountInput from '@/components/ui/AppAmountInput.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import AppModal from '@/components/ui/AppModal.vue'
import AppTabs from '@/components/ui/AppTabs.vue'
import AssetAvatar from '@/components/finance/AssetAvatar.vue'
import AssetSelect from '@/components/finance/AssetSelect.vue'

const props = withDefaults(defineProps<{
  assets: MarketAsset[]
  wallet: WalletSummary
  initialSide?: TradeSide
  initialAsset?: string
  compact?: boolean
}>(), { initialSide: 'buy', compact: false })

const router = useRouter()
const walletStore = useWalletStore()
const notificationsStore = useNotificationsStore()
const side = ref<TradeSide>(props.initialSide)
const symbol = ref(props.initialAsset || 'USDT')
const inputSide = ref<'toman' | 'crypto'>(props.initialSide === 'sell' ? 'crypto' : 'toman')
const tomanAmount = ref(props.initialSide === 'sell' ? '' : '50000000')
const cryptoAmount = ref(props.initialSide === 'sell' ? '100' : '')
const calculating = ref(false)
const seconds = ref(27)
const quoteDurationSeconds = ref(27)
const reviewOpen = ref(false)
const reviewQuote = ref<TradeQuote | null>(null)
const reviewSeconds = ref(0)
const reviewExpired = ref(false)
const submitting = ref(false)
const successOpen = ref(false)
const orderNumber = ref('')
const priceUpdated = ref(false)
const quote = ref<TradeQuote | null>(null)
const quoteError = ref('')
const quoteAction = ref<{ label: string; to: string } | null>(null)
const completedOrder = ref<OtcOrder | null>(null)
const priceChange = ref<{ previous: string; current: string } | null>(null)
const orderRequestId = ref('')
const confirmReviewButton = ref<ComponentPublicInstance | null>(null)
const refreshReviewButton = ref<ComponentPublicInstance | null>(null)
let calculationTimer: number | undefined
let quoteTimer: number | undefined
let reviewTimer: number | undefined
let requestVersion = 0
let quoteController: AbortController | undefined
let reopenReviewAfterRefresh: boolean = false
let preserveReviewError = false

const tradableAssets = computed(() => props.assets.filter((asset) => asset.tradable))
const assetBalances = computed<Record<string, string | undefined>>(() => Object.fromEntries(
  props.wallet.assets.map((item) => [item.symbol, item.available]),
))
const asset = computed(() => tradableAssets.value.find((item) => item.symbol === symbol.value) || tradableAssets.value[0])
const walletAsset = computed(() => props.wallet.assets.find((item) => item.symbol === symbol.value))
const rate = computed(() => quote.value?.rateToman || (side.value === 'buy' ? asset.value?.buyPriceToman || '0' : asset.value?.sellPriceToman || '0'))
const feeBase = computed(() => quote.value?.tomanAmount || calculateQuoteTotal(cryptoAmount.value || '0', rate.value, 0))
const orderLimitBase = computed(() => inputSide.value === 'toman' ? (tomanAmount.value || '0') : feeBase.value)
const fee = computed(() => quote.value?.feeToman || calculatePercentageAmount(feeBase.value, '0.15', 0))
const finalToman = computed(() => quote.value?.finalTomanAmount || (side.value === 'buy' ? addDecimal(feeBase.value, fee.value) : subtractDecimal(feeBase.value, fee.value)))
const quoteProgress = computed(() => Math.max(0, Math.min(100, (seconds.value / quoteDurationSeconds.value) * 100)))
const quoteNearExpiry = computed(() => Boolean(quote.value) && seconds.value <= 7)
const ctaLabel = computed(() => `${side.value === 'buy' ? 'ادامه خرید' : 'ادامه فروش'} ${asset.value?.nameFa || ''}`.trim())

const validationError = computed(() => {
  if (quoteError.value) return quoteError.value
  if (!asset.value) return 'ارز انتخاب‌شده در حال حاضر در دسترس نیست.'
  if (!tomanAmount.value || !cryptoAmount.value) return ''
  if (compareDecimal(orderLimitBase.value, '1000000') < 0) return 'حداقل مبلغ سفارش ۱,۰۰۰,۰۰۰ تومان است.'
  if (compareDecimal(orderLimitBase.value, '500000000') > 0) return 'حداکثر مبلغ هر سفارش ۵۰۰,۰۰۰,۰۰۰ تومان است.'
  if (side.value === 'buy' && compareDecimal(finalToman.value, props.wallet.availableToman) > 0) return 'موجودی تومان برای این خرید کافی نیست.'
  if (side.value === 'sell' && compareDecimal(cryptoAmount.value, walletAsset.value?.available || '0') > 0) return `موجودی ${asset.value.nameFa} برای این فروش کافی نیست.`
  return ''
})

const refreshTimer = (nextQuote: TradeQuote) => {
  const totalDuration = Math.max(1, Math.ceil((Date.parse(nextQuote.expiresAt) - Date.parse(nextQuote.createdAt)) / 1000))
  quoteDurationSeconds.value = totalDuration
  seconds.value = Math.max(0, Math.ceil((Date.parse(nextQuote.expiresAt) - Date.now()) / 1000))
  window.clearInterval(quoteTimer)
  quoteTimer = window.setInterval(() => {
    seconds.value -= 1
    if (seconds.value <= 0) {
      window.clearInterval(quoteTimer)
      priceUpdated.value = true
      calculate()
      window.setTimeout(() => { priceUpdated.value = false }, 2500)
    }
  }, 1000)
}

const calculate = () => {
  window.clearTimeout(calculationTimer)
  window.clearInterval(quoteTimer)
  quoteController?.abort()
  const version = ++requestVersion
  quote.value = null
  quoteError.value = ''
  quoteAction.value = null
  const amount = inputSide.value === 'toman' ? tomanAmount.value : cryptoAmount.value
  if (!amount || amount === '0' || !asset.value) {
    reopenReviewAfterRefresh = false
    calculating.value = false
    return
  }
  calculating.value = true
  calculationTimer = window.setTimeout(() => { void (async () => {
    quoteController = new AbortController()
    try {
      const nextQuote = await tradeService.getQuote({
        side: side.value,
        assetSymbol: symbol.value,
        inputSide: inputSide.value,
        amount,
      }, quoteController.signal)
      if (version !== requestVersion) return
      quote.value = nextQuote
      // Never mutate the side the customer is actively typing. The other side
      // is the calculated output; the immutable review uses canonical totals.
      if (inputSide.value === 'toman') cryptoAmount.value = nextQuote.cryptoAmount
      else tomanAmount.value = nextQuote.tomanAmount
      refreshTimer(nextQuote)
      if (reopenReviewAfterRefresh) {
        reopenReviewAfterRefresh = false
        openReview()
      }
    } catch (error) {
      if (error instanceof DOMException && error.name === 'AbortError') return
      if (version !== requestVersion) return
      reopenReviewAfterRefresh = false
      quoteError.value = error instanceof Error ? error.message : 'دریافت نرخ ممکن نشد. دوباره تلاش کنید.'
      if (error instanceof ApiError && error.details?.actionLabel && error.details.actionRoute) {
        quoteAction.value = { label: error.details.actionLabel, to: error.details.actionRoute }
      }
    } finally {
      if (version === requestVersion) calculating.value = false
    }
  })() }, 360)
}

watch([tomanAmount, cryptoAmount, symbol], (next, previous) => {
  if (next[0] !== previous?.[0] && inputSide.value === 'toman') calculate()
  else if (next[1] !== previous?.[1] && inputSide.value === 'crypto') calculate()
  else if (next[2] !== previous?.[2]) calculate()
}, { immediate: true })

watch(side, (value) => {
  inputSide.value = value === 'buy' ? 'toman' : 'crypto'
  if (value === 'sell' && !cryptoAmount.value) cryptoAmount.value = '100'
  calculate()
})

const updateToman = (value: string) => { inputSide.value = 'toman'; tomanAmount.value = value }
const updateCrypto = (value: string) => { inputSide.value = 'crypto'; cryptoAmount.value = value }
const setTomanPreset = (value: string) => {
  inputSide.value = 'toman'
  tomanAmount.value = value
}
const setPercentage = (percent: string) => {
  inputSide.value = 'crypto'
  cryptoAmount.value = calculatePercentageAmount(walletAsset.value?.available || '0', percent, asset.value?.amountPrecision ?? 8)
}
const swapFocus = () => {
  inputSide.value = inputSide.value === 'toman' ? 'crypto' : 'toman'
  calculate()
}

watch(tradableAssets, (items) => {
  if (items.length && !items.some((item) => item.symbol === symbol.value)) symbol.value = items[0]!.symbol
}, { immediate: true })

const expireReview = () => {
  const confirmControl = confirmReviewButton.value?.$el
  const confirmHadFocus = confirmControl instanceof HTMLElement && document.activeElement === confirmControl
  reviewExpired.value = true
  window.clearInterval(reviewTimer)
  if (!confirmHadFocus) return
  void nextTick(() => {
    const refreshControl = refreshReviewButton.value?.$el
    if (refreshControl instanceof HTMLButtonElement && !refreshControl.disabled) {
      refreshControl.focus({ preventScroll: true })
    }
  })
}

const openReview = () => {
  if (!quote.value || validationError.value || cryptoAmount.value === '0') return
  window.clearInterval(quoteTimer)
  window.clearInterval(reviewTimer)
  reviewQuote.value = { ...quote.value }
  orderRequestId.value = globalThis.crypto.randomUUID()
  reviewSeconds.value = Math.max(0, Math.ceil((Date.parse(quote.value.expiresAt) - Date.now()) / 1000))
  reviewExpired.value = reviewSeconds.value <= 0
  reviewOpen.value = true
  if (!reviewExpired.value) {
    reviewTimer = window.setInterval(() => {
      reviewSeconds.value = Math.max(0, reviewSeconds.value - 1)
      if (reviewSeconds.value === 0) {
        expireReview()
      }
    }, 1000)
  }
}
const refreshReview = () => {
  reopenReviewAfterRefresh = true
  reviewOpen.value = false
}
const exitPriceChange = (reopenReview = false) => {
  // PRICE_CHANGED closes the immutable review while its quote timer is paused.
  // Every modal exit must therefore discard that quote and request a fresh one;
  // otherwise edit/dismiss paths could leave a stale, untimed quote actionable.
  if (!priceChange.value) return
  priceChange.value = null
  reopenReviewAfterRefresh = reopenReview
  calculate()
}
const handlePriceChangeVisibility = (open: boolean) => {
  if (!open) exitPriceChange()
}
const confirm = async () => {
  if (submitting.value) return
  const acceptedQuote = reviewQuote.value
  if (!acceptedQuote || reviewExpired.value) return
  submitting.value = true
  try {
    const order = await tradeService.createOrder({
      quoteId: acceptedQuote.id,
      acceptedRateToman: acceptedQuote.rateToman,
      clientRequestId: orderRequestId.value,
    })
    completedOrder.value = order
    orderNumber.value = order.orderNumber
    await Promise.allSettled([walletStore.refresh(), notificationsStore.fetchNotifications()])
    reviewOpen.value = false
    successOpen.value = true
  } catch (error) {
    if (error instanceof ApiError && error.code === 'PRICE_CHANGED') {
      quote.value = null
      priceChange.value = {
        previous: String(error.details?.previousRate || acceptedQuote.rateToman),
        current: String(error.details?.currentRate || acceptedQuote.rateToman),
      }
      reviewOpen.value = false
    } else if (error instanceof ApiError && error.code === 'QUOTE_EXPIRED') {
      expireReview()
      quoteError.value = 'مهلت این نرخ تمام شد. نرخ تازه را دریافت و دوباره بررسی کنید.'
    } else {
      quote.value = null
      quoteError.value = error instanceof Error ? error.message : 'ثبت سفارش انجام نشد. دوباره تلاش کنید.'
      preserveReviewError = true
      reviewOpen.value = false
    }
  } finally {
    submitting.value = false
  }
}

watch(reviewOpen, (open) => {
  if (open) return
  window.clearInterval(reviewTimer)
  const hadReview = Boolean(reviewQuote.value)
  reviewQuote.value = null
  if (preserveReviewError) {
    preserveReviewError = false
    return
  }
  if (hadReview && !submitting.value && !successOpen.value && !priceChange.value) calculate()
})

onBeforeUnmount(() => { window.clearInterval(quoteTimer); window.clearInterval(reviewTimer); window.clearTimeout(calculationTimer); quoteController?.abort() })
</script>

<template>
  <AppCard class="trade-card" :class="{ compact, 'is-buy': side === 'buy', 'is-sell': side === 'sell' }" padding="lg">
    <header class="trade-header">
      <div><span class="eyebrow"><i /> معامله مستقیم با روشا</span><h2>{{ compact ? 'خرید و فروش سریع' : 'خرید و فروش' }}</h2><p>ارز و مبلغ را انتخاب کنید؛ نرخ نهایی پیش از ثبت تأیید می‌شود.</p></div>
      <span class="secure desktop-only"><AppIcon name="shield" :size="16" /> نرخ شفاف و امن</span>
    </header>

    <AppTabs v-model="side" :items="[{ label: 'خرید', value: 'buy' }, { label: 'فروش', value: 'sell' }]" />

    <div class="asset-select-wrap">
      <AssetSelect v-model="symbol" :assets="tradableAssets" :balances="assetBalances" label="ارز مورد نظر" show-balance />
    </div>

    <div class="converter">
      <section class="converter__field">
        <AppAmountInput
          :model-value="tomanAmount"
          :label="side === 'buy' ? 'پرداخت می‌کنم' : 'دریافت می‌کنم'"
          suffix="تومان"
          type="toman"
          :balance="side === 'buy' ? wallet.availableToman : undefined"
          balance-label="موجودی قابل استفاده"
          :disabled="calculating && inputSide === 'crypto'"
          @update:model-value="updateToman"
        />
      </section>
      <div class="converter__swap-row">
        <span aria-hidden="true" />
        <button type="button" class="swap" aria-label="تغییر سمت ورودی مبلغ" @click="swapFocus"><AppIcon name="swapVertical" :size="20" /></button>
        <span aria-hidden="true" />
      </div>
      <section class="converter__field">
        <AppAmountInput
          :model-value="cryptoAmount"
          :label="side === 'buy' ? 'دریافت می‌کنم' : 'می‌فروشم'"
          :suffix="symbol"
          type="crypto"
          :max-fraction-digits="asset?.amountPrecision ?? 8"
          :balance="side === 'sell' ? walletAsset?.available : undefined"
          balance-label="موجودی قابل فروش"
          :disabled="calculating && inputSide === 'toman'"
          @update:model-value="updateCrypto"
        />
      </section>
    </div>

    <div v-if="side === 'buy'" class="quick-values">
      <span>مبالغ پرکاربرد</span>
      <div class="preset-buttons">
        <button v-for="item in [{ l: '۱۰ میلیون', v: '10000000' }, { l: '۲۵ میلیون', v: '25000000' }, { l: '۵۰ میلیون', v: '50000000' }, { l: '۱۰۰ میلیون', v: '100000000' }]" :key="item.v" type="button" :class="{ active: tomanAmount === item.v && inputSide === 'toman' }" @click="setTomanPreset(item.v)">{{ item.l }}</button>
      </div>
    </div>
    <div v-else class="quick-values">
      <span>انتخاب از موجودی</span>
      <div class="preset-buttons">
        <button v-for="item in [{ l: '۲۵٪', v: '25' }, { l: '۵۰٪', v: '50' }, { l: '۷۵٪', v: '75' }, { l: 'همه', v: '100' }]" :key="item.v" type="button" @click="setPercentage(item.v)">{{ item.l }}</button>
      </div>
    </div>

    <Transition name="notice"><div v-if="priceUpdated" class="quote-notice"><AppIcon name="refresh" :size="17" /> نرخ معامله به‌روزرسانی شد.</div></Transition>
    <div v-if="validationError" class="trade-error" role="alert">
      <AppIcon name="warning" :size="19" /><span>{{ validationError }}</span>
      <RouterLink v-if="quoteAction" :to="quoteAction.to">{{ quoteAction.label }}</RouterLink>
      <RouterLink v-else-if="side === 'buy' && validationError.includes('موجودی')" to="/app/deposit/toman">واریز تومان</RouterLink>
      <button v-else-if="quoteError && !calculating" type="button" @click="calculate">دریافت دوباره نرخ</button>
    </div>

    <dl class="quote-summary" aria-live="polite">
      <div><dt>نرخ لحظه‌ای</dt><dd>هر ۱ {{ asset?.nameFa }} = {{ formatToman(rate) }}</dd></div>
      <div><dt>کارمزد معامله <span>۰٫۱۵٪</span></dt><dd>{{ formatToman(fee) }}</dd></div>
      <div class="total"><dt>{{ side === 'buy' ? 'مبلغ نهایی پرداخت' : 'مبلغ نهایی دریافت' }}</dt><dd>{{ formatToman(finalToman) }}</dd></div>
    </dl>

    <div class="quote-life" :class="{ warning: quoteNearExpiry }">
      <span v-if="quote"><AppIcon name="clock" :size="16" /> اعتبار نرخ: {{ toPersianDigits(seconds) }} ثانیه</span>
      <span v-else><AppIcon name="refresh" :size="16" /> {{ calculating ? 'در حال دریافت نرخ…' : 'برای مشاهده نرخ، مبلغ را وارد کنید' }}</span>
      <span class="life-track"><i :style="{ width: `${quote ? quoteProgress : 0}%` }" /></span>
    </div>

    <div class="trade-submit">
      <AppButton size="lg" block :disabled="!!validationError || !cryptoAmount || calculating || !quote" :loading="calculating" @click="openReview">
        {{ ctaLabel }}
      </AppButton>
      <small><AppIcon name="shield" :size="15" /> مبلغ سفارش فقط پس از تأیید شما ثبت می‌شود</small>
    </div>

    <AppModal v-model="reviewOpen" :title="`${side === 'buy' ? 'تأیید خرید' : 'تأیید فروش'} ${asset?.nameFa}`" description="پیش از تأیید، جزئیات معامله را یک‌بار بررسی کنید.">
      <div v-if="reviewQuote" class="review-hero" :class="reviewQuote.side"><AssetAvatar v-if="asset" :symbol="asset.symbol" :color="asset.color" size="lg" /><div><span>{{ side === 'buy' ? 'دریافت می‌کنید' : 'می‌فروشید' }}</span><strong><bdi dir="ltr">{{ formatCrypto(reviewQuote.cryptoAmount, { symbol: reviewQuote.assetSymbol }) }}</bdi></strong><small>{{ side === 'buy' ? 'خرید مستقیم از روشا' : 'فروش مستقیم به روشا' }}</small></div></div>
      <dl v-if="reviewQuote" class="review-list">
        <div><dt>نوع عملیات</dt><dd>{{ reviewQuote.side === 'buy' ? 'خرید از روشا' : 'فروش به روشا' }}</dd></div>
        <div><dt>نرخ</dt><dd>{{ formatToman(reviewQuote.rateToman) }}</dd></div>
        <div><dt>کارمزد</dt><dd>{{ formatToman(reviewQuote.feeToman) }}</dd></div>
        <div><dt>{{ reviewQuote.side === 'buy' ? 'پرداخت از' : 'واریز به' }}</dt><dd>کیف پول تومان</dd></div>
        <div class="review-total"><dt>{{ reviewQuote.side === 'buy' ? 'مبلغ قابل پرداخت' : 'مبلغ قابل دریافت' }}</dt><dd>{{ formatToman(reviewQuote.finalTomanAmount) }}</dd></div>
      </dl>
      <div class="review-note" :class="{ expired: reviewExpired }">
        <span class="sr-only" role="status" aria-atomic="true">{{ reviewExpired ? 'مهلت این نرخ تمام شده است؛ پیش از ادامه نرخ تازه را بررسی کنید.' : '' }}</span>
        <AppIcon :name="reviewExpired ? 'warning' : 'clock'" :size="18" />
        {{ reviewExpired ? 'مهلت این نرخ تمام شده است؛ پیش از ادامه نرخ تازه را بررسی کنید.' : `این نرخ ${toPersianDigits(reviewSeconds)} ثانیه دیگر معتبر است.` }}
      </div>
      <template #footer><AppButton v-if="reviewExpired" ref="refreshReviewButton" size="lg" block icon="refresh" @click="refreshReview">دریافت و بررسی نرخ تازه</AppButton><AppButton v-else ref="confirmReviewButton" size="lg" block :loading="submitting" @click="confirm">تأیید و {{ side === 'buy' ? 'خرید' : 'فروش' }}</AppButton><AppButton variant="secondary" size="lg" :disabled="submitting" @click="reviewOpen = false">ویرایش</AppButton></template>
    </AppModal>

    <AppModal v-model="successOpen" title="سفارش شما ثبت شد" :dismissible="false" size="sm">
      <div class="success-state"><span class="success-icon"><AppIcon name="check" :size="34" /></span><h3>{{ side === 'buy' ? 'خرید' : 'فروش' }} {{ asset?.nameFa }} با موفقیت ثبت شد</h3><p>پردازش سفارش معمولاً کمتر از یک دقیقه زمان می‌برد.</p><span class="order-no"><small>شماره سفارش</small><bdi>{{ orderNumber }}</bdi></span></div>
      <template #footer><AppButton block @click="successOpen = false; router.push(completedOrder ? `/app/orders/${completedOrder.id}` : '/app/orders')">مشاهده سفارش</AppButton><AppButton variant="secondary" @click="successOpen = false; router.push('/app/dashboard')">داشبورد</AppButton></template>
    </AppModal>

    <AppModal :model-value="!!priceChange" title="قیمت به‌روزرسانی شد" description="برای محافظت از شما، مبلغ سفارش بی‌اجازه تغییر نکرده است." size="sm" @update:model-value="handlePriceChangeVisibility">
      <dl v-if="priceChange" class="price-change"><div><dt>نرخ قبلی</dt><dd>{{ formatToman(priceChange.previous) }}</dd></div><div><dt>نرخ جدید</dt><dd>{{ formatToman(priceChange.current) }}</dd></div></dl>
      <template #footer><AppButton block @click="exitPriceChange(true)">دریافت و بررسی نرخ جدید</AppButton><AppButton variant="secondary" @click="exitPriceChange()">ویرایش مبلغ</AppButton></template>
    </AppModal>
  </AppCard>
</template>

<style scoped>
.trade-card { position: relative; min-width: 0; border-color: color-mix(in srgb, var(--color-primary), var(--color-border) 70%); box-shadow: 0 18px 48px rgba(0, 7, 17, .16); }
.trade-header { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-4); margin-bottom: var(--space-5); }
.trade-header h2 { margin: .2rem 0 .15rem; font-size: var(--font-size-2xl); letter-spacing: -.02em; }
.trade-header p { max-width: 31rem; margin: 0; color: var(--color-text-muted); font-size: var(--font-size-sm); }
.eyebrow, .secure { display: inline-flex; align-items: center; gap: var(--space-2); color: var(--color-success); font-size: var(--font-size-xs); font-weight: 600; }
.eyebrow i { width: .42rem; height: .42rem; border-radius: 50%; background: var(--color-success); box-shadow: 0 0 0 4px var(--color-success-soft); }
.secure { padding: .4rem .7rem; border: 1px solid color-mix(in srgb, var(--color-success), transparent 80%); border-radius: var(--radius-pill); background: var(--color-success-soft); }
.trade-card :deep(.tabs) { padding: .32rem; border-radius: var(--radius-lg); }
.trade-card :deep(.tabs button) { min-height: 2.85rem; }
.is-buy :deep(.tabs button.active) { background: linear-gradient(135deg, var(--action-primary-hover), var(--action-primary-active)); box-shadow: 0 8px 20px color-mix(in srgb, var(--action-primary), transparent 75%); color: var(--on-primary); }
.is-sell :deep(.tabs button.active) { background: linear-gradient(135deg, var(--color-success-hover), var(--color-success)); box-shadow: 0 8px 20px color-mix(in srgb, var(--color-success), transparent 77%); color: var(--on-success); }
.asset-select-wrap { position: relative; margin-top: var(--space-5); }
.asset-select-wrap :deep(.select-field__control) { min-height: 3.65rem; border-radius: var(--radius-lg); background: var(--color-surface-2); }
.converter { display: grid; min-width: 0; margin-top: var(--space-5); }
.converter__field { min-width: 0; }
.converter :deep(.amount-field__control) { min-height: 4.65rem; border-radius: var(--radius-lg); background: color-mix(in srgb, var(--color-surface-2), var(--color-bg-app) 14%); }
.converter :deep(.amount-field__control:focus-within) { background: var(--color-surface-1); }
.converter :deep(input) { font-size: clamp(1.35rem, 3vw, 1.75rem); }
.converter__swap-row { display: grid; min-height: 3.5rem; grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr); align-items: center; gap: var(--space-3); }
.converter__swap-row > span { height: 1px; background: var(--color-border-soft); }
.swap { display: grid; width: 2.85rem; height: 2.85rem; border: 1px solid var(--color-border-strong); border-radius: .92rem; background: var(--color-surface-3); color: var(--color-primary); box-shadow: var(--shadow-xs); transition: border-color var(--transition-fast), background var(--transition-fast), color var(--transition-fast), transform var(--transition-fast); place-items: center; }
.swap:hover { border-color: var(--color-primary-border); background: var(--color-primary-soft); transform: scale(1.03); }
.swap:focus-visible { outline: 2px solid var(--color-border-focus); outline-offset: 2px; box-shadow: var(--shadow-focus); }
.is-sell .swap { color: var(--color-success); }
.quick-values { display: grid; gap: var(--space-2); margin-top: var(--space-3); }
.quick-values > span { color: var(--color-text-muted); font-size: var(--font-size-xs); }
.preset-buttons { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: var(--space-2); }
.preset-buttons button { min-width: 0; min-height: 2.45rem; padding-inline: var(--space-2); overflow: hidden; border: 1px solid var(--color-border); border-radius: var(--radius-sm); background: var(--color-surface-2); color: var(--color-text-secondary); font-size: var(--font-size-xs); text-overflow: ellipsis; white-space: nowrap; transition: border-color var(--transition-fast), background var(--transition-fast), color var(--transition-fast); }
.preset-buttons button:hover, .preset-buttons button.active { border-color: color-mix(in srgb, var(--color-primary), var(--color-border) 40%); background: var(--color-primary-soft); color: var(--color-primary); }
.is-sell .preset-buttons button:hover { border-color: color-mix(in srgb, var(--color-success), var(--color-border) 40%); background: var(--color-success-soft); color: var(--color-success); }
.quote-summary { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0; margin: var(--space-5) 0 0; overflow: hidden; border: 1px solid var(--color-border-soft); border-radius: var(--radius-lg); background: color-mix(in srgb, var(--color-surface-2), var(--color-bg-app) 18%); }
.quote-summary > div { display: grid; align-content: start; gap: .25rem; min-width: 0; padding: var(--space-3) var(--space-4); }
.quote-summary > div:nth-child(2) { border-inline-start: 1px solid var(--color-border-soft); }
.quote-summary > div.total { grid-column: 1 / -1; display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); padding: var(--space-4); border-block-start: 1px solid var(--color-border-soft); background: color-mix(in srgb, var(--color-surface-3), transparent 30%); }
.quote-summary dt, .review-list dt { color: var(--color-text-muted); }
.quote-summary dd, .review-list dd { min-width: 0; margin: 0; font-weight: 500; text-align: start; }
.quote-summary dd { overflow-wrap: anywhere; }
.quote-summary dt span { padding: .12rem .4rem; border-radius: var(--radius-pill); background: var(--color-gold-soft); color: var(--color-gold); font-size: .65rem; }
.quote-summary .total dd { color: var(--color-text-primary); font-size: var(--font-size-lg); font-weight: 700; text-align: end; }
.is-sell .quote-summary .total dd { color: var(--color-success); }
.quote-life { display: flex; align-items: center; gap: var(--space-3); margin: var(--space-3) 0 var(--space-4); color: var(--color-text-muted); font-size: var(--font-size-xs); transition: color var(--transition-fast); }
.quote-life.warning { color: var(--color-warning); }
.quote-life > span:first-child { display: inline-flex; min-width: 11.3rem; align-items: center; gap: var(--space-1); white-space: nowrap; }
.life-track { width: 100%; height: .2rem; overflow: hidden; border-radius: var(--radius-pill); background: var(--color-surface-3); direction: ltr; }
.life-track i { display: block; height: 100%; border-radius: inherit; background: var(--color-primary); transition: width 1s linear, background var(--transition-fast); }
.is-sell .life-track i { background: var(--color-success); }
.quote-life.warning .life-track i { background: var(--color-warning); }
.trade-submit { display: grid; gap: var(--space-2); }
.trade-submit > small { display: flex; align-items: center; justify-content: center; gap: var(--space-1); color: var(--color-text-muted); font-size: .68rem; text-align: center; }
.trade-submit :deep(.app-button) { min-height: 3.75rem; }
.is-sell .trade-submit :deep(.app-button--primary) { background: var(--color-success); box-shadow: 0 8px 22px color-mix(in srgb, var(--color-success), transparent 78%); color: var(--on-success); }
.is-sell .trade-submit :deep(.app-button--primary:hover:not(:disabled)) { background: var(--color-success-hover); }
.quote-notice, .trade-error { display: flex; align-items: center; gap: var(--space-2); margin-top: var(--space-4); padding: var(--space-3); border-radius: var(--radius-md); font-size: var(--font-size-xs); }
.quote-notice { background: var(--color-info-soft); color: var(--color-info); }
.trade-error { border: 1px solid rgba(240,108,117,.16); background: var(--color-danger-soft); color: var(--color-danger); }
.trade-error span { flex: 1; }
.trade-error a,.trade-error button { flex: 0 0 auto; border: 0; background: transparent; color: inherit; font-weight: 700; text-decoration: underline; }
.notice-enter-active, .notice-leave-active { transition: opacity var(--transition-fast), transform var(--transition-fast); }
.notice-enter-from, .notice-leave-to { opacity: 0; transform: translateY(-.25rem); }
.review-hero { display: flex; align-items: center; gap: var(--space-4); padding: var(--space-4); border: 1px solid color-mix(in srgb, var(--color-primary), transparent 82%); border-radius: var(--radius-lg); background: var(--color-primary-soft); }
.review-hero.sell { border-color: color-mix(in srgb, var(--color-success), transparent 82%); background: var(--color-success-soft); }
.review-hero div { display: grid; }
.review-hero span, .review-hero small { color: var(--color-text-muted); font-size: var(--font-size-xs); }
.review-hero strong { margin: .1rem 0; font-size: var(--font-size-xl); }
.review-list { display: grid; gap: var(--space-3); margin: var(--space-5) 0; }
.review-list > div { display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); padding-bottom: var(--space-3); border-block-end: 1px solid var(--color-border-soft); }
.review-list .review-total { padding: var(--space-4); border: 0; border-radius: var(--radius-md); background: var(--color-surface-2); }
.review-total dd { color: var(--color-primary); font-size: var(--font-size-lg); font-weight: 700; }
.review-note { display: flex; gap: var(--space-2); padding: var(--space-3); border-radius: var(--radius-md); background: var(--color-info-soft); color: var(--color-info); font-size: var(--font-size-xs); }
.review-note.expired { background: var(--color-warning-soft); color: var(--color-warning); }
.success-state { display: grid; justify-items: center; text-align: center; }
.success-icon { display: grid; width: 5rem; height: 5rem; margin-bottom: var(--space-4); border: 1px solid rgba(53,201,149,.25); border-radius: 50%; background: var(--color-success-soft); color: var(--color-success); place-items: center; }
.success-state h3 { margin-bottom: var(--space-2); }
.success-state p { color: var(--color-text-muted); }
.order-no { display: grid; width: 100%; padding: var(--space-3); border: 1px dashed var(--color-border-hover); border-radius: var(--radius-md); background: var(--color-surface-2); }
.order-no small { color: var(--color-text-muted); }
.order-no bdi { margin-top: .2rem; font-weight: 700; direction: ltr; }
.price-change { display: grid; gap: var(--space-3); margin: 0; }
.price-change div { display: flex; justify-content: space-between; gap: var(--space-3); padding: var(--space-3); border-radius: var(--radius-md); background: var(--color-surface-2); }
.price-change dt { color: var(--color-text-muted); }
.price-change dd { margin: 0; font-weight: 700; }
.price-change div:last-child dd { color: var(--color-primary); }
.compact .trade-header { margin-bottom: var(--space-4); }
.compact .trade-header h2 { font-size: var(--font-size-xl); }
.compact .trade-header p { display: none; }
.compact :deep(.tabs button) { min-height: 2.6rem; }
.compact .asset-select-wrap,
.compact .converter { margin-top: var(--space-4); }
.compact .asset-select-wrap :deep(.select-field__control) { min-height: 3.35rem; }
.compact .converter :deep(.amount-field__control) { min-height: 4.1rem; }
.compact .converter__swap-row { min-height: 3rem; }
.compact .quick-values { margin-top: var(--space-2); }
.compact .quote-summary { margin-top: var(--space-4); }
.compact .quote-life { margin-block: var(--space-2) var(--space-3); }
.compact .trade-submit :deep(.app-button) { min-height: 3.35rem; }

@media (max-width: 767px) {
  .trade-card { box-shadow: none; }
  .trade-header { margin-bottom: var(--space-4); }
  .trade-header h2 { font-size: var(--font-size-xl); }
  .trade-header p { max-width: 18rem; font-size: var(--font-size-xs); }
  .trade-card :deep(.tabs button) { min-height: 2.7rem; }
  .asset-select-wrap { margin-top: var(--space-4); }
  .converter { margin-top: var(--space-4); }
  .converter :deep(.amount-field__control) { min-height: 4.4rem; }
  .converter__swap-row { min-height: 3.35rem; gap: var(--space-2); }
  .swap { width: 2.75rem; height: 2.75rem; }
  .quick-values > span { display: none; }
  .preset-buttons button { min-height: 2.5rem; font-size: .7rem; }
  .quote-summary { margin-top: var(--space-4); font-size: var(--font-size-xs); }
  .quote-summary > div { padding: var(--space-3); }
  .quote-summary > div.total { padding: var(--space-3); }
  .quote-summary .total dd { font-size: var(--font-size-md); }
  .quote-life { display: grid; gap: var(--space-2); }
  .quote-life > span:first-child { min-width: 0; }
}

@media (max-width: 359px) {
  .preset-buttons { gap: var(--space-1); }
  .preset-buttons button { padding-inline: var(--space-1); font-size: .65rem; }
  .quote-summary > div.total { display: grid; gap: var(--space-1); }
  .quote-summary .total dd { text-align: start; }
}
</style>
