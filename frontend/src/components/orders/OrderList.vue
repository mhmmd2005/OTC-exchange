<script setup lang="ts">
import type { OtcOrder } from '@/types'
import { formatPersianDate, formatTime } from '@/utils/formatters'
import AppIcon from '@/components/ui/AppIcon.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import AssetAvatar from '@/components/finance/AssetAvatar.vue'
import CryptoValue from '@/components/finance/CryptoValue.vue'
import MoneyValue from '@/components/finance/MoneyValue.vue'

defineProps<{ orders: OtcOrder[]; compact?: boolean }>()
const colors: Record<string, string> = { USDT: '#26A17B', BTC: '#F7931A', ETH: '#627EEA', TRX: '#EF0027', TON: '#0098EA' }
</script>

<template>
  <div class="orders-list" :class="{ compact }">
    <table class="order-table desktop-only">
      <caption class="sr-only">فهرست سفارش‌های خرید و فروش</caption>
      <colgroup><col class="column-order"><col class="column-amount"><col class="column-rate priority-tertiary"><col class="column-total"><col class="column-date priority-secondary"><col class="column-status"><col class="column-detail"></colgroup>
      <thead><tr><th scope="col">سفارش</th><th scope="col" class="column-label-amount">مقدار</th><th scope="col" class="priority-tertiary">نرخ معامله</th><th scope="col">مبلغ نهایی</th><th scope="col" class="priority-secondary">زمان ثبت</th><th scope="col">وضعیت</th><th scope="col"><span class="sr-only">جزئیات</span></th></tr></thead>
      <tbody><tr v-for="order in orders" :key="order.id" class="order-row">
        <th scope="row"><RouterLink :to="`/app/orders/${order.id}`" class="order-asset"><AssetAvatar :symbol="order.assetSymbol" :color="colors[order.assetSymbol]" /><span><strong>{{ order.assetNameFa }}</strong><small dir="ltr">{{ order.orderNumber }}</small></span><i :class="order.side">{{ order.side === 'buy' ? 'خرید' : 'فروش' }}</i></RouterLink></th>
        <td class="order-value order-amount"><CryptoValue :value="order.cryptoAmount" :symbol="order.assetSymbol" label="مقدار رمزارز" /></td>
        <td class="order-value order-rate priority-tertiary"><MoneyValue :value="order.rateToman" label="به‌ازای هر واحد" /></td>
        <td class="order-value order-value--total"><MoneyValue :value="order.finalTomanAmount" label="با احتساب کارمزد" /></td>
        <td class="order-value order-date priority-secondary"><strong>{{ formatPersianDate(order.createdAt) }}</strong><small>{{ formatTime(order.createdAt) }}</small></td>
        <td><StatusBadge domain="order" :status="order.status" /></td>
        <td><RouterLink :to="`/app/orders/${order.id}`" class="row-chevron" :aria-label="`مشاهده جزئیات ${order.orderNumber}`"><AppIcon name="chevronLeft" :size="17" /></RouterLink></td>
      </tr></tbody>
    </table>

    <div class="order-mobile mobile-only">
      <RouterLink v-for="order in orders" :key="order.id" :to="`/app/orders/${order.id}`" class="order-card">
        <header>
          <span class="order-card__identity"><AssetAvatar :symbol="order.assetSymbol" :color="colors[order.assetSymbol]" /><span><strong>{{ order.side === 'buy' ? 'خرید' : 'فروش' }} {{ order.assetNameFa }}</strong><small dir="ltr">{{ order.orderNumber }}</small></span></span>
          <StatusBadge domain="order" :status="order.status" />
        </header>
        <div class="order-card__amounts">
          <CryptoValue :value="order.cryptoAmount" :symbol="order.assetSymbol" label="مقدار" />
          <MoneyValue :value="order.finalTomanAmount" label="مبلغ نهایی" />
        </div>
        <footer><time :datetime="order.createdAt">{{ formatPersianDate(order.createdAt) }} — {{ formatTime(order.createdAt) }}</time><AppIcon name="chevronLeft" :size="16" /></footer>
      </RouterLink>
    </div>
  </div>
</template>

