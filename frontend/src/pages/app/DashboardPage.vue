<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type {
  OtcOrder,
  PortfolioPeriod,
  PortfolioValuePoint,
  PricePoint,
  Transaction,
  VerificationStep,
  VerificationSummary,
} from '@/types'
import { marketService } from '@/services/market.service'
import { orderService } from '@/services/order.service'
import { transactionService } from '@/services/transaction.service'
import { verificationService } from '@/services/verification.service'
import { useAuthStore } from '@/stores/auth'
import { useMarketStore } from '@/stores/markets'
import { usePreferencesStore } from '@/stores/preferences'
import { useWalletStore } from '@/stores/wallet'
import { accountLevelLabel } from '@/utils/account'
import { compareDecimal } from '@/utils/decimal'
import { formatRelativeTime, toPersianDigits } from '@/utils/formatters'
import { buildPortfolioValueHistory } from '@/utils/portfolio'
import AppButton from '@/components/ui/AppButton.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import PortfolioSummary from '@/components/finance/PortfolioSummary.vue'
import QuickActions from '@/components/finance/QuickActions.vue'
import DashboardMarketPreview from '@/components/dashboard/DashboardMarketPreview.vue'
import DashboardWalletPreview from '@/components/dashboard/DashboardWalletPreview.vue'
import OrderList from '@/components/orders/OrderList.vue'
import OtcQuickTrade from '@/components/trade/OtcQuickTrade.vue'
import TransactionList from '@/components/transactions/TransactionList.vue'

const auth = useAuthStore()
const marketStore = useMarketStore()
const walletStore = useWalletStore()
const preferencesStore = usePreferencesStore()
const recentOrders = ref<OtcOrder[]>([])
const recentTransactions = ref<Transaction[]>([])
const verification = ref<VerificationSummary | null>(null)
const portfolioHistory = ref<PortfolioValuePoint[]>([])
const portfolioPeriod = ref<PortfolioPeriod>('7d')
const portfolioHistoryLoading = ref(false)
const portfolioHistoryError = ref('')
const auxiliaryLoading = ref(true)
const verificationLoading = ref(true)
const auxiliaryError = ref('')
const route = useRoute()
const router = useRouter()
const showWelcome = ref(route.query.welcome === '1')
let portfolioHistoryRequestSequence = 0

const isLoading = computed(() => marketStore.loading || walletStore.loading || auxiliaryLoading.value)
const hidden = computed(() => preferencesStore.preferences.hideBalances)
const walletUpdatedLabel = computed(() => walletStore.lastUpdated
  ? `آخرین به‌روزرسانی: ${formatRelativeTime(walletStore.lastUpdated)}`
  : undefined)
const level = computed(() => accountLevelLabel(verification.value?.currentLevel || auth.user?.accountLevel))
const requiredSteps = computed(() => verification.value?.steps.filter((step) => step.required) ?? [])
const remainingRequiredSteps = computed(() => requiredSteps.value.filter((step) => step.status !== 'verified').length)
const welcomeMessage = computed(() => remainingRequiredSteps.value
  ? `${toPersianDigits(remainingRequiredSteps.value)} گام ضروری تا آماده‌شدن کامل حساب باقی مانده است.`
  : 'مراحل ضروری حساب شما تکمیل شده است؛ می‌توانید خدمات فعال را استفاده کنید.')
const fatalError = computed(() => !isLoading.value && !walletStore.summary
  ? walletStore.error || 'اطلاعات کیف پول و دارایی‌ها دریافت نشد.'
  : '')
