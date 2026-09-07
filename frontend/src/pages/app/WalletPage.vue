<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { compareDecimal } from '@/utils/decimal'
import { formatRelativeTime } from '@/utils/formatters'
import { usePreferencesStore } from '@/stores/preferences'
import { useWalletStore } from '@/stores/wallet'
import AppButton from '@/components/ui/AppButton.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import AppInput from '@/components/ui/AppInput.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import PortfolioSummary from '@/components/finance/PortfolioSummary.vue'
import QuickActions from '@/components/finance/QuickActions.vue'
import WalletAssetList from '@/components/wallet/WalletAssetList.vue'

const walletStore = useWalletStore()
const preferencesStore = usePreferencesStore()
const search = ref('')

const balancesHidden = computed(() => preferencesStore.hideBalances)
const hideZeroBalances = computed(() => preferencesStore.hideZeroBalances)
const fundedAssetCount = computed(() => walletStore.assets.filter((asset) => compareDecimal(asset.total, '0') > 0).length)
const filteredAssets = computed(() => {
  const query = search.value.trim().toLocaleLowerCase('fa')
  return walletStore.assets.filter((asset) => {
    const matchesSearch = !query
      || asset.nameFa.toLocaleLowerCase('fa').includes(query)
      || asset.nameEn.toLowerCase().includes(query)
      || asset.symbol.toLowerCase().includes(query)
    const hasBalance = compareDecimal(asset.total, '0') !== 0
    return matchesSearch && (!hideZeroBalances.value || hasBalance)
  })
})

const updatedLabel = computed(() => walletStore.lastUpdated
  ? `آخرین به‌روزرسانی: ${formatRelativeTime(walletStore.lastUpdated)}`
  : undefined)

async function load(force = false) {
  await Promise.all([
    walletStore.fetchWallet(force),
    preferencesStore.hydrate(),
  ])
}

onMounted(() => load())
</script>

<template>
  <div class="page wallet-page">
    <PageHeader title="کیف پول" description="مدیریت یکپارچه موجودی تومان و رمزارزهای شما">
      <template #actions>
        <AppButton
          variant="secondary"
          size="sm"
          icon="refresh"
          :loading="walletStore.loading"
          @click="load(true)"
        >به‌روزرسانی</AppButton>
      </template>
    </PageHeader>

    <div v-if="walletStore.loading && !walletStore.summary" class="wallet-skeleton" aria-label="در حال دریافت کیف پول">
      <AppSkeleton height="17rem" radius="var(--radius-xl)" />
      <AppSkeleton height="8rem" radius="var(--radius-xl)" />
      <AppSkeleton height="28rem" radius="var(--radius-xl)" />
    </div>

    <template v-else-if="walletStore.summary">
      <div class="wallet-hero">
        <PortfolioSummary
          :total="walletStore.summary.totalValueToman"
          :toman="walletStore.summary.tomanBalance"
          :crypto="walletStore.summary.cryptoValueToman"
          :hidden="balancesHidden"
          :updated-label="updatedLabel"
          @toggle="preferencesStore.toggleBalances()"
        />
        <section class="wallet-shortcuts">
          <div class="section-heading">
            <div><span class="section-kicker">دسترسی سریع</span><h2>عملیات کیف پول</h2><p>واریز و برداشت با چند مرحله شفاف</p></div>
            <span class="secure"><AppIcon name="shield" :size="16" /> امن</span>
          </div>
          <QuickActions />
          <p class="security-note"><AppIcon name="info" :size="17" /> برداشت‌ها پیش از ارسال با کد یک‌بارمصرف تأیید می‌شوند.</p>
        </section>
      </div>

      <div class="wallet-assurance" role="note">
        <span><i class="live-dot" /><strong>{{ fundedAssetCount.toLocaleString('fa-IR') }}</strong> دارایی دارای موجودی</span>
        <span><AppIcon name="lock" :size="16" />برداشت امن با تأیید دومرحله‌ای</span>
        <RouterLink to="/app/transactions">مشاهده گردش حساب <AppIcon name="chevronLeft" :size="15" /></RouterLink>
      </div>

      <AppCard class="assets-card" padding="none">
        <div class="assets-toolbar">
          <div class="assets-title"><span class="assets-title__icon"><AppIcon name="wallet" :size="20" /></span><span><h2>دارایی‌ها</h2><p>{{ filteredAssets.length.toLocaleString('fa-IR') }} دارایی · برای مشاهده جزئیات انتخاب کنید</p></span></div>
          <div class="toolbar-actions">
            <AppInput v-model="search" class="asset-search" placeholder="جست‌وجوی ارز" inputmode="search" icon="search" />
            <label class="zero-filter">
              <input
                type="checkbox"
                :checked="hideZeroBalances"
                @change="preferencesStore.toggleZeroBalances()"
              >
              <span aria-hidden="true"><i /></span>
              مخفی کردن دارایی‌های صفر
            </label>
          </div>
        </div>

        <WalletAssetList
          v-if="filteredAssets.length"
          :assets="filteredAssets"
          :hidden="balancesHidden"
        />
        <EmptyState
          v-else
          icon="search"
          title="دارایی‌ای پیدا نشد"
          description="عبارت جست‌وجو یا فیلتر موجودی صفر را تغییر دهید."
        >
          <AppButton variant="secondary" size="sm" @click="search = ''; hideZeroBalances && preferencesStore.toggleZeroBalances()">پاک کردن فیلترها</AppButton>
        </EmptyState>
      </AppCard>
    </template>

    <AppCard v-else class="wallet-error">
      <EmptyState icon="warning" title="کیف پول بارگیری نشد" :description="walletStore.error || 'اتصال خود را بررسی کنید و دوباره تلاش کنید.'">
        <AppButton @click="load(true)">تلاش دوباره</AppButton>
      </EmptyState>
    </AppCard>
  </div>
