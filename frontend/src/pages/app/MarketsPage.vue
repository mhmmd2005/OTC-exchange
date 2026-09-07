<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useMarketStore } from '@/stores/markets'
import { usePreferencesStore } from '@/stores/preferences'
import { useWalletStore } from '@/stores/wallet'
import { compareDecimal } from '@/utils/financial'
import { formatPercentage, formatPersianDateTime } from '@/utils/formatters'
import AppButton from '@/components/ui/AppButton.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import AppInput from '@/components/ui/AppInput.vue'
import AppSelect from '@/components/ui/AppSelect.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import AppTabs from '@/components/ui/AppTabs.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import MarketList from '@/components/markets/MarketList.vue'

const route = useRoute()
const marketStore = useMarketStore()
const walletStore = useWalletStore()
const preferencesStore = usePreferencesStore()
const search = ref(typeof route.query.q === 'string' ? route.query.q : '')
const scope = ref('all')
const sort = ref('default')
const sortOptions = [
  { value: 'default', label: 'مرتب‌سازی پیش‌فرض' },
  { value: 'change', label: 'بیشترین تغییر' },
  { value: 'price', label: 'بیشترین قیمت' },
]
const hasFilters = computed(() => Boolean(search.value.trim()) || scope.value === 'favorites')
const leadingMover = computed(() => [...marketStore.assets].sort((a, b) => compareDecimal(b.change24hPercent, a.change24hPercent))[0])
const heldAssetCount = computed(() => walletStore.assets.filter((item) => item.symbol !== 'IRT' && compareDecimal(item.total, '0') > 0).length)
const tradableCount = computed(() => marketStore.assets.filter((item) => item.tradable).length)

const filtered = computed(() => {
  const query = search.value.trim().toLocaleLowerCase('fa')
  let items = marketStore.assets.filter((asset) => !query || [asset.symbol, asset.nameFa, asset.nameEn].some((value) => value.toLocaleLowerCase('fa').includes(query)))
  if (scope.value === 'favorites') items = items.filter((asset) => preferencesStore.preferences.favoriteAssets.includes(asset.symbol))
  if (sort.value === 'change') items = [...items].sort((a, b) => compareDecimal(b.change24hPercent, a.change24hPercent))
  if (sort.value === 'price') items = [...items].sort((a, b) => compareDecimal(b.buyPriceToman, a.buyPriceToman))
  return items
})

async function loadMarkets(): Promise<void> {
  try {
    await marketStore.fetchMarkets()
  } catch {
    // The store keeps a localized error and any last successfully loaded prices.
  }
}

onMounted(() => {
  void Promise.allSettled([
    loadMarkets(),
    walletStore.fetchWallet(),
    preferencesStore.hydrate(),
  ])
})
watch(() => route.query.q, (value) => {
  search.value = typeof value === 'string' ? value : ''
})
</script>