const verificationTitle = computed(() => {
  const status = verification.value?.status
  if (status === 'verified') return 'حساب شما آماده معامله است'
  if (status === 'pending' || status === 'in_progress') return 'احراز هویت شما در حال بررسی است'
  if (status === 'needs_correction' || status === 'rejected') return 'احراز هویت به اصلاح نیاز دارد'
  return 'برای استفاده کامل، احراز هویت را تکمیل کنید'
})
const verificationAction = computed(() => {
  const status = verification.value?.status
  if (status === 'verified' && (verification.value?.progressPercent ?? 0) < 100) return 'ارتقای سطح'
  if (status === 'pending' || status === 'in_progress') return 'مشاهده وضعیت'
  if (status === 'needs_correction' || status === 'rejected') return 'اصلاح اطلاعات'
  if (status === 'verified') return 'مشاهده سطح حساب'
  return 'تکمیل احراز هویت'
})

function stepRoute(step: VerificationStep): string {
  if (step.id === 'bank') return '/app/bank-accounts'
  if (step.id === 'basic_info') return '/app/profile'
  return '/app/verification'
}

function errorText(reason: unknown, fallback: string): string {
  return reason instanceof Error ? reason.message : fallback
}

function isUsablePricePoint(point: PricePoint): boolean {
  try {
    return Number.isFinite(Date.parse(point.timestamp)) && compareDecimal(point.priceToman, '0') > 0
  } catch {
    return false
  }
}

async function loadPortfolioHistory(period: PortfolioPeriod = portfolioPeriod.value): Promise<void> {
  const requestId = ++portfolioHistoryRequestSequence
  portfolioPeriod.value = period
  portfolioHistoryLoading.value = true
  portfolioHistoryError.value = ''

  const wallet = walletStore.summary
  const heldAssets = wallet?.assets.filter((asset) => (
    asset.symbol !== 'IRT'
    && compareDecimal(asset.total, '0') > 0
    && marketStore.assets.some((market) => market.symbol === asset.symbol)
  )) ?? []

  if (!wallet || !heldAssets.length) {
    if (requestId === portfolioHistoryRequestSequence) {
      portfolioHistory.value = []
      portfolioHistoryLoading.value = false
    }
    return
  }

  try {
    const histories = await Promise.all(heldAssets.map(async (asset) => ({
      asset,
      points: (await marketService.getPriceHistory(asset.symbol, period)).filter(isUsablePricePoint),
    })))
    if (requestId !== portfolioHistoryRequestSequence) return

    const history = buildPortfolioValueHistory(
      wallet.tomanBalance,
      histories.map((history) => ({ total: history.asset.total, points: history.points })),
    )
    portfolioHistory.value = history
    if (!history.length) portfolioHistoryError.value = 'دادهٔ تاریخی کافی برای این بازه وجود ندارد.'
  } catch (caught) {
    if (requestId === portfolioHistoryRequestSequence) {
      portfolioHistory.value = []
      portfolioHistoryError.value = errorText(caught, 'داده‌های تاریخی دارایی دریافت نشد.')
    }
  } finally {
    if (requestId === portfolioHistoryRequestSequence) portfolioHistoryLoading.value = false
  }
}

function changePortfolioPeriod(period: PortfolioPeriod): void {
  if (period === portfolioPeriod.value && portfolioHistory.value.length) return
  void loadPortfolioHistory(period)
}

