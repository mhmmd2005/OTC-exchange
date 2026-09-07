<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import type { AssetNetwork, Transaction } from '@/types'
import { transactionService } from '@/services/transaction.service'
import { useWalletStore } from '@/stores/wallet'
import { formatCrypto, formatToman, toPersianDigits } from '@/utils/formatters'
import AppButton from '@/components/ui/AppButton.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import AssetAvatar from '@/components/finance/AssetAvatar.vue'
import TransactionList from '@/components/transactions/TransactionList.vue'

const route = useRoute()
const walletStore = useWalletStore()
const transactions = ref<Transaction[]>([])
const loading = ref(true)
const error = ref('')
let loadSequence = 0

const symbol = computed(() => String(route.params.symbol || 'IRT').toUpperCase())
const asset = computed(() => walletStore.getAsset(symbol.value))
const isToman = computed(() => symbol.value === 'IRT')

function networkStatusLabel(network: AssetNetwork): string {
  if (network.status === 'active') return 'فعال'
  if (network.status === 'congested') return 'شبکه شلوغ'
  if (network.status === 'maintenance') return 'در حال به‌روزرسانی'
  return 'غیرفعال'
}

async function load() {
  const requestId = ++loadSequence
  loading.value = true
  error.value = ''
  try {
    await walletStore.fetchWallet()
    if (!walletStore.getAsset(symbol.value)) return
    const result = await transactionService.list({ assetSymbol: symbol.value, pageSize: 6 })
    if (requestId === loadSequence) transactions.value = result.items
  } catch (caught) {
    if (requestId === loadSequence) {
      error.value = caught instanceof Error ? caught.message : 'اطلاعات این کیف پول دریافت نشد.'
    }
  } finally {
    if (requestId === loadSequence) loading.value = false
  }
}

watch(symbol, load, { immediate: true })
</script>

