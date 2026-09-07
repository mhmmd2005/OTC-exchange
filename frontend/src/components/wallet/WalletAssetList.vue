<script setup lang="ts">
import type { WalletAsset } from '@/types'
import { compareDecimal } from '@/utils/decimal'
import AppIcon from '@/components/ui/AppIcon.vue'
import AssetAvatar from '@/components/finance/AssetAvatar.vue'
import CryptoValue from '@/components/finance/CryptoValue.vue'
import MoneyValue from '@/components/finance/MoneyValue.vue'

defineProps<{ assets: WalletAsset[]; hidden?: boolean; compact?: boolean }>()

function isLocked(asset: WalletAsset): boolean {
  return compareDecimal(asset.locked, '0') > 0
}

function assetActionCount(asset: WalletAsset): number {
  if (asset.symbol === 'IRT') return 2
  return [asset.buyEnabled, asset.sellEnabled, asset.depositEnabled, asset.withdrawalEnabled]
    .filter(Boolean).length
}
</script>

<template>
  <div class="wallet-assets" :class="{ compact }">
    <table class="asset-table desktop-only">
      <caption class="sr-only">موجودی و امکانات دارایی‌های کیف پول</caption>
      <colgroup><col class="column-identity"><col class="column-total"><col class="column-available priority-secondary"><col class="column-locked priority-secondary"><col class="column-toman"><col class="column-actions"></colgroup>
      <thead><tr><th scope="col">دارایی</th><th scope="col">موجودی کل</th><th scope="col" class="priority-secondary">قابل برداشت</th><th scope="col" class="priority-secondary">مسدود</th><th scope="col">ارزش روز</th><th scope="col">عملیات</th></tr></thead>
      <tbody>
      <tr v-for="asset in assets" :key="asset.symbol" class="asset-row">
        <th scope="row"><RouterLink :to="`/app/wallet/${asset.symbol}`" class="asset-identity">
          <AssetAvatar :symbol="asset.symbol" :color="asset.color" />
          <span><strong>{{ asset.nameFa }}</strong><small dir="ltr">{{ asset.nameEn }} · {{ asset.symbol }}</small></span>
        </RouterLink></th>
        <td class="asset-value asset-value--primary"><MoneyValue v-if="asset.symbol === 'IRT'" :value="asset.total" label="کل موجودی" :hidden="hidden" /><CryptoValue v-else :value="asset.total" :symbol="asset.symbol" label="کل موجودی" :hidden="hidden" /></td>
        <td class="asset-value priority-secondary"><MoneyValue v-if="asset.symbol === 'IRT'" :value="asset.available" label="آماده استفاده" :hidden="hidden" /><CryptoValue v-else :value="asset.available" :symbol="asset.symbol" label="آماده استفاده" :hidden="hidden" /></td>
        <td class="asset-value priority-secondary" :class="{ 'has-lock': isLocked(asset) }"><MoneyValue v-if="asset.symbol === 'IRT'" :value="asset.locked" :label="isLocked(asset) ? 'در سفارش یا برداشت' : 'بدون مبلغ مسدود'" :hidden="hidden" /><CryptoValue v-else :value="asset.locked" :symbol="asset.symbol" :label="isLocked(asset) ? 'در سفارش یا برداشت' : 'بدون مبلغ مسدود'" :hidden="hidden" /></td>
        <td class="asset-value asset-value--toman"><MoneyValue :value="asset.tomanValue" :label="asset.symbol === 'IRT' ? 'موجودی ریالی' : 'معادل تومان'" :hidden="hidden" /></td>
        <td><nav class="asset-actions" :aria-label="`عملیات ${asset.nameFa}`">
          <template v-if="asset.symbol === 'IRT'">
            <RouterLink class="asset-action--primary" to="/app/deposit/toman">واریز</RouterLink>
            <RouterLink to="/app/withdraw/toman">برداشت</RouterLink>
          </template>
          <template v-else>
            <RouterLink v-if="asset.buyEnabled" class="asset-action--primary" :to="`/app/trade?side=buy&asset=${asset.symbol}`">خرید</RouterLink>
            <RouterLink v-if="asset.sellEnabled" :to="`/app/trade?side=sell&asset=${asset.symbol}`">فروش</RouterLink>
            <RouterLink v-if="!compact && asset.depositEnabled" :to="`/app/deposit/crypto/${asset.symbol}`">واریز</RouterLink>
            <RouterLink v-if="!compact && asset.withdrawalEnabled" :to="`/app/withdraw/crypto/${asset.symbol}`">برداشت</RouterLink>
          </template>
          <RouterLink :to="`/app/wallet/${asset.symbol}`" class="asset-more" aria-label="جزئیات کیف پول"><AppIcon name="chevronLeft" :size="17" /></RouterLink>
        </nav></td>
      </tr>
      </tbody>
    </table>

    <div class="asset-mobile mobile-only">
      <article v-for="asset in assets" :key="asset.symbol" class="asset-card">
        <RouterLink
          :to="`/app/wallet/${asset.symbol}`"
          class="asset-card__top"
          :aria-label="`مشاهده جزئیات کیف پول ${asset.nameFa}`"
        >
          <span class="asset-card__identity">
            <AssetAvatar :symbol="asset.symbol" :color="asset.color" />
            <span class="asset-identity__copy"><strong>{{ asset.nameFa }}</strong><small dir="ltr">{{ asset.nameEn }} · {{ asset.symbol }}</small></span>
          </span>
          <span class="asset-card__detail">جزئیات <AppIcon name="chevronLeft" :size="17" /></span>
        </RouterLink>

        <div class="asset-card__balance">
          <MoneyValue v-if="asset.symbol === 'IRT'" class="asset-card__primary-value" :value="asset.total" label="موجودی کل" :hidden="hidden" />
          <CryptoValue v-else class="asset-card__primary-value" :value="asset.total" :symbol="asset.symbol" label="موجودی کل" :hidden="hidden" />
          <MoneyValue class="asset-card__equivalent" :value="asset.tomanValue" :label="asset.symbol === 'IRT' ? 'ارزش موجودی' : 'معادل تومان'" :hidden="hidden" />
        </div>

        <div class="asset-card__metrics">
          <span><MoneyValue v-if="asset.symbol === 'IRT'" :value="asset.available" label="قابل استفاده" :hidden="hidden" /><CryptoValue v-else :value="asset.available" :symbol="asset.symbol" label="قابل استفاده" :hidden="hidden" /></span>
          <span :class="{ 'has-lock': isLocked(asset) }"><MoneyValue v-if="asset.symbol === 'IRT'" :value="asset.locked" label="مسدود" :hidden="hidden" /><CryptoValue v-else :value="asset.locked" :symbol="asset.symbol" label="مسدود" :hidden="hidden" /></span>
        </div>
        <nav
          v-if="!compact && assetActionCount(asset)"
          class="asset-card__actions"
          :class="`asset-card__actions--${assetActionCount(asset)}`"
          :aria-label="`عملیات ${asset.nameFa}`"
        >
          <template v-if="asset.symbol === 'IRT'">
            <RouterLink to="/app/deposit/toman"><AppIcon name="download" :size="17" />واریز</RouterLink>
            <RouterLink to="/app/withdraw/toman"><AppIcon name="upload" :size="17" />برداشت</RouterLink>
          </template>
          <template v-else>
            <RouterLink v-if="asset.buyEnabled" :to="`/app/trade?side=buy&asset=${asset.symbol}`"><AppIcon name="plus" :size="17" />خرید</RouterLink>
            <RouterLink v-if="asset.sellEnabled" :to="`/app/trade?side=sell&asset=${asset.symbol}`"><AppIcon name="minus" :size="17" />فروش</RouterLink>
            <RouterLink v-if="asset.depositEnabled" :to="`/app/deposit/crypto/${asset.symbol}`"><AppIcon name="arrowDown" :size="17" />واریز</RouterLink>
            <RouterLink v-if="asset.withdrawalEnabled" :to="`/app/withdraw/crypto/${asset.symbol}`"><AppIcon name="arrowUp" :size="17" />برداشت</RouterLink>
          </template>
        </nav>
      </article>
    </div>
  </div>