const load = async () => {
  auxiliaryLoading.value = true
  verificationLoading.value = true
  verification.value = null
  auxiliaryError.value = ''
  const results = await Promise.allSettled([
    marketStore.fetchMarkets(),
    walletStore.fetchWallet(),
    orderService.list({ pageSize: 4 }),
    transactionService.list({ pageSize: 4 }),
    preferencesStore.hydrate(),
    verificationService.getSummary(),
  ])
  const [marketsResult, walletResult, ordersResult, transactionsResult, , verificationResult] = results
  const partialErrors: string[] = []

  if (marketsResult.status === 'rejected') partialErrors.push(errorText(marketsResult.reason, 'قیمت ارزها دریافت نشد.'))
  if (walletResult.status === 'rejected') partialErrors.push(errorText(walletResult.reason, 'اطلاعات کیف پول دریافت نشد.'))
  if (ordersResult.status === 'fulfilled') recentOrders.value = ordersResult.value.items
  else partialErrors.push(errorText(ordersResult.reason, 'سفارش‌های اخیر دریافت نشدند.'))
  if (transactionsResult.status === 'fulfilled') recentTransactions.value = transactionsResult.value.items
  else partialErrors.push(errorText(transactionsResult.reason, 'تراکنش‌های اخیر دریافت نشدند.'))
  if (verificationResult.status === 'fulfilled') verification.value = verificationResult.value
  else partialErrors.push(errorText(verificationResult.reason, 'وضعیت احراز هویت دریافت نشد.'))

  auxiliaryError.value = [...new Set(partialErrors)].join(' ')
  verificationLoading.value = false
  auxiliaryLoading.value = false
  if (marketsResult.status === 'fulfilled' && walletResult.status === 'fulfilled') {
    void loadPortfolioHistory()
  } else if (walletResult.status === 'fulfilled' && marketsResult.status === 'rejected') {
    portfolioHistory.value = []
    portfolioHistoryLoading.value = false
    portfolioHistoryError.value = errorText(marketsResult.reason, 'قیمت‌های تاریخی دارایی دریافت نشد.')
  }
}

const dismissWelcome = () => {
  showWelcome.value = false
  const query = { ...route.query }
  delete query.welcome
  void router.replace({ query })
}

onMounted(() => { void load() })
</script>

