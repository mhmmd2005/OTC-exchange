<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import type { TradeSide, VerificationSummary } from '@/types'
import { verificationService } from '@/services/verification.service'
import { useMarketStore } from '@/stores/markets'
import { useWalletStore } from '@/stores/wallet'
import { accountLevelLabel } from '@/utils/account'
import { compareDecimal, subtractDecimal } from '@/utils/decimal'
import { formatToman } from '@/utils/formatters'
import AppButton from '@/components/ui/AppButton.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import OtcQuickTrade from '@/components/trade/OtcQuickTrade.vue'

const route = useRoute()
const marketStore = useMarketStore()
const walletStore = useWalletStore()
const verification = ref<VerificationSummary | null>(null)
const loading = ref(true)
const coreError = ref('')
const initialSide = computed<TradeSide>(() => route.query.side === 'sell' ? 'sell' : 'buy')
const initialAsset = computed(() => typeof route.query.asset === 'string' ? route.query.asset.toUpperCase() : 'USDT')
const level = computed(() => accountLevelLabel(verification.value?.currentLevel))

function remaining(limit: string, used: string): string {
  const value = subtractDecimal(limit, used)
  return compareDecimal(value, '0') < 0 ? '0' : value
}

const remainingBuy = computed(() => verification.value
  ? remaining(verification.value.limits.dailyBuy, verification.value.limits.usedBuy)
  : '')
const remainingSell = computed(() => verification.value
  ? remaining(verification.value.limits.dailySell, verification.value.limits.usedSell)
  : '')

async function load(): Promise<void> {
  loading.value = true
  verification.value = null
  coreError.value = ''
  const [marketsResult, walletResult, verificationResult] = await Promise.allSettled([
    marketStore.fetchMarkets(),
    walletStore.fetchWallet(),
    verificationService.getSummary(),
  ])
  if (verificationResult.status === 'fulfilled') verification.value = verificationResult.value
  if (marketsResult.status === 'rejected' || walletResult.status === 'rejected') {
    const reason = marketsResult.status === 'rejected' ? marketsResult.reason : walletResult.status === 'rejected' ? walletResult.reason : undefined
    coreError.value = reason instanceof Error ? reason.message : 'اطلاعات لازم برای معامله دریافت نشد.'
  }
  loading.value = false
}

onMounted(() => { void load() })
</script>

<template>
  <div class="page trade-page">
    <PageHeader title="خرید و فروش مستقیم" description="بدون بازار معاملاتی؛ شما مستقیم از روشا می‌خرید یا به روشا می‌فروشید">
      <template v-if="marketStore.lastUpdated" #actions><span class="market-live"><i /> نرخ‌ها به‌روز هستند</span></template>
    </PageHeader>
    <div class="trade-layout">
      <OtcQuickTrade v-if="!loading && !coreError && walletStore.summary && marketStore.assets.length" :key="`${initialSide}-${initialAsset}`" :assets="marketStore.assets" :wallet="walletStore.summary" :initial-side="initialSide" :initial-asset="initialAsset" />
      <AppSkeleton v-else-if="loading" height="42rem" radius="var(--radius-xl)" />
      <AppCard v-else class="trade-error" padding="lg" role="alert"><span><AppIcon name="warning" :size="25" /></span><div><strong>فرم معامله آماده نشد</strong><p>{{ coreError || 'کیف پول یا نرخ ارزها در دسترس نیست.' }}</p></div><AppButton variant="secondary" icon="refresh" @click="load">تلاش دوباره</AppButton></AppCard>
      <aside class="trade-aside">
        <AppCard class="trust-card">
          <span class="trust-mark"><AppIcon name="shield" :size="25" /></span>
          <h2>معامله‌ای ساده و قابل پیش‌بینی</h2>
          <p>طرف معامله شما روشاست؛ نرخ، کارمزد و مبلغ نهایی را پیش از ثبت می‌بینید.</p>
          <ul><li><AppIcon name="check" :size="16" /> بدون صف خریدار و فروشنده</li><li><AppIcon name="check" :size="16" /> تأیید مبلغ نهایی پیش از ثبت</li><li><AppIcon name="check" :size="16" /> پیگیری سفارش از یک مسیر روشن</li></ul>
        </AppCard>
        <AppCard v-if="verification">
          <div class="aside-title"><span><AppIcon name="info" :size="20" /></span><div><h3>حدود معامله امروز</h3><p v-if="level">بر اساس {{ level }} حساب شما</p></div></div>
          <dl class="limits"><div><dt>حداقل هر سفارش</dt><dd>۱ میلیون تومان</dd></div><div><dt>حداکثر هر سفارش</dt><dd>۵۰۰ میلیون تومان</dd></div><div><dt>باقی‌مانده خرید امروز</dt><dd class="success">{{ formatToman(remainingBuy) }}</dd></div><div><dt>باقی‌مانده فروش امروز</dt><dd class="success">{{ formatToman(remainingSell) }}</dd></div></dl>
          <RouterLink to="/app/verification">مشاهده سطح و سقف‌ها <AppIcon name="chevronLeft" :size="16" /></RouterLink>
        </AppCard>
        <AppSkeleton v-else-if="loading" height="18rem" radius="var(--radius-xl)" />
        <div class="support-tip"><AppIcon name="help" :size="19" /><span>برای معامله نیاز به راهنمایی دارید؟</span><RouterLink to="/app/support">گفت‌وگو با پشتیبانی</RouterLink></div>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.trade-page { max-width: 80rem; }