</template>

<style scoped>
.wallet-page { max-width: 84rem; }
.wallet-hero { display: grid; grid-template-columns: minmax(22rem, .9fr) minmax(28rem, 1.1fr); align-items: stretch; gap: var(--space-5); }
.wallet-shortcuts { position: relative; display: flex; overflow: hidden; flex-direction: column; justify-content: center; padding: var(--space-6); border: 1px solid var(--color-border); border-radius: var(--radius-xl); background: linear-gradient(145deg, var(--color-surface-1), color-mix(in srgb, var(--color-primary-soft) 38%, var(--color-surface-1))); box-shadow: var(--shadow-sm); }
.wallet-shortcuts :deep(.quick-actions) { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.wallet-shortcuts::after { position: absolute; inset: -5rem auto auto -5rem; width: 11rem; height: 11rem; border: 1px solid color-mix(in srgb, var(--color-gold) 12%, transparent); border-radius: 50%; content: ''; pointer-events: none; }
.section-heading { display: flex; align-items: start; justify-content: space-between; gap: var(--space-4); margin-bottom: var(--space-5); }
.section-heading h2, .assets-toolbar h2 { margin: 0; font-size: var(--font-size-lg); }
.section-heading p, .assets-toolbar p { margin: .15rem 0 0; color: var(--color-text-muted); font-size: var(--font-size-xs); }
.section-kicker { display: block; margin-bottom: .15rem; color: var(--color-primary); font-size: .67rem; font-weight: 650; letter-spacing: .02em; }
.secure { display: inline-flex; align-items: center; gap: .3rem; padding: .25rem .6rem; border-radius: var(--radius-pill); background: var(--color-success-soft); color: var(--color-success); font-size: var(--font-size-xs); }
.security-note { display: flex; align-items: center; gap: var(--space-2); margin: var(--space-5) 0 0; color: var(--color-text-muted); font-size: var(--font-size-xs); }
.security-note :deep(svg) { flex: 0 0 auto; color: var(--color-info); }
.wallet-assurance { display: flex; min-height: 3.25rem; align-items: center; gap: var(--space-5); margin-top: var(--space-4); padding-inline: var(--space-5); border: 1px solid var(--color-border-soft); border-radius: var(--radius-lg); background: color-mix(in srgb, var(--color-surface-2) 72%, transparent); color: var(--color-text-muted); font-size: var(--font-size-xs); }
.wallet-assurance > span { display: inline-flex; align-items: center; gap: var(--space-2); }
.wallet-assurance strong { color: var(--color-text-primary); font-size: var(--font-size-sm); }
.wallet-assurance svg { color: var(--color-success); }
.wallet-assurance a { display: inline-flex; align-items: center; gap: .2rem; margin-inline-start: auto; color: var(--color-primary); font-weight: 600; }
.wallet-assurance a svg { color: currentColor; }
.live-dot { width: .42rem; height: .42rem; border-radius: 50%; background: var(--color-success); box-shadow: 0 0 0 .22rem var(--color-success-soft); }
.assets-card { margin-top: var(--space-5); overflow: hidden; }
.assets-toolbar { display: flex; align-items: center; justify-content: space-between; gap: var(--space-5); padding: var(--space-5); border-block-end: 1px solid var(--color-border-soft); }
.assets-title { display: flex; align-items: center; gap: var(--space-3); }
.assets-title > span:last-child { display: grid; }
.assets-title__icon { display: grid; width: 2.7rem; height: 2.7rem; border: 1px solid color-mix(in srgb, var(--color-primary) 20%, transparent); border-radius: .85rem; background: var(--color-primary-soft); color: var(--color-primary); place-items: center; }
.toolbar-actions { display: flex; align-items: center; gap: var(--space-4); }
.asset-search { width: min(20rem, 32vw); }
.asset-search :deep(.field__control) { min-height: var(--control-height-sm); }
.asset-search :deep(input) { height: 2.25rem; }
.zero-filter { display: inline-flex; align-items: center; gap: var(--space-2); color: var(--color-text-secondary); font-size: var(--font-size-xs); white-space: nowrap; cursor: pointer; }
.zero-filter input { position: absolute; width: 1px; height: 1px; opacity: 0; }
.zero-filter > span { position: relative; width: 2.35rem; height: 1.35rem; border: 1px solid var(--color-border-hover); border-radius: var(--radius-pill); background: var(--color-surface-3); transition: background var(--transition-fast), border-color var(--transition-fast); }
.zero-filter i { position: absolute; inset-block-start: .15rem; inset-inline-start: .15rem; width: .95rem; height: .95rem; border-radius: 50%; background: var(--color-text-muted); transition: transform var(--transition-fast), background var(--transition-fast); }
.zero-filter input:checked + span { border-color: var(--color-primary); background: var(--color-primary-soft); }
.zero-filter input:checked + span i { background: var(--color-primary); transform: translateX(-1rem); }
.zero-filter input:focus-visible + span { outline: 2px solid var(--color-border-focus); outline-offset: 3px; box-shadow: var(--shadow-focus); }
.wallet-skeleton { display: grid; grid-template-columns: minmax(22rem, .9fr) minmax(28rem, 1.1fr); gap: var(--space-5); }
.wallet-skeleton > :last-child { grid-column: 1 / -1; }
@media (max-width: 980px) { .wallet-hero, .wallet-skeleton { grid-template-columns: 1fr; } .wallet-skeleton > :last-child { grid-column: auto; } }
@media (max-width: 900px) {
  .assets-toolbar { align-items: stretch; flex-direction: column; gap: var(--space-4); }
  .toolbar-actions { width: 100%; justify-content: space-between; }
  .asset-search { width: min(100%, 28rem); flex: 1; }
}
@media (max-width: 767px) {
  .wallet-page :deep(.page-header p) { display: none; }
  .wallet-hero :deep(.portfolio) { min-width: 0; }
  .wallet-hero :deep(.portfolio header button) { width: 2.75rem; height: 2.75rem; }
  .wallet-hero :deep(.portfolio__value), .wallet-hero :deep(.portfolio__value bdi) { min-width: 0; max-width: 100%; overflow-wrap: anywhere; }
  .wallet-hero :deep(.portfolio__split > div) { min-width: 0; }
  .wallet-hero :deep(.portfolio__split strong), .wallet-hero :deep(.portfolio__split bdi) { min-width: 0; overflow-wrap: anywhere; }
  .wallet-shortcuts { padding: var(--space-4); }
  .wallet-hero { gap: var(--space-4); }
  .wallet-assurance { display: grid; grid-template-columns: 1fr auto; gap: var(--space-2); min-height: auto; padding: var(--space-3) var(--space-4); }
  .wallet-assurance > span:nth-child(2) { display: none; }
  .wallet-assurance a { margin: 0; }
  .assets-card { margin-top: var(--space-4); }
  .assets-toolbar { padding: var(--space-4); }
  .toolbar-actions { align-items: stretch; flex-direction: column; gap: var(--space-3); }
  .asset-search { width: 100%; }
  .zero-filter { min-height: 2.75rem; }
}
@media (max-width: 420px) {
  .section-heading p, .security-note { display: none; }
  .wallet-shortcuts :deep(.quick-actions) { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .wallet-assurance { grid-template-columns: 1fr; }
  .wallet-assurance a { min-height: 2.75rem; justify-self: start; }
  .assets-toolbar { gap: var(--space-4); padding-inline: var(--space-3); }
  .assets-title { align-items: flex-start; }
  .assets-title p { max-width: 14rem; line-height: 1.65; }
}
</style>