<template>
  <div class="page dashboard-page">
    <PageHeader title="داشبورد" description="تصویر روشن و به‌روز از دارایی‌ها و فعالیت حساب شما">
      <template v-if="level" #actions><AppButton variant="secondary" size="sm" to="/app/verification" icon="verify">{{ level }}</AppButton></template>
    </PageHeader>

    <AppCard v-if="showWelcome && verification" class="welcome-checklist" padding="md">
      <div class="welcome-copy"><span class="welcome-icon"><AppIcon name="sparkle" :size="24" /></span><div><h2>حسابتان را برای اولین معامله آماده کنید</h2><p>{{ welcomeMessage }}</p></div><button type="button" aria-label="بستن راهنمای شروع" @click="dismissWelcome"><AppIcon name="close" :size="19" /></button></div>
      <div class="welcome-steps" :style="{ '--welcome-columns': String(Math.max(1, requiredSteps.length)) }">
        <RouterLink v-for="(step, index) in requiredSteps" :key="step.id" :to="stepRoute(step)" :class="{ done: step.status === 'verified' }">
          <i><AppIcon v-if="step.status === 'verified'" name="check" :size="14" /><template v-else>{{ toPersianDigits(index + 1) }}</template></i>{{ step.title }}
        </RouterLink>
      </div>
    </AppCard>
    <AppSkeleton v-else-if="showWelcome && verificationLoading" height="8rem" radius="var(--radius-xl)" />

    <div v-if="isLoading && !walletStore.summary" class="dashboard-skeleton" aria-label="در حال دریافت داشبورد">
      <AppSkeleton height="29rem" radius="var(--radius-xl)" /><AppSkeleton height="8rem" radius="var(--radius-xl)" /><AppSkeleton height="40rem" radius="var(--radius-xl)" />
    </div>

    <AppCard v-else-if="fatalError" class="dashboard-fatal" padding="lg" role="alert">
      <span><AppIcon name="warning" :size="26" /></span><div><strong>داشبورد آماده نشد</strong><p>{{ fatalError }}</p></div><AppButton variant="secondary" icon="refresh" @click="load">تلاش دوباره</AppButton>
    </AppCard>

    <div v-else-if="walletStore.summary" class="dashboard-layout">
      <div class="dashboard-primary">
        <div class="dashboard-overview">
          <PortfolioSummary
            class="area-portfolio"
            :total="walletStore.summary.totalValueToman"
            :toman="walletStore.summary.tomanBalance"
            :crypto="walletStore.summary.cryptoValueToman"
            :hidden="hidden"
            :updated-label="walletUpdatedLabel"
            :history="portfolioHistory"
            :history-period="portfolioPeriod"
            :history-loading="portfolioHistoryLoading"
            :history-error="portfolioHistoryError"
            @toggle="preferencesStore.toggleBalances()"
            @update:history-period="changePortfolioPeriod"
            @retry-history="loadPortfolioHistory()"
          />
          <div class="area-actions">
            <div class="block-heading"><h2>عملیات سریع</h2><span>خرید، فروش و جابه‌جایی تومان</span></div>
            <QuickActions />
          </div>
        </div>
        <OtcQuickTrade v-if="marketStore.assets.length" class="area-trade" :assets="marketStore.assets" :wallet="walletStore.summary" compact />
        <AppCard v-else class="area-trade market-unavailable" padding="lg"><AppIcon name="warning" :size="24" /><strong>نرخ‌های معامله در دسترس نیست</strong><p>{{ marketStore.error || 'برای دریافت دوباره نرخ‌ها تلاش کنید.' }}</p><AppButton variant="secondary" size="sm" icon="refresh" @click="load">تلاش دوباره</AppButton></AppCard>
      </div>
      <AppCard v-if="verification" class="area-kyc account-ready" padding="md">
        <span class="ready-icon"><AppIcon name="verify" :size="24" /></span>
        <div><strong>{{ verificationTitle }}</strong><p>{{ verification.message }}</p><span class="progress"><i :style="{ width: `${verification.progressPercent}%` }" /></span></div>
        <AppButton variant="secondary" size="sm" to="/app/verification">{{ verificationAction }}</AppButton>
      </AppCard>
      <AppSkeleton v-else-if="verificationLoading" class="area-kyc" height="7rem" radius="var(--radius-xl)" />
    </div>

    <div v-if="walletStore.summary" class="dashboard-sections">
      <AppCard class="dashboard-preview-card" padding="none">
        <div class="card-heading"><div><h2>دارایی‌های من</h2><p>خلاصه موجودی و ارزش روز دارایی‌ها</p></div><RouterLink to="/app/wallet">مشاهده کیف پول <AppIcon name="chevronLeft" :size="16" /></RouterLink></div>
        <DashboardWalletPreview :assets="walletStore.summary.assets.slice(0, 4)" :hidden="hidden" />
      </AppCard>

      <AppCard class="dashboard-preview-card" padding="none">
        <div class="card-heading"><div><h2>قیمت ارزها</h2><p>قیمت خرید و تغییرات ۲۴ ساعت بازار</p></div><RouterLink to="/app/markets">مشاهده همه ارزها <AppIcon name="chevronLeft" :size="16" /></RouterLink></div>
        <DashboardMarketPreview :assets="marketStore.assets.slice(0, 4)" />
      </AppCard>

      <div class="activity-grid">
        <AppCard padding="none">
          <div class="card-heading"><div><h2>سفارش‌های اخیر</h2><p>آخرین خرید و فروش‌های OTC</p></div><RouterLink to="/app/orders">همه سفارش‌ها <AppIcon name="chevronLeft" :size="16" /></RouterLink></div>
          <OrderList :orders="recentOrders" compact />
        </AppCard>
        <AppCard padding="none">
          <div class="card-heading"><div><h2>تراکنش‌های اخیر</h2><p>گردش مالی حساب شما</p></div><RouterLink to="/app/transactions">همه تراکنش‌ها <AppIcon name="chevronLeft" :size="16" /></RouterLink></div>
          <TransactionList :transactions="recentTransactions" compact />
        </AppCard>
      </div>

      <div v-if="auxiliaryError" class="load-error" role="alert"><AppIcon name="warning" :size="19" /><span>{{ auxiliaryError }}</span><button type="button" @click="load">تلاش دوباره</button></div>
    </div>
  </div>
</template>

