<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import type { PortfolioPeriod, PricePoint, Transaction } from '@/types'
import { marketService } from '@/services/market.service'
import { transactionService } from '@/services/transaction.service'
import { useMarketStore } from '@/stores/markets'
import { useWalletStore } from '@/stores/wallet'
import { formatCrypto, formatPercentage, formatToman } from '@/utils/formatters'
import AppButton from '@/components/ui/AppButton.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import AssetAvatar from '@/components/finance/AssetAvatar.vue'
import AssetPriceChart from '@/components/finance/AssetPriceChart.vue'
import TransactionList from '@/components/transactions/TransactionList.vue'

const route = useRoute()
const marketStore = useMarketStore()
const walletStore = useWalletStore()
const history = ref<PricePoint[]>([])
const historyPeriod = ref<PortfolioPeriod>('24h')
const historyLoading = ref(false)
const historyError = ref('')
const transactions = ref<Transaction[]>([])
const transactionsLoading = ref(false)
const transactionsError = ref('')
const loading = ref(true)
const error = ref('')
let requestSequence = 0
let historyRequestSequence = 0
let transactionRequestSequence = 0
const symbol = computed(() => String(route.params.symbol || 'USDT').toUpperCase())
const asset = computed(() => marketStore.assets.find((item) => item.symbol === symbol.value))
const walletAsset = computed(() => walletStore.summary?.assets.find((item) => item.symbol === symbol.value))
const trend = computed(() => Number(asset.value?.change24hPercent || 0) >= 0)

async function loadHistory(period: PortfolioPeriod = historyPeriod.value): Promise<void> {
  const requestedSymbol = symbol.value
  const requestId = ++historyRequestSequence
  historyPeriod.value = period
  historyLoading.value = true
  historyError.value = ''
  try {
    const points = await marketService.getPriceHistory(requestedSymbol, period)
    if (requestId !== historyRequestSequence || requestedSymbol !== symbol.value) return
    history.value = points
    if (points.length < 2) historyError.value = 'دادهٔ تاریخی کافی برای این بازه وجود ندارد.'
  } catch (caught) {
    if (requestId !== historyRequestSequence) return
    history.value = []
    historyError.value = caught instanceof Error ? caught.message : 'نمودار قیمت دریافت نشد.'
  } finally {
    if (requestId === historyRequestSequence) historyLoading.value = false
  }
}

async function loadTransactions(): Promise<void> {
  const requestedSymbol = symbol.value
  const requestId = ++transactionRequestSequence
  transactionsLoading.value = true
  transactionsError.value = ''
  try {
    const result = await transactionService.list({ assetSymbol: requestedSymbol, pageSize: 4 })
    if (requestId !== transactionRequestSequence || requestedSymbol !== symbol.value) return
    transactions.value = result.items
  } catch (caught) {
    if (requestId !== transactionRequestSequence) return
    transactions.value = []
    transactionsError.value = caught instanceof Error ? caught.message : 'تراکنش‌های این ارز دریافت نشد.'
  } finally {
    if (requestId === transactionRequestSequence) transactionsLoading.value = false
  }
}

async function loadAsset(): Promise<void> {
  const requestedSymbol = symbol.value
  const requestId = ++requestSequence
  loading.value = true
  error.value = ''
  history.value = []
  transactions.value = []
  try {
    await Promise.all([marketStore.fetchMarkets(), walletStore.fetchWallet()])
    if (requestId !== requestSequence) return
    if (!marketStore.assets.some((item) => item.symbol === requestedSymbol)) {
      throw new Error('ارز مورد نظر پیدا نشد یا در دسترس نیست.')
    }
    if (requestId !== requestSequence) return
    loading.value = false
    await Promise.allSettled([loadHistory(), loadTransactions()])
  } catch (caught) {
    if (requestId === requestSequence) {
      error.value = caught instanceof Error ? caught.message : 'اطلاعات این ارز دریافت نشد.'
    }
  } finally {
    if (requestId === requestSequence) loading.value = false
  }
}

watch(symbol, () => { void loadAsset() }, { immediate: true })

function changeHistoryPeriod(period: PortfolioPeriod): void {
  if (period === historyPeriod.value && history.value.length) return
  void loadHistory(period)
}
</script>