<template>
  <div class="page wallet-detail-page">
    <PageHeader
      :title="asset ? `کیف پول ${asset.nameFa}` : 'جزئیات کیف پول'"
      :description="asset ? `${asset.nameEn} · ${asset.symbol}` : 'موجودی و گردش این دارایی'"
      back-to="/app/wallet"
    />

    <div v-if="loading && !asset" class="detail-skeleton">
      <AppSkeleton height="18rem" radius="var(--radius-xl)" />
      <AppSkeleton height="18rem" radius="var(--radius-xl)" />
    </div>

    <template v-else-if="asset">
      <div class="balance-layout">
        <AppCard class="balance-card" padding="lg">
          <div class="balance-heading">
            <AssetAvatar :symbol="asset.symbol" :color="asset.color" size="lg" />
            <div><small>کل موجودی</small><strong><span v-if="isToman">{{ formatToman(asset.total) }}</span><bdi v-else dir="ltr">{{ formatCrypto(asset.total, { symbol: asset.symbol }) }}</bdi></strong></div>
          </div>
          <p class="balance-equivalent" v-if="!isToman">ارزش روز: {{ formatToman(asset.tomanValue) }}</p>
          <div class="balance-split">
            <div><span>موجودی قابل برداشت</span><strong><span v-if="isToman">{{ formatToman(asset.available) }}</span><bdi v-else dir="ltr">{{ formatCrypto(asset.available, { symbol: asset.symbol }) }}</bdi></strong></div>
            <div><span>مبلغ مسدود</span><strong><span v-if="isToman">{{ formatToman(asset.locked) }}</span><bdi v-else dir="ltr">{{ formatCrypto(asset.locked, { symbol: asset.symbol }) }}</bdi></strong></div>
          </div>
        </AppCard>

        <AppCard class="actions-card" padding="lg">
          <div class="actions-heading"><span><AppIcon name="wallet" :size="23" /></span><div><h2>چه کاری می‌خواهید انجام دهید؟</h2><p>عملیات در دسترس برای این کیف پول</p></div></div>
          <div v-if="isToman" class="wallet-actions two">
            <AppButton block to="/app/deposit/toman" icon="download">واریز تومان</AppButton>
            <AppButton block variant="secondary" to="/app/withdraw/toman" icon="upload">برداشت تومان</AppButton>
          </div>
          <div v-else class="wallet-actions">
            <AppButton v-if="asset.buyEnabled" block :to="`/app/trade?side=buy&asset=${asset.symbol}`">خرید</AppButton>
            <AppButton v-if="asset.sellEnabled" block variant="secondary" :to="`/app/trade?side=sell&asset=${asset.symbol}`">فروش</AppButton>
            <AppButton block variant="ghost" :disabled="!asset.depositEnabled" :to="asset.depositEnabled ? `/app/deposit/crypto/${asset.symbol}` : undefined">واریز</AppButton>
            <AppButton block variant="ghost" :disabled="!asset.withdrawalEnabled" :to="asset.withdrawalEnabled ? `/app/withdraw/crypto/${asset.symbol}` : undefined">برداشت</AppButton>
          </div>
          <div class="safety-note"><AppIcon name="shield" :size="18" /><span>تمام برداشت‌ها با کنترل‌های امنیتی حساب شما محافظت می‌شوند.</span></div>
        </AppCard>
      </div>

      <AppCard v-if="!isToman && asset.networks.length" class="network-card" padding="none">
        <div class="card-heading"><div><h2>شبکه‌های پشتیبانی‌شده</h2><p>کارمزد و زمان پردازش هر شبکه پیش از برداشت نمایش داده می‌شود.</p></div></div>
        <div class="network-grid">
          <article v-for="network in asset.networks" :key="network.id" class="network-item" :class="network.status">
            <div class="network-title"><span><strong>{{ network.displayName }}</strong><bdi dir="ltr">{{ network.code }}</bdi></span><em>{{ networkStatusLabel(network) }}</em></div>
            <dl>
              <div><dt>زمان تقریبی</dt><dd>{{ toPersianDigits(network.estimatedArrivalMinutes) }} دقیقه</dd></div>
              <div><dt>تأیید شبکه</dt><dd>{{ toPersianDigits(network.confirmations) }} تأیید</dd></div>
              <div><dt>کارمزد برداشت</dt><dd><bdi dir="ltr">{{ formatCrypto(network.withdrawalFee, { symbol: asset.symbol }) }}</bdi></dd></div>
            </dl>
          </article>
        </div>
      </AppCard>

      <AppCard class="transactions-card" padding="none">
        <div class="card-heading"><div><h2>گردش اخیر {{ asset.nameFa }}</h2><p>واریز، برداشت و معامله‌های این دارایی</p></div><RouterLink :to="{ path: '/app/transactions', query: { asset: asset.symbol } }">همه تراکنش‌ها <AppIcon name="chevronLeft" :size="16" /></RouterLink></div>
        <TransactionList v-if="transactions.length" :transactions="transactions" />
        <EmptyState v-else icon="transactions" title="هنوز تراکنشی ثبت نشده" description="اولین فعالیت این کیف پول در این بخش نمایش داده می‌شود." />
      </AppCard>

      <div v-if="error" class="inline-error" role="alert"><AppIcon name="warning" :size="18" />{{ error }}<button type="button" @click="load">تلاش دوباره</button></div>
    </template>

    <AppCard v-else>
      <EmptyState icon="wallet" title="این کیف پول پیدا نشد" description="دارایی مورد نظر در فهرست کیف پول شما وجود ندارد.">
        <AppButton to="/app/wallet">بازگشت به کیف پول</AppButton>
      </EmptyState>
    </AppCard>
  </div>
</template>