<template>
  <div class="page markets-page">
    <PageHeader title="ارزها" description="قیمت خرید از روشا و فروش به روشا، شفاف و بر پایه آخرین نرخ دریافتی" />
    <section v-if="marketStore.assets.length" class="market-snapshot" aria-label="نمای کلی بازار">
      <article><span class="snapshot-icon snapshot-icon--live"><i /></span><span><small>بازارهای فعال</small><strong>{{ tradableCount.toLocaleString('fa-IR') }} دارایی</strong></span></article>
      <article><span class="snapshot-icon"><AppIcon :name="Number(leadingMover?.change24hPercent || 0) >= 0 ? 'arrowUp' : 'arrowDown'" :size="18" /></span><span><small>بیشترین تغییر امروز</small><strong v-if="leadingMover">{{ leadingMover.nameFa }} <bdi dir="ltr">{{ formatPercentage(leadingMover.change24hPercent, { showSign: true }) }}</bdi></strong><strong v-else>—</strong></span></article>
      <article><span class="snapshot-icon snapshot-icon--gold"><AppIcon name="wallet" :size="18" /></span><span><small>دارایی‌های شما</small><strong>{{ heldAssetCount.toLocaleString('fa-IR') }} رمزارز</strong></span><RouterLink to="/app/wallet" aria-label="مشاهده کیف پول"><AppIcon name="chevronLeft" :size="17" /></RouterLink></article>
    </section>
    <AppCard class="markets-workspace" padding="none">
      <div class="market-toolbar">
        <AppTabs v-model="scope" :items="[{ label: 'همه ارزها', value: 'all' }, { label: 'علاقه‌مندی‌ها', value: 'favorites' }]" />
        <AppInput v-model="search" icon="search" type="search" inputmode="search" placeholder="نام یا نماد ارز…" />
        <AppSelect v-model="sort" :options="sortOptions" aria-label="مرتب‌سازی فهرست ارزها" />
      </div>
      <div v-if="!marketStore.loading && !marketStore.error && marketStore.assets.length" class="market-note">
        <span><i /> آخرین دریافت موفق: {{ marketStore.lastUpdated ? formatPersianDateTime(marketStore.lastUpdated) : 'همین حالا' }}</span>
        <span>اختلاف قیمت خرید و فروش، هزینه تأمین نقدشوندگی روشاست.</span>
      </div>
      <div v-else-if="!marketStore.loading && marketStore.error && marketStore.assets.length" class="market-note market-note--stale" role="status">
        <span><AppIcon name="warning" :size="15" /> قیمت‌های نمایش‌داده‌شده ممکن است قدیمی باشند.</span>
        <button type="button" @click="loadMarkets">دریافت دوباره</button>
      </div>
      <div v-if="marketStore.loading" class="skeleton-list"><AppSkeleton v-for="i in 5" :key="i" height="4.8rem" /></div>
      <div v-else-if="marketStore.error && !marketStore.assets.length" class="load-error" role="alert">
        <span><AppIcon name="warning" :size="25" /></span>
        <div><strong>قیمت ارزها بارگیری نشد</strong><p>{{ marketStore.error }}</p></div>
        <AppButton variant="secondary" size="sm" icon="refresh" @click="loadMarkets">تلاش دوباره</AppButton>
      </div>
      <MarketList v-else-if="filtered.length" :assets="filtered" :wallet="walletStore.summary || undefined" :favorites="preferencesStore.preferences.favoriteAssets" @toggle-favorite="preferencesStore.toggleFavorite" />
      <EmptyState
        v-else-if="marketStore.assets.length && hasFilters"
        icon="search"
        title="ارزی با این مشخصات پیدا نشد"
        description="نام فارسی یا نماد انگلیسی ارز را جست‌وجو کنید."
      ><button type="button" class="reset" @click="search = ''; scope = 'all'">پاک کردن فیلترها</button></EmptyState>
      <EmptyState v-else icon="wallet" title="فعلاً ارزی برای نمایش نیست" description="پس از دریافت فهرست قابل معامله، ارزها اینجا نمایش داده می‌شوند.">
        <AppButton variant="secondary" icon="refresh" @click="loadMarkets">دریافت دوباره</AppButton>
      </EmptyState>
    </AppCard>
  </div>
</template>