<style scoped>
.orders-list { width: 100%; max-width: 100%; min-width: 0; container: order-data / inline-size; }
.order-table { width: 100%; border-collapse: collapse; table-layout: fixed; }
.column-order { width: 22%; }.column-amount { width: 15%; }.column-rate { width: 15%; }.column-total { width: 16%; }.column-date { width: 13%; }.column-status { width: 15%; }.column-detail { width: 4%; }
.order-table th { font-weight: inherit; text-align: start; }
.order-table thead th { height: 2.9rem; padding-inline: var(--space-5); border-block-end: 1px solid var(--color-border); background: color-mix(in srgb, var(--color-surface-2) 70%, transparent); color: var(--color-text-muted); font-size: var(--font-size-xs); font-weight: 500; white-space: nowrap; }
.order-table tbody th, .order-table tbody td { height: 5.45rem; padding: .75rem var(--space-5); border-block-end: 1px solid var(--color-border-soft); vertical-align: middle; transition: background var(--transition-fast); }
.order-table tbody tr:hover > * { background: var(--color-surface-2); }
.order-table tbody tr:last-child > * { border-block-end: 0; }
.order-asset { display: flex; min-width: 0; align-items: center; gap: var(--space-3); }
.order-asset > span, .order-value { display: grid; min-width: 0; gap: .1rem; line-height: 1.36; }
.order-asset strong { overflow: hidden; font-size: var(--font-size-sm); font-weight: 600; text-overflow: ellipsis; white-space: nowrap; }
.order-value > :deep(.money-value), .order-value > :deep(.crypto-value) { min-width: 0; }
.order-value > :deep(.money-value strong), .order-value > :deep(.crypto-value strong) { font-weight: 600; }
.order-date strong { min-width: 0; font-size: var(--font-size-sm); font-weight: 500; line-height: 1.5; }
.order-asset small, .order-value small { overflow: hidden; color: var(--color-text-muted); font-size: .68rem; text-overflow: ellipsis; white-space: nowrap; }
.order-asset i { display: inline-flex; min-height: 1.45rem; align-items: center; padding-inline: .45rem; border-radius: var(--radius-pill); font-size: .65rem; font-style: normal; font-weight: 650; }
.order-asset i.buy { background: var(--color-success-soft); color: var(--color-success); }
.order-asset i.sell { background: var(--color-danger-soft); color: var(--color-danger); }
.order-value--total > :deep(.money-value strong) { color: var(--color-text-primary); font-weight: 650; }
.order-date strong { color: var(--color-text-secondary); font-weight: 500; }
.row-chevron { display: grid; width: 1.8rem; height: 1.8rem; border-radius: var(--radius-sm); color: var(--color-text-muted); place-items: center; }
.order-row:hover .row-chevron { background: var(--color-surface-3); color: var(--color-primary); }
.compact .order-table thead, .compact .order-amount, .compact .priority-tertiary, .compact .priority-secondary, .compact .column-amount { display: none; }
.compact .order-table tbody th, .compact .order-table tbody td { height: 4.85rem; padding-inline: var(--space-4); }
.order-card { display: grid; gap: var(--space-3); padding: var(--space-4); border-block-end: 1px solid var(--color-border-soft); background: var(--color-surface-1); }
.order-card:last-child { border-block-end: 0; }
.order-card header { display: flex; min-width: 0; align-items: center; justify-content: space-between; gap: var(--space-3); }
.order-card__identity { display: flex; min-width: 0; align-items: center; gap: var(--space-3); }
.order-card__identity > span { display: grid; min-width: 0; line-height: 1.38; }
.order-card__identity strong { overflow: visible; font-size: var(--font-size-sm); font-weight: 650; text-overflow: clip; white-space: normal; overflow-wrap: break-word; }
.order-card__identity small { color: var(--color-text-muted); font-size: .68rem; }
.order-card__amounts { display: grid; grid-template-columns: 1fr 1fr; gap: 1px; overflow: hidden; border: 1px solid var(--color-border-soft); border-radius: var(--radius-md); background: var(--color-border-soft); }
.order-card__amounts > :deep(.money-value), .order-card__amounts > :deep(.crypto-value) { min-width: 0; padding: .65rem var(--space-3); background: var(--color-surface-2); }
.order-card__amounts > :deep(.money-value strong), .order-card__amounts > :deep(.crypto-value strong) { font-size: var(--font-size-xs); }
.order-card footer { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: center; gap: var(--space-2); color: var(--color-text-muted); font-size: .68rem; }
.order-card footer time { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.order-card footer svg { color: var(--color-primary); }
@container order-data (max-width: 70rem) {
  .priority-tertiary { display: none; }
  .column-order { width: 26%; }.column-amount { width: 18%; }.column-total { width: 20%; }.column-date { width: 16%; }.column-status { width: 16%; }.column-detail { width: 4%; }
  .order-table thead th, .order-table tbody th, .order-table tbody td { padding-inline: var(--space-4); }
}
@container order-data (max-width: 58rem) {
  .priority-secondary { display: none; }
  .column-order { width: 29%; }.column-amount { width: 21%; }.column-total { width: 24%; }.column-status { width: 21%; }.column-detail { width: 5%; }
}
@container order-data (max-width: 46rem) {
  .order-table.desktop-only { display: none !important; }
  .order-mobile.mobile-only { display: grid !important; width: 100%; max-width: 100%; min-width: 0; }
  .order-card { width: 100%; max-width: 100%; min-width: 0; }
}
@container order-data (max-width: 24rem) { .order-card { padding-inline: var(--space-3); }.order-card header { align-items: flex-start; }.order-card__identity { gap: var(--space-2); }.order-card__amounts { grid-template-columns: 1fr; } }
</style>
