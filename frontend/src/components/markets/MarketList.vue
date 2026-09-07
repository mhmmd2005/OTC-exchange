<script setup lang="ts">
import type { MarketAsset, WalletSummary } from '@/types'
import { compareDecimal } from '@/utils/financial'
import { formatPercentage } from '@/utils/formatters'
import AppButton from '@/components/ui/AppButton.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import AssetAvatar from '@/components/finance/AssetAvatar.vue'
import CryptoValue from '@/components/finance/CryptoValue.vue'
import MoneyValue from '@/components/finance/MoneyValue.vue'

const props = defineProps<{ assets: MarketAsset[]; wallet?: WalletSummary; favorites?: string[]; compact?: boolean }>()
defineEmits<{ toggleFavorite: [symbol: string] }>()

const isPositive = (asset: MarketAsset) => compareDecimal(asset.change24hPercent, '0') >= 0
const isFavorite = (asset: MarketAsset) => props.favorites?.includes(asset.symbol) ?? false
const holding = (asset: MarketAsset) => props.wallet?.assets.find((item) => item.symbol === asset.symbol)
</script>

<template>
  <div class="market-list" :class="{ compact }">
    <table class="market-table desktop-only">
      <caption class="sr-only">قیمت خرید و فروش ارزها و دارایی کاربر</caption>
      <colgroup>
        <col class="column-asset"><col class="column-buy"><col class="column-sell"><col class="column-change priority-secondary"><col v-if="wallet" class="column-holding priority-secondary"><col class="column-actions">
      </colgroup>
      <thead>
        <tr><th scope="col">دارایی</th><th scope="col">خرید از روشا</th><th scope="col">فروش به روشا</th><th scope="col" class="priority-secondary">تغییر ۲۴ ساعت</th><th v-if="wallet" scope="col" class="priority-secondary">دارایی شما</th><th scope="col"><span class="sr-only">عملیات</span></th></tr>
      </thead>
      <tbody>
        <tr v-for="asset in assets" :key="asset.symbol">
          <td>
            <div class="asset-cell">
              <button type="button" :aria-label="`${isFavorite(asset) ? 'حذف' : 'افزودن'} ${asset.nameFa} ${isFavorite(asset) ? 'از' : 'به'} علاقه‌مندی‌ها`" :class="{ active: isFavorite(asset) }" @click="$emit('toggleFavorite', asset.symbol)"><AppIcon name="star" :size="17" /></button>
              <AssetAvatar :symbol="asset.symbol" :color="asset.color" />
              <RouterLink :to="`/app/markets/${asset.symbol}`"><strong>{{ asset.nameFa }}</strong><small dir="ltr">{{ asset.nameEn }} · {{ asset.symbol }}</small></RouterLink>
            </div>
          </td>
          <td><MoneyValue class="price-cell" :value="asset.buyPriceToman" label="قیمت پرداختی شما" /></td>
          <td><MoneyValue class="price-cell" :value="asset.sellPriceToman" label="مبلغ دریافتی شما" /></td>
          <td class="priority-secondary"><span class="change" :class="isPositive(asset) ? 'up' : 'down'"><AppIcon :name="isPositive(asset) ? 'arrowUp' : 'arrowDown'" :size="14" />{{ formatPercentage(asset.change24hPercent, { showSign: true }) }}</span></td>
          <td v-if="wallet" class="priority-secondary"><span class="holding"><CryptoValue :value="holding(asset)?.total || '0'" :symbol="asset.symbol" /><MoneyValue :value="holding(asset)?.tomanValue || '0'" /></span></td>
          <td><div class="row-actions"><AppButton class="primary-row-action" size="sm" :disabled="!asset.tradable" :to="asset.tradable ? `/app/trade?side=buy&asset=${asset.symbol}` : undefined">خرید</AppButton><AppButton class="secondary-row-action" size="sm" variant="secondary" :disabled="!asset.tradable" :to="asset.tradable ? `/app/trade?side=sell&asset=${asset.symbol}` : undefined">فروش</AppButton><RouterLink :to="`/app/markets/${asset.symbol}`" class="details-link" :aria-label="`مشاهده جزئیات ${asset.nameFa}`"><AppIcon name="chevronLeft" :size="17" /></RouterLink></div></td>
        </tr>
      </tbody>
    </table>

    <div class="market-mobile mobile-only">
      <article v-for="asset in assets" :key="asset.symbol" class="market-card">
        <header class="market-card__head">
          <RouterLink :to="`/app/markets/${asset.symbol}`" class="market-card__identity"><AssetAvatar :symbol="asset.symbol" :color="asset.color" /><span><strong>{{ asset.nameFa }}</strong><small dir="ltr">{{ asset.nameEn }} · {{ asset.symbol }}</small></span></RouterLink>
          <span class="change" :class="isPositive(asset) ? 'up' : 'down'"><AppIcon :name="isPositive(asset) ? 'arrowUp' : 'arrowDown'" :size="13" />{{ formatPercentage(asset.change24hPercent, { showSign: true }) }}</span>
          <button type="button" class="favorite" :class="{ active: isFavorite(asset) }" :aria-label="`${isFavorite(asset) ? 'حذف' : 'افزودن'} ${asset.nameFa} ${isFavorite(asset) ? 'از' : 'به'} علاقه‌مندی‌ها`" @click="$emit('toggleFavorite', asset.symbol)"><AppIcon name="star" :size="18" /></button>
        </header>
        <div class="market-card__prices">
          <MoneyValue :value="asset.buyPriceToman" label="خرید از روشا" />
          <MoneyValue :value="asset.sellPriceToman" label="فروش به روشا" />
        </div>
        <div v-if="wallet && !compact" class="market-card__holding"><span>دارایی شما</span><CryptoValue :value="holding(asset)?.total || '0'" :symbol="asset.symbol" /><MoneyValue :value="holding(asset)?.tomanValue || '0'" /></div>
        <div class="market-card__actions"><AppButton size="sm" block :disabled="!asset.tradable" :to="asset.tradable ? `/app/trade?side=buy&asset=${asset.symbol}` : undefined">خرید</AppButton><AppButton v-if="!compact" size="sm" block variant="secondary" :disabled="!asset.tradable" :to="asset.tradable ? `/app/trade?side=sell&asset=${asset.symbol}` : undefined">فروش</AppButton></div>
      </article>
    </div>
  </div>