<style scoped>
.markets-page { max-width: 86rem; }
.market-snapshot { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: var(--space-3); margin-bottom: var(--space-5); }
.market-snapshot article { display: flex; min-width: 0; min-height: 4.75rem; align-items: center; gap: var(--space-3); padding: var(--space-3) var(--space-4); border: 1px solid var(--color-border); border-radius: var(--radius-lg); background: linear-gradient(135deg, var(--color-surface-1), color-mix(in srgb, var(--color-surface-2) 68%, transparent)); }
.market-snapshot article > span:nth-child(2) { display: grid; min-width: 0; flex: 1; }
.market-snapshot small { color: var(--color-text-muted); font-size: .68rem; }
.market-snapshot strong { min-width: 0; font-size: var(--font-size-sm); font-weight: 650; line-height: 1.5; overflow-wrap: anywhere; white-space: normal; }
.market-snapshot strong bdi { margin-inline-start: .3rem; color: var(--color-success); }
.market-snapshot article > a { display: grid; width: 2rem; height: 2rem; border-radius: var(--radius-sm); color: var(--color-text-muted); place-items: center; }
.snapshot-icon { display: grid; width: 2.65rem; height: 2.65rem; flex: 0 0 auto; border-radius: .82rem; background: var(--color-primary-soft); color: var(--color-primary); place-items: center; }
.snapshot-icon--live { background: var(--color-success-soft); }.snapshot-icon--live i { width: .55rem; height: .55rem; border-radius: 50%; background: var(--color-success); box-shadow: 0 0 0 .28rem color-mix(in srgb, var(--color-success-soft) 80%, transparent); }
.snapshot-icon--gold { background: var(--color-gold-soft); color: var(--color-gold); }
.markets-workspace { overflow: hidden; }
.market-toolbar { display: grid; grid-template-columns: auto minmax(15rem, 1fr) 12rem; align-items: end; gap: var(--space-3); padding: var(--space-5); }.market-toolbar :deep(.tabs) { min-width: 17rem; }.market-note { display: flex; align-items: center; justify-content: space-between; gap: var(--space-3); padding: .7rem var(--space-5); border-block: 1px solid var(--color-border-soft); background: var(--color-surface-2); color: var(--color-text-muted); font-size: var(--font-size-xs); }.market-note span:first-child { display: inline-flex; align-items: center; gap: var(--space-2); color: var(--color-success); }.market-note i { width: .4rem; height: .4rem; border-radius: 50%; background: var(--color-success); }.market-note--stale { background: var(--color-warning-soft); }.market-note--stale span:first-child { color: var(--color-warning); }.market-note--stale button { min-height: 2rem; padding-inline: var(--space-3); border: 1px solid currentColor; border-radius: var(--radius-pill); background: transparent; color: var(--color-warning); font-size: var(--font-size-xs); }.load-error { display: flex; align-items: center; gap: var(--space-4); padding: var(--space-8); }.load-error > span { display: grid; width: 3rem; height: 3rem; flex: 0 0 auto; border-radius: 1rem; background: var(--color-danger-soft); color: var(--color-danger); place-items: center; }.load-error > div { flex: 1; }.load-error p { margin: .15rem 0 0; color: var(--color-text-muted); font-size: var(--font-size-sm); }.skeleton-list { display: grid; gap: 1px; padding: var(--space-3); }.reset { min-height: 2.5rem; padding-inline: var(--space-4); border: 1px solid var(--color-border); border-radius: var(--radius-sm); background: var(--color-surface-2); color: var(--color-primary); }
@media (max-width: 960px) { .market-toolbar { grid-template-columns: 1fr 1fr; }.market-toolbar :deep(.tabs) { grid-column: 1 / -1; min-width: 0; } }
@media (max-width: 767px) { .market-snapshot { grid-template-columns: 1fr 1fr; gap: var(--space-2); margin-bottom: var(--space-4); }.market-snapshot article { min-height: 4.25rem; padding: var(--space-3); }.market-snapshot article:last-child { grid-column: 1 / -1; }.snapshot-icon { width: 2.3rem; height: 2.3rem; }.market-toolbar { grid-template-columns: 1fr; padding: var(--space-4); }.market-toolbar :deep(.tabs) { grid-column: auto; }.market-note:not(.market-note--stale) span:last-child { display: none; }.market-note { justify-content: center; padding-inline: var(--space-4); }.market-note--stale { justify-content: space-between; }.load-error { align-items: flex-start; flex-wrap: wrap; padding: var(--space-5); }.load-error > div { min-width: calc(100% - 4rem); }.markets-workspace { border-inline: 0; border-radius: var(--radius-xl); }.markets-page > :deep(.app-card) { box-shadow: none; } }
@media (max-width: 380px) { .market-snapshot { grid-template-columns: 1fr; }.market-snapshot article:last-child { grid-column: auto; } }
</style>