<style scoped>
.wallet-detail-page { max-width: 78rem; }
.balance-layout { display: grid; grid-template-columns: minmax(0, 1.15fr) minmax(22rem, .85fr); gap: var(--space-5); }
.balance-card { position: relative; overflow: hidden; background: linear-gradient(145deg, var(--color-surface-1), rgba(67,139,255,.08)); }
.balance-card::after { position: absolute; inset-block-start: -7rem; inset-inline-end: -5rem; width: 18rem; height: 18rem; border-radius: 50%; background: radial-gradient(circle, rgba(67,139,255,.12), transparent 68%); content: ''; pointer-events: none; }
.balance-heading { position: relative; z-index: 1; display: flex; align-items: center; gap: var(--space-4); }
.balance-heading > div { display: grid; min-width: 0; }
.balance-heading small, .balance-equivalent { color: var(--color-text-muted); font-size: var(--font-size-sm); }
.balance-heading strong { min-width: 0; margin-top: .15rem; font-size: clamp(1.45rem, 4vw, 2rem); line-height: 1.45; overflow-wrap: anywhere; white-space: normal; }
.balance-heading bdi, .balance-split bdi, .network-item dd bdi { unicode-bidi: isolate; }
.balance-equivalent { position: relative; z-index: 1; margin: var(--space-2) 4.65rem 0 0; }
.balance-split { position: relative; z-index: 1; display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-3); margin-top: var(--space-7); padding-top: var(--space-5); border-block-start: 1px solid var(--color-border-soft); }
.balance-split div { display: grid; gap: .25rem; min-width: 0; }
.balance-split span { color: var(--color-text-muted); font-size: var(--font-size-xs); }
.balance-split strong { min-width: 0; font-size: var(--font-size-sm); line-height: 1.5; overflow-wrap: anywhere; white-space: normal; }
.actions-card { display: flex; flex-direction: column; }
.actions-heading { display: flex; align-items: center; gap: var(--space-3); }
.actions-heading > span { display: grid; width: 2.85rem; height: 2.85rem; border-radius: .85rem; background: var(--color-primary-soft); color: var(--color-primary); place-items: center; }
.actions-heading h2 { margin: 0; font-size: var(--font-size-md); }
.actions-heading p { margin: .1rem 0 0; color: var(--color-text-muted); font-size: var(--font-size-xs); }
.wallet-actions { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-2); margin-top: var(--space-5); }
.wallet-actions.two { margin-block: auto; padding-block: var(--space-5); }
.safety-note { display: flex; align-items: center; gap: var(--space-2); margin-top: auto; padding-top: var(--space-4); color: var(--color-text-muted); font-size: var(--font-size-xs); }
.safety-note :deep(svg) { flex: 0 0 auto; color: var(--color-success); }
.network-card, .transactions-card { margin-top: var(--space-5); overflow: hidden; }
.card-heading { display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); padding: var(--space-5); border-block-end: 1px solid var(--color-border-soft); }
.card-heading h2 { margin: 0; font-size: var(--font-size-lg); }
.card-heading p { margin: .15rem 0 0; color: var(--color-text-muted); font-size: var(--font-size-xs); }
.card-heading a { display: inline-flex; align-items: center; gap: .25rem; color: var(--color-primary); font-size: var(--font-size-xs); font-weight: 600; white-space: nowrap; }
.network-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(18rem, 1fr)); gap: var(--space-3); padding: var(--space-5); }
.network-item { padding: var(--space-4); border: 1px solid var(--color-border-soft); border-radius: var(--radius-lg); background: var(--color-surface-2); }
.network-item.maintenance, .network-item.disabled { opacity: .65; }
.network-title, .network-title > span { display: flex; align-items: center; justify-content: space-between; gap: var(--space-2); }
.network-title > span { justify-content: flex-start; }
.network-title strong { font-size: var(--font-size-sm); }
.network-title bdi { color: var(--color-text-muted); font-size: var(--font-size-xs); }
.network-title em { padding: .15rem .5rem; border-radius: var(--radius-pill); background: var(--color-success-soft); color: var(--color-success); font-size: .67rem; font-style: normal; }
.network-item.congested .network-title em, .network-item.maintenance .network-title em { background: var(--color-warning-soft); color: var(--color-warning); }
.network-item.disabled .network-title em { background: var(--color-danger-soft); color: var(--color-danger); }
.network-item dl { display: grid; gap: var(--space-2); margin: var(--space-4) 0 0; }
.network-item dl div { display: flex; justify-content: space-between; gap: var(--space-3); }
.network-item dt { color: var(--color-text-muted); font-size: var(--font-size-xs); }
.network-item dd { min-width: 0; max-width: 64%; margin: 0; font-size: var(--font-size-xs); font-weight: 500; text-align: end; overflow-wrap: anywhere; white-space: normal; }
.inline-error { display: flex; align-items: center; gap: var(--space-2); margin-top: var(--space-4); padding: var(--space-3) var(--space-4); border: 1px solid rgba(240,108,117,.2); border-radius: var(--radius-md); background: var(--color-danger-soft); color: var(--color-danger); }
.inline-error button { margin-inline-start: auto; border: 0; background: transparent; color: inherit; font-weight: 600; text-decoration: underline; }
.detail-skeleton { display: grid; grid-template-columns: 1.15fr .85fr; gap: var(--space-5); }
@media (max-width: 900px) { .balance-layout, .detail-skeleton { grid-template-columns: 1fr; } }
@media (max-width: 767px) { .card-heading, .network-grid { padding: var(--space-4); } .card-heading p { display: none; } .network-grid { grid-template-columns: 1fr; } }
@media (max-width: 420px) { .balance-split { grid-template-columns: 1fr; } .wallet-actions { gap: var(--space-2); } .balance-equivalent { margin-inline-start: 0; } }
</style>