<template>
  <div class="page asset-page">
    <PageHeader :title="asset ? `${asset.nameFa} (${asset.symbol})` : 'جزئیات ارز'" description="قیمت، موجودی و عملیات این دارایی" back-to="/app/markets" />
    <AppSkeleton v-if="loading" height="24rem" radius="var(--radius-xl)" />
    <EmptyState v-else-if="error || !asset" icon="warning" title="اطلاعات ارز در دسترس نیست" :description="error || 'ارز مورد نظر پیدا نشد.'"><AppButton to="/app/markets">بازگشت به ارزها</AppButton></EmptyState>
    <template v-else-if="asset">
      <div class="asset-overview">
        <AppCard class="price-card" padding="lg">
          <div class="asset-heading"><AssetAvatar :symbol="asset.symbol" :color="asset.color" size="lg" /><div><span>{{ asset.nameEn }}</span><h2>{{ asset.nameFa }}</h2></div><span class="change" :class="trend ? 'up' : 'down'"><AppIcon :name="trend ? 'arrowUp' : 'arrowDown'" :size="16" /> {{ formatPercentage(asset.change24hPercent, { showSign: true }) }}</span></div>
          <div class="prices"><div><small>خرید از روشا</small><strong>{{ formatToman(asset.buyPriceToman) }}</strong></div><div><small>فروش به روشا</small><strong>{{ formatToman(asset.sellPriceToman) }}</strong></div></div>
          <AssetPriceChart
            :points="history"
            :period="historyPeriod"
            :loading="historyLoading"
            :error="historyError"
            @update:period="changeHistoryPeriod"
            @retry="loadHistory()"
          />
          <div class="chart-meta"><span>کمترین ۲۴ ساعت: {{ formatToman(asset.low24hToman) }}</span><span>بیشترین ۲۴ ساعت: {{ formatToman(asset.high24hToman) }}</span></div>
        </AppCard>
        <AppCard class="holding-card" padding="lg">
          <span class="label">دارایی شما</span><strong class="balance"><bdi dir="ltr">{{ formatCrypto(walletAsset?.total || '0', { symbol: asset.symbol }) }}</bdi></strong><span class="equivalent">معادل {{ formatToman(walletAsset?.tomanValue || '0') }}</span>
          <div class="holding-split"><span><small>قابل استفاده</small><strong><bdi dir="ltr">{{ formatCrypto(walletAsset?.available || '0', { symbol: asset.symbol }) }}</bdi></strong></span><span><small>مسدود</small><strong><bdi dir="ltr">{{ formatCrypto(walletAsset?.locked || '0', { symbol: asset.symbol }) }}</bdi></strong></span></div>
          <div class="holding-actions"><AppButton block :disabled="!asset.tradable" :to="asset.tradable ? `/app/trade?side=buy&asset=${asset.symbol}` : undefined">خرید</AppButton><AppButton block variant="secondary" :disabled="!asset.tradable" :to="asset.tradable ? `/app/trade?side=sell&asset=${asset.symbol}` : undefined">فروش</AppButton><AppButton block variant="ghost" :disabled="!asset.depositEnabled" :to="asset.depositEnabled ? `/app/deposit/crypto/${asset.symbol}` : undefined">واریز</AppButton><AppButton block variant="ghost" :disabled="!asset.withdrawalEnabled" :to="asset.withdrawalEnabled ? `/app/withdraw/crypto/${asset.symbol}` : undefined">برداشت</AppButton></div>
        </AppCard>
      </div>
      <AppCard class="networks" padding="none"><div class="section-head"><div><h2>شبکه‌های پشتیبانی‌شده</h2><p>پیش از انتقال، شبکه مبدأ و مقصد را یکسان انتخاب کنید.</p></div></div><div class="network-list"><div v-for="network in asset.networks" :key="network.id"><span><strong>{{ network.displayName }}</strong><small>{{ network.estimatedArrivalMinutes }} دقیقه تقریبی · {{ network.confirmations }} تأیید</small></span><span :class="network.status">{{ network.status === 'active' ? 'فعال' : network.status === 'congested' ? 'شبکه شلوغ' : 'در حال به‌روزرسانی' }}</span></div></div></AppCard>
      <AppCard padding="none"><div class="section-head"><div><h2>تراکنش‌های اخیر {{ asset.nameFa }}</h2><p>واریز، برداشت و معامله‌های این دارایی</p></div><RouterLink to="/app/transactions">همه تراکنش‌ها <AppIcon name="chevronLeft" :size="16" /></RouterLink></div><div v-if="transactionsLoading" class="activity-loading"><AppSkeleton height="4.5rem" /><AppSkeleton height="4.5rem" /></div><div v-else-if="transactionsError" class="activity-error" role="alert"><AppIcon name="warning" :size="20" /><span>{{ transactionsError }}</span><AppButton variant="secondary" size="sm" icon="refresh" @click="loadTransactions">تلاش دوباره</AppButton></div><TransactionList v-else :transactions="transactions" compact /></AppCard>
    </template>
  </div>