.market-live { display: inline-flex; align-items: center; gap: var(--space-2); padding: .45rem .7rem; border: 1px solid color-mix(in srgb, var(--color-success), transparent 80%); border-radius: var(--radius-pill); background: var(--color-success-soft); color: var(--color-success); font-size: var(--font-size-xs); font-weight: 600; }
.market-live i { width: .42rem; height: .42rem; border-radius: 50%; background: currentColor; box-shadow: 0 0 0 4px color-mix(in srgb, var(--color-success), transparent 86%); }
.trade-layout { display: grid; grid-template-columns: minmax(28rem, 1.35fr) minmax(19rem, .65fr); align-items: start; gap: var(--space-5); }
.trade-aside { position: sticky; inset-block-start: calc(var(--header-height) + var(--space-5)); display: grid; gap: var(--space-4); }
.trust-card { border-color: color-mix(in srgb, var(--color-primary), var(--color-border) 72%); background: linear-gradient(145deg, var(--color-surface-1), color-mix(in srgb, var(--color-primary-soft), var(--color-surface-1) 45%)); }
.trust-mark { display: grid; width: 3.25rem; height: 3.25rem; border: 1px solid color-mix(in srgb, var(--color-primary), transparent 78%); border-radius: 1rem; background: var(--color-primary-soft); color: var(--color-primary); place-items: center; }
.trust-card h2 { margin: var(--space-4) 0 var(--space-2); font-size: var(--font-size-xl); }
.trust-card p { margin-bottom: 0; color: var(--color-text-muted); font-size: var(--font-size-sm); }
.trust-card ul { display: grid; gap: var(--space-2); margin: var(--space-5) 0 0; padding: 0; list-style: none; }
.trust-card li { display: flex; align-items: center; gap: var(--space-2); padding: var(--space-2) var(--space-3); border-radius: var(--radius-sm); background: color-mix(in srgb, var(--color-surface-2), transparent 24%); color: var(--color-text-secondary); font-size: var(--font-size-sm); }
.trust-card li :deep(svg) { color: var(--color-success); }
.aside-title { display: flex; align-items: center; gap: var(--space-3); }
.aside-title > span { display: grid; width: 2.7rem; height: 2.7rem; border-radius: .8rem; background: var(--color-info-soft); color: var(--color-info); place-items: center; }
.aside-title h3 { margin: 0; font-size: var(--font-size-md); }
.aside-title p { margin: .1rem 0 0; color: var(--color-text-muted); font-size: var(--font-size-xs); }
.limits { display: grid; gap: var(--space-3); margin: var(--space-5) 0; }
.limits div { display: flex; justify-content: space-between; gap: var(--space-3); padding-bottom: var(--space-3); border-block-end: 1px solid var(--color-border-soft); }
.limits div:last-child { padding-bottom: 0; border: 0; }
.limits dt { color: var(--color-text-muted); }
.limits dd { margin: 0; font-weight: 600; text-align: end; }
.limits .success { color: var(--color-success); }
.trade-aside .app-card > a { display: inline-flex; align-items: center; gap: var(--space-1); color: var(--color-primary); font-size: var(--font-size-sm); font-weight: 600; }
.support-tip { display: flex; align-items: center; gap: var(--space-2); padding: var(--space-3); color: var(--color-text-muted); font-size: var(--font-size-xs); }
.support-tip span { flex: 1; }
.support-tip a { color: var(--color-primary); font-weight: 600; }
.trade-error { display: flex; align-items: center; gap: var(--space-4); }
.trade-error > span { display: grid; width: 3.25rem; height: 3.25rem; flex: 0 0 auto; border-radius: 1rem; background: var(--color-danger-soft); color: var(--color-danger); place-items: center; }
.trade-error > div { flex: 1; }
.trade-error p { margin: .15rem 0 0; color: var(--color-text-muted); }

@media (max-width: 980px) {
  .trade-layout { grid-template-columns: 1fr; }
  .trade-aside { position: static; grid-template-columns: 1fr 1fr; }
  .support-tip { grid-column: 1 / -1; }
}

@media (max-width: 767px) {
  .trade-page { padding-top: 0; }
  .trade-page :deep(.page-header p),
  .trade-page :deep(.page-header__actions) { display: none; }
  .trade-layout { gap: var(--space-4); }
  .trade-layout > :first-child { margin-inline: calc(var(--space-4) * -1); border-inline: 0; border-radius: 0 0 var(--radius-xl) var(--radius-xl); }
  .trade-aside { grid-template-columns: 1fr; }
  .trust-card, .support-tip { display: none; }
}

@media (max-width: 359px) {
  .trade-layout > :first-child { margin-inline: calc(var(--space-3) * -1); }
}
</style>