</template>

<style scoped>
.wallet-assets { width: 100%; max-width: 100%; min-width: 0; container: wallet-data / inline-size; }
.asset-table { width: 100%; border-collapse: collapse; table-layout: fixed; }
.column-identity { width: 18%; }.column-total, .column-available { width: 15%; }.column-locked { width: 13%; }.column-toman { width: 16%; }.column-actions { width: 23%; }
.asset-table th { font-weight: inherit; text-align: start; }
.asset-table thead th { height: 2.9rem; padding-inline: var(--space-5); border-block-end: 1px solid var(--color-border); background: color-mix(in srgb, var(--color-surface-2) 70%, transparent); color: var(--color-text-muted); font-size: var(--font-size-xs); font-weight: 500; white-space: nowrap; }
.asset-table tbody th, .asset-table tbody td { height: 5.55rem; padding: .8rem var(--space-5); border-block-end: 1px solid var(--color-border-soft); vertical-align: middle; transition: background var(--transition-fast); }
.asset-table tbody tr:last-child > * { border-block-end: 0; }
.asset-table tbody tr:hover > * { background: var(--color-surface-2); }
.asset-identity { display: flex; min-width: 0; align-items: center; gap: var(--space-3); }
.asset-identity > span, .asset-identity__copy { display: grid; min-width: 0; line-height: 1.38; }
.asset-identity strong, .asset-identity__copy strong { overflow: hidden; font-size: var(--font-size-sm); font-weight: 650; text-overflow: ellipsis; white-space: nowrap; }
.asset-identity small, .asset-identity__copy small { overflow: hidden; color: var(--color-text-muted); font-size: .7rem; text-overflow: ellipsis; white-space: nowrap; }
.asset-value { min-width: 0; }
.asset-value > :deep(.money-value), .asset-value > :deep(.crypto-value) { min-width: 0; }
.asset-value > :deep(.money-value strong), .asset-value > :deep(.crypto-value strong) { font-weight: 550; }
.asset-value--primary > :deep(.money-value strong), .asset-value--primary > :deep(.crypto-value strong) { color: var(--color-text-primary); font-weight: 650; }
.asset-value--toman > :deep(.money-value strong) { color: var(--color-text-secondary); }
.asset-value.has-lock > :deep(.money-value strong), .asset-value.has-lock > :deep(.crypto-value strong) { color: var(--color-warning); }
.asset-actions { display: flex; min-width: 0; flex-wrap: wrap; align-items: center; justify-content: flex-end; gap: .35rem; }
.asset-actions > a { display: inline-flex; min-height: 2rem; align-items: center; justify-content: center; padding-inline: .58rem; border: 1px solid var(--color-border); border-radius: var(--radius-sm); background: var(--color-surface-1); color: var(--color-text-secondary); font-size: .69rem; font-weight: 600; transition: border-color var(--transition-fast), background var(--transition-fast), color var(--transition-fast); }
.asset-actions > .asset-action--primary { border-color: color-mix(in srgb, var(--color-primary) 30%, var(--color-border)); background: var(--color-primary-soft); color: var(--color-primary); }
.asset-actions > a:hover { border-color: var(--color-border-hover); background: var(--color-surface-3); color: var(--color-text-primary); }
.asset-actions > .asset-more { width: 2rem; padding: 0; border-color: transparent; background: transparent; color: var(--color-text-muted); }
.compact .asset-table thead, .compact .priority-secondary { display: none; }
.compact .asset-table tbody th, .compact .asset-table tbody td { height: 4.8rem; padding-inline: var(--space-4); }
.asset-mobile { min-width: 0; }
.asset-card { min-width: 0; padding: var(--space-4); border-block-end: 1px solid var(--color-border-soft); background: var(--color-surface-1); }
.asset-card:last-child { border-block-end: 0; }
.asset-card__top { display: flex; min-height: 2.75rem; align-items: center; justify-content: space-between; gap: var(--space-3); }
.asset-card__identity { display: flex; min-width: 0; align-items: center; gap: var(--space-3); }
.asset-card__identity .asset-identity__copy strong { overflow: visible; text-overflow: clip; white-space: normal; overflow-wrap: break-word; }
.asset-card__detail { display: inline-flex; min-height: 2.75rem; flex: 0 0 auto; align-items: center; gap: .15rem; color: var(--color-primary); font-size: var(--font-size-xs); font-weight: 600; }
.asset-card__detail svg { color: currentColor; }
.asset-card__balance { display: grid; min-width: 0; gap: var(--space-2); margin-top: var(--space-4); padding-block-end: var(--space-4); border-block-end: 1px solid var(--color-border-soft); line-height: 1.45; }
.asset-card__primary-value :deep(small) { order: -1; }
.asset-card__primary-value :deep(strong) { color: var(--color-text-primary); font-size: clamp(1.15rem, 5.8cqi, 1.45rem); font-weight: 700; }
.asset-card__equivalent :deep(strong) { color: var(--color-text-secondary); font-size: var(--font-size-xs); }
.asset-card__metrics { display: grid; grid-template-columns: 1fr 1fr; gap: 1px; margin-top: var(--space-3); overflow: hidden; border: 1px solid var(--color-border-soft); border-radius: var(--radius-md); background: var(--color-border-soft); }
.asset-card__metrics > span { display: grid; min-width: 0; gap: .15rem; padding: .65rem var(--space-3); background: var(--color-surface-2); }
.asset-card__metrics > span:first-child { border-radius: 0 var(--radius-md) var(--radius-md) 0; }
.asset-card__metrics > span:last-child { border-radius: var(--radius-md) 0 0 var(--radius-md); }
.asset-card__metrics > span > :deep(.money-value strong), .asset-card__metrics > span > :deep(.crypto-value strong) { color: var(--color-text-secondary); font-size: .74rem; font-weight: 600; }
.asset-card__metrics .has-lock > :deep(.money-value strong), .asset-card__metrics .has-lock > :deep(.crypto-value strong) { color: var(--color-warning); }
.asset-card__actions { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-2); padding-top: var(--space-3); }
.asset-card__actions--1 { grid-template-columns: minmax(0, 1fr); }
.asset-card__actions--2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.asset-card__actions--3 > :last-child { grid-column: 1 / -1; }
.asset-card__actions > a { display: inline-flex; min-height: 2.75rem; align-items: center; justify-content: center; gap: .35rem; border: 1px solid var(--color-border); border-radius: var(--radius-sm); background: var(--color-surface-2); color: var(--color-text-secondary); font-size: .72rem; font-weight: 600; }
.asset-card__actions > a:first-child { border-color: color-mix(in srgb, var(--color-primary) 35%, transparent); background: var(--color-primary-soft); color: var(--color-primary); }
.compact .asset-card__metrics { margin-bottom: 0; }
@container wallet-data (max-width: 72rem) {
  .priority-secondary { display: none; }
  .column-identity { width: 27%; }.column-total { width: 23%; }.column-toman { width: 23%; }.column-actions { width: 27%; }
  .asset-table thead th, .asset-table tbody th, .asset-table tbody td { padding-inline: var(--space-4); }
  .asset-actions > a:not(.asset-action--primary, .asset-more) { display: none; }
}
@container wallet-data (max-width: 46rem) {
  .asset-table.desktop-only { display: none !important; }
  .asset-mobile.mobile-only { display: grid !important; width: 100%; max-width: 100%; min-width: 0; }
  .asset-card { width: 100%; max-width: 100%; min-width: 0; }
}
@container wallet-data (max-width: 26rem) {
  .asset-card { padding-inline: var(--space-3); }
  .asset-card__top, .asset-card__identity { gap: var(--space-2); }
  .asset-card__detail { font-size: .68rem; }
  .asset-card__actions > a { gap: .3rem; }
}
@container wallet-data (max-width: 24rem) {
  .asset-card__metrics { grid-template-columns: 1fr; }
  .asset-card__metrics > span:first-child, .asset-card__metrics > span:last-child { border-radius: var(--radius-md); }
}
@container wallet-data (max-width: 22rem) {
  .asset-card__detail { width: 2.75rem; justify-content: center; font-size: 0; }
}
</style>