</template>

<style scoped>
.market-list { width: 100%; max-width: 100%; min-width: 0; container: market-data / inline-size; }
.market-table { width: 100%; border-collapse: collapse; table-layout: fixed; }
.column-asset { width: 20%; }.column-buy, .column-sell { width: 15%; }.column-change { width: 11%; }.column-holding { width: 17%; }.column-actions { width: 22%; }
th { height: 2.9rem; padding-inline: var(--space-5); border-block-end: 1px solid var(--color-border); background: color-mix(in srgb, var(--color-surface-2) 70%, transparent); color: var(--color-text-muted); font-size: var(--font-size-xs); font-weight: 500; text-align: start; white-space: nowrap; }
td { height: 5.55rem; padding: .72rem var(--space-5); border-block-end: 1px solid var(--color-border-soft); vertical-align: middle; }
tbody tr { transition: background var(--transition-fast); }
tbody tr:hover { background: var(--color-surface-2); }
tbody tr:last-child td { border-block-end: 0; }
.asset-cell { display: flex; min-width: 0; align-items: center; gap: var(--space-3); }
.asset-cell > button, .favorite { display: grid; width: 2rem; height: 2rem; flex: 0 0 auto; border: 0; border-radius: var(--radius-sm); background: transparent; color: var(--color-text-muted); place-items: center; }
.favorite { width: 2.75rem; height: 2.75rem; }
.asset-cell > button:hover, .favorite:hover { background: var(--color-gold-soft); color: var(--color-gold); }
.asset-cell > button.active, .favorite.active { color: var(--color-gold); }
.asset-cell a, .market-card__identity > span, .holding { display: grid; min-width: 0; line-height: 1.38; }
.asset-cell strong, .market-card__identity strong { overflow: hidden; font-size: var(--font-size-sm); font-weight: 650; text-overflow: ellipsis; white-space: nowrap; }
.asset-cell small, .market-card__identity small { overflow: hidden; color: var(--color-text-muted); font-size: .68rem; text-overflow: ellipsis; white-space: nowrap; }
.price-cell { min-width: 0; }
.price-cell :deep(strong), .holding :deep(strong) { font-weight: 550; }
.holding { gap: .12rem; }
.holding > :deep(.money-value strong) { color: var(--color-text-muted); font-size: .7rem; }
.change { display: inline-flex; width: max-content; align-items: center; gap: .22rem; padding: .28rem .55rem; border-radius: var(--radius-pill); direction: ltr; font-size: var(--font-size-xs); font-variant-numeric: tabular-nums; font-weight: 650; white-space: nowrap; }
.change.up { background: var(--color-success-soft); color: var(--color-success); }
.change.down { background: var(--color-danger-soft); color: var(--color-danger); }
.row-actions { display: flex; min-width: 0; align-items: center; justify-content: flex-end; gap: var(--space-2); }
.row-actions :deep(.app-button) { min-height: 2.25rem; padding-inline: var(--space-3); }
.details-link { display: grid; width: 2.15rem; height: 2.15rem; border-radius: var(--radius-sm); color: var(--color-text-muted); place-items: center; }
.details-link:hover { background: var(--color-surface-3); color: var(--color-primary); }
.compact th:nth-child(3), .compact td:nth-child(3), .compact th:nth-child(5), .compact td:nth-child(5), .compact .row-actions > :nth-child(2) { display: none; }
.compact td { height: 4.85rem; padding-inline: var(--space-4); }
.compact th { display: none; }
.compact .row-actions { min-width: 0; }
.market-mobile { min-width: 0; }
.market-card { padding: var(--space-4); border-block-end: 1px solid var(--color-border-soft); background: var(--color-surface-1); }
.market-card:last-child { border-block-end: 0; }
.market-card__head { display: grid; grid-template-columns: minmax(0, 1fr) auto auto; align-items: center; gap: var(--space-2); }
.market-card__identity { display: flex; min-width: 0; align-items: center; gap: var(--space-3); }
.market-card__identity strong { overflow: visible; text-overflow: clip; white-space: normal; overflow-wrap: break-word; }
.market-card__prices { display: grid; grid-template-columns: 1fr 1fr; gap: 1px; margin-top: var(--space-4); overflow: hidden; border: 1px solid var(--color-border-soft); border-radius: var(--radius-md); background: var(--color-border-soft); }
.market-card__prices > :deep(.money-value) { min-width: 0; padding: .7rem var(--space-3); background: var(--color-surface-2); }
.market-card__prices > :deep(.money-value strong) { font-size: var(--font-size-xs); }
.market-card__holding { display: grid; grid-template-columns: auto 1fr; gap: .08rem var(--space-2); margin-top: var(--space-3); padding: .55rem var(--space-3); border-radius: var(--radius-sm); background: var(--color-surface-2); }
.market-card__holding span { grid-row: 1 / span 2; align-self: center; color: var(--color-text-muted); font-size: .68rem; }
.market-card__holding > :deep(.crypto-value), .market-card__holding > :deep(.money-value) { justify-self: end; text-align: end; }
.market-card__holding > :deep(.money-value strong) { color: var(--color-text-muted); font-size: .7rem; }
.market-card__actions { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-2); margin-top: var(--space-3); }
.compact .market-card__actions { grid-template-columns: 1fr; }
@container market-data (max-width: 70rem) {
  th, td { padding-inline: var(--space-4); }
  .priority-secondary { display: none; }
  .column-asset { width: 28%; }.column-buy, .column-sell { width: 23%; }.column-actions { width: 26%; }
  .secondary-row-action { display: none; }
}
@container market-data (max-width: 46rem) {
  .market-table.desktop-only { display: none !important; }
  .market-mobile.mobile-only { display: grid !important; width: 100%; max-width: 100%; min-width: 0; }
}
@container market-data (max-width: 24rem) {
  .market-card__prices { grid-template-columns: 1fr; }
}
@media (max-width: 380px) {
  .market-card { padding-inline: var(--space-3); }
  .market-card__head { gap: .35rem; }
  .market-card__identity { gap: var(--space-2); }
}
@media (hover: none), (pointer: coarse) {
  .asset-cell > button { width: 2.75rem; height: 2.75rem; }
  .row-actions :deep(.app-button) { min-height: 2.75rem; }
}
</style>