</template>

<style scoped>
.asset-page { max-width: 78rem; }.asset-overview { display: grid; grid-template-columns: minmax(0, 1.35fr) minmax(20rem, .65fr); gap: var(--space-5); }.asset-heading { display: flex; align-items: center; gap: var(--space-3); }.asset-heading > div { flex: 1; }.asset-heading h2 { margin: .1rem 0 0; font-size: var(--font-size-xl); }.asset-heading > div span { color: var(--color-text-muted); font-size: var(--font-size-xs); direction: ltr; }.change { display: inline-flex; align-items: center; gap: .2rem; direction: ltr; font-weight: 600; }.change.up { color: var(--color-success); }.change.down { color: var(--color-danger); }.prices { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-4); margin-top: var(--space-6); }.prices > div { display: grid; gap: .2rem; padding: var(--space-4); border-radius: var(--radius-md); background: var(--color-surface-2); }.prices small, .chart-meta, .label, .equivalent { color: var(--color-text-muted); font-size: var(--font-size-xs); }.prices strong { overflow-wrap: anywhere; font-size: var(--font-size-lg); }.chart-meta { display: flex; justify-content: space-between; gap: var(--space-3); margin-top: var(--space-2); }.holding-card { display: flex; flex-direction: column; }.balance { margin-top: var(--space-2); overflow-wrap: anywhere; font-size: var(--font-size-2xl); }.equivalent { margin-top: .1rem; }.holding-split { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-2); margin-block: var(--space-5); }.holding-split span { display: grid; min-width: 0; padding: var(--space-3); border-radius: var(--radius-md); background: var(--color-surface-2); }.holding-split small { color: var(--color-text-muted); font-size: var(--font-size-xs); }.holding-split strong { margin-top: .2rem; overflow-wrap: anywhere; font-size: var(--font-size-xs); }.holding-actions { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-2); margin-top: auto; }.networks { margin-top: var(--space-5); }.section-head { display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); padding: var(--space-5); border-block-end: 1px solid var(--color-border-soft); }.section-head h2 { margin: 0; font-size: var(--font-size-lg); }.section-head p { margin: .15rem 0 0; color: var(--color-text-muted); font-size: var(--font-size-xs); }.section-head a { display: inline-flex; align-items: center; color: var(--color-primary); font-size: var(--font-size-xs); font-weight: 600; }.network-list { display: grid; grid-template-columns: repeat(auto-fit, minmax(15rem, 1fr)); gap: var(--space-3); padding: var(--space-5); }.network-list > div { display: flex; align-items: center; justify-content: space-between; gap: var(--space-3); padding: var(--space-4); border: 1px solid var(--color-border-soft); border-radius: var(--radius-md); background: var(--color-surface-2); }.network-list > div > span:first-child { display: grid; min-width: 0; }.network-list small { overflow-wrap: anywhere; color: var(--color-text-muted); font-size: var(--font-size-xs); }.network-list > div > span:last-child { flex: 0 0 auto; padding: .15rem .5rem; border-radius: var(--radius-pill); font-size: var(--font-size-xs); }.network-list .active { background: var(--color-success-soft); color: var(--color-success); }.network-list .congested, .network-list .maintenance { background: var(--color-warning-soft); color: var(--color-warning); }.activity-loading { display: grid; gap: var(--space-2); padding: var(--space-4); }.activity-error { display: flex; align-items: center; gap: var(--space-3); padding: var(--space-5); color: var(--color-danger); }.activity-error span { min-width: 0; flex: 1; }.asset-page > :deep(.app-card:last-child) { margin-top: var(--space-5); }
@media (max-width: 900px) { .asset-overview { grid-template-columns: 1fr; } }
@media (max-width: 767px) { .prices strong { font-size: var(--font-size-sm); }.chart-meta { align-items: flex-start; flex-direction: column; gap: .15rem; }.network-list { grid-template-columns: 1fr; padding: var(--space-4); }.section-head { padding: var(--space-4); }.section-head p { display: none; }.activity-error { align-items: flex-start; flex-direction: column; }.activity-error :deep(.app-button) { width: 100%; } }
</style>