<style scoped>
.dashboard-page { container: dashboard / inline-size; }
.dashboard-layout { display: grid; grid-template-columns: minmax(0, 1.12fr) minmax(34rem, .88fr); align-items: start; gap: var(--space-5); }
.dashboard-primary { display: contents; }
.dashboard-overview { display: grid; min-width: 0; grid-column: 1; grid-row: 1; gap: var(--space-5); }
.welcome-checklist { margin-bottom: var(--space-5); border-color: rgba(67,139,255,.2); background: linear-gradient(100deg, var(--color-primary-soft), var(--color-surface-1) 58%); }.welcome-copy { display: flex; align-items: center; gap: var(--space-3); }.welcome-icon { display: grid; width: 3rem; height: 3rem; flex: 0 0 auto; border-radius: .95rem; background: var(--color-primary); color: white; place-items: center; }.welcome-copy > div { flex: 1; }.welcome-copy h2 { margin: 0; font-size: var(--font-size-lg); }.welcome-copy p { margin: .1rem 0 0; color: var(--color-text-muted); font-size: var(--font-size-xs); }.welcome-copy > button { display: grid; width: 2.5rem; height: 2.5rem; border: 0; border-radius: var(--radius-sm); background: transparent; color: var(--color-text-muted); place-items: center; }.welcome-steps { display: grid; grid-template-columns: repeat(var(--welcome-columns), minmax(0, 1fr)); gap: var(--space-2); margin-top: var(--space-4); }.welcome-steps > * { display: flex; min-height: 2.75rem; align-items: center; justify-content: center; gap: var(--space-2); padding-inline: var(--space-2); border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface-2); color: var(--color-text-secondary); font-size: var(--font-size-xs); }.welcome-steps i { display: grid; width: 1.3rem; height: 1.3rem; border-radius: 50%; background: var(--color-surface-3); color: var(--color-text-muted); font-style: normal; place-items: center; }.welcome-steps .done { border-color: rgba(53,201,149,.18); background: var(--color-success-soft); color: var(--color-success); }
.area-trade { min-width: 0; grid-column: 2; grid-row: 1 / span 2; }
.block-heading { display: flex; align-items: baseline; justify-content: space-between; gap: var(--space-3); margin-bottom: var(--space-3); }
.block-heading h2 { margin: 0; color: var(--color-text-primary); font-size: var(--font-size-md); font-weight: 600; }
.block-heading span { color: var(--color-text-muted); font-size: var(--font-size-xs); }
.area-kyc { grid-column: 1; grid-row: 2; }
.account-ready { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: var(--space-4); border-color: rgba(221,183,110,.17); background: linear-gradient(100deg, var(--color-gold-soft), var(--color-surface-1) 55%); }
.ready-icon { display: grid; width: 3rem; height: 3rem; border-radius: .9rem; background: var(--color-gold-soft); color: var(--color-gold); place-items: center; }
.account-ready strong { font-size: var(--font-size-sm); }.account-ready p { margin: .2rem 0 var(--space-2); color: var(--color-text-muted); font-size: var(--font-size-xs); }
.progress { display: block; width: min(15rem, 100%); height: .25rem; overflow: hidden; border-radius: var(--radius-pill); background: var(--color-surface-3); }.progress i { display: block; height: 100%; background: var(--color-gold); }
.dashboard-sections { display: grid; min-width: 0; grid-template-columns: repeat(auto-fit, minmax(min(100%, 38rem), 1fr)); gap: var(--space-5); margin-top: var(--space-5); }
.dashboard-sections > *, .activity-grid > * { min-width: 0; }
.card-heading { display: flex; min-width: 0; align-items: flex-start; justify-content: space-between; flex-wrap: wrap; gap: var(--space-3) var(--space-4); padding: var(--space-5); border-block-end: 1px solid var(--color-border-soft); }
.card-heading > div { min-width: min(16rem, 100%); flex: 1; }
.card-heading h2 { margin: 0; font-size: var(--font-size-lg); }.card-heading p { margin: .2rem 0 0; color: var(--color-text-muted); font-size: var(--font-size-xs); }.card-heading a { display: inline-flex; align-items: center; gap: var(--space-1); color: var(--color-primary); font-size: var(--font-size-xs); font-weight: 600; white-space: nowrap; }
.card-heading a { min-height: 2.75rem; flex: 0 0 auto; margin-block: -.55rem; padding-inline: .25rem; }
.activity-grid { display: grid; min-width: 0; grid-column: 1 / -1; grid-template-columns: repeat(auto-fit, minmax(min(100%, 38rem), 1fr)); gap: var(--space-5); }
.dashboard-skeleton { display: grid; grid-template-columns: 1fr minmax(26rem, .72fr); gap: var(--space-5); }.dashboard-skeleton > :last-child { grid-column: 2; grid-row: 1 / span 2; }
.load-error { display: flex; grid-column: 1 / -1; align-items: center; gap: var(--space-2); padding: var(--space-3) var(--space-4); border: 1px solid rgba(240,108,117,.18); border-radius: var(--radius-md); background: var(--color-danger-soft); color: var(--color-danger); }.load-error span { flex: 1; }.load-error button { border: 0; background: transparent; color: inherit; font-weight: 700; text-decoration: underline; }
.dashboard-fatal { display: flex; align-items: center; gap: var(--space-4); }.dashboard-fatal > span { display: grid; width: 3.25rem; height: 3.25rem; flex: 0 0 auto; border-radius: 1rem; background: var(--color-danger-soft); color: var(--color-danger); place-items: center; }.dashboard-fatal > div { flex: 1; }.dashboard-fatal strong { font-size: var(--font-size-lg); }.dashboard-fatal p, .market-unavailable p { margin: .15rem 0 0; color: var(--color-text-muted); font-size: var(--font-size-sm); }.market-unavailable { display: grid; justify-items: start; gap: var(--space-3); }
@container dashboard (max-width: 72rem) {
  .dashboard-layout { grid-template-columns: minmax(0, 1fr); }
  .dashboard-overview, .area-trade, .area-kyc { grid-column: auto; grid-row: auto; }
  .dashboard-skeleton { grid-template-columns: minmax(0, 1fr); }
  .dashboard-skeleton > :last-child { grid-column: 1; grid-row: auto; }
}
@media (max-width: 767px) { .dashboard-page :deep(.page-header) { margin-bottom: var(--space-4); }.dashboard-page :deep(.page-header p) { display: none; }.dashboard-primary, .dashboard-overview { gap: var(--space-4); }.welcome-copy { align-items: flex-start; }.welcome-copy p { line-height: 1.7; }.welcome-steps { display: flex; overflow-x: auto; padding-bottom: var(--space-1); scroll-snap-type: x mandatory; }.welcome-steps > * { min-width: 9rem; scroll-snap-align: start; }.account-ready { grid-template-columns: auto minmax(0, 1fr); }.account-ready .app-button { grid-column: 2; justify-self: start; }.area-actions :deep(.quick-actions) { grid-template-columns: repeat(4, minmax(0, 1fr)); }.block-heading span { display: none; }.card-heading { padding: var(--space-4); }.card-heading p { display: none; }.card-heading h2 { font-size: var(--font-size-md); }.area-trade { margin-inline: calc(var(--space-4) * -1); border-inline: 0; border-radius: var(--radius-xl); }.dashboard-fatal { align-items: flex-start; flex-wrap: wrap; }.dashboard-fatal > div { min-width: calc(100% - 5rem); } }
@media (max-width: 420px) { .area-actions :deep(.quick-actions) { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 359px) { .area-trade { margin-inline: calc(var(--space-3) * -1); }.account-ready { grid-template-columns: 1fr; }.account-ready .app-button { grid-column: 1; } }
</style>
