<script setup lang="ts">
import { useRoute } from 'vue-router'
import type { Transaction } from '@/types'
import { formatPersianDate, formatTime } from '@/utils/formatters'
import AppIcon from '@/components/ui/AppIcon.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import CryptoValue from '@/components/finance/CryptoValue.vue'
import MoneyValue from '@/components/finance/MoneyValue.vue'

defineProps<{ transactions: Transaction[]; compact?: boolean }>()

const route = useRoute()

const typeIcons: Record<string, string> = { buy: 'trade', sell: 'trade', toman_deposit: 'download', toman_withdrawal: 'upload', crypto_deposit: 'arrowDown', crypto_withdrawal: 'arrowUp', fee: 'wallet', refund: 'refresh', reversal: 'refresh' }
const incomingTypes = new Set(['buy', 'toman_deposit', 'crypto_deposit', 'refund'])
const tone = (item: Transaction) => incomingTypes.has(item.type) ? 'incoming' : item.type === 'reversal' ? 'warning' : 'outgoing'
</script>

<template>
  <div class="transactions-list" :class="{ compact }">
    <table class="transaction-table desktop-only">
      <caption class="sr-only">فهرست تراکنش‌های حساب</caption>
      <colgroup><col class="column-transaction"><col class="column-amount"><col class="column-toman priority-secondary"><col class="column-date priority-tertiary"><col class="column-status"><col class="column-detail"></colgroup>
      <thead><tr><th scope="col">تراکنش</th><th scope="col">مبلغ</th><th scope="col" class="priority-secondary">معادل تومان</th><th scope="col" class="priority-tertiary">زمان ثبت</th><th scope="col">وضعیت</th><th scope="col"><span class="sr-only">جزئیات</span></th></tr></thead>
      <tbody><tr v-for="item in transactions" :key="item.id" class="transaction-row">
        <th scope="row"><RouterLink :to="{ path: '/app/transactions', query: { ...route.query, detail: item.id } }" class="transaction-main"><span class="transaction-icon" :class="tone(item)"><AppIcon :name="typeIcons[item.type] || 'transactions'" :size="20" /></span><span class="transaction-copy"><strong>{{ item.title }}</strong><small>{{ item.description || item.referenceNumber }}</small></span></RouterLink></th>
        <td class="transaction-value transaction-amount"><MoneyValue v-if="item.assetSymbol === 'IRT'" :value="item.amount" :label="tone(item) === 'incoming' ? 'ورودی به حساب' : item.type === 'reversal' ? 'اصلاح گردش' : 'خروجی از حساب'" /><CryptoValue v-else :value="item.amount" :symbol="item.assetSymbol" :label="tone(item) === 'incoming' ? 'ورودی به حساب' : item.type === 'reversal' ? 'اصلاح گردش' : 'خروجی از حساب'" /></td>
        <td class="transaction-value transaction-toman priority-secondary"><MoneyValue v-if="item.tomanAmount" :value="item.tomanAmount" :label="item.networkCode ? `شبکه ${item.networkCode}` : 'ارزش ثبت‌شده'" /><span v-else class="empty-value">—<small>{{ item.networkCode ? `شبکه ${item.networkCode}` : 'ارزش ثبت‌شده' }}</small></span></td>
        <td class="transaction-value transaction-date priority-tertiary"><strong>{{ formatPersianDate(item.createdAt) }}</strong><small>{{ formatTime(item.createdAt) }}</small></td>
        <td><StatusBadge domain="transaction" :status="item.status" /></td>
        <td><RouterLink :to="{ path: '/app/transactions', query: { ...route.query, detail: item.id } }" class="details" :aria-label="`مشاهده جزئیات ${item.title}`"><AppIcon name="chevronLeft" :size="17" /></RouterLink></td>
      </tr></tbody>
    </table>

    <div class="transaction-mobile mobile-only">
      <RouterLink v-for="item in transactions" :key="item.id" :to="{ path: '/app/transactions', query: { ...route.query, detail: item.id } }" class="transaction-card">
        <span class="transaction-icon" :class="tone(item)"><AppIcon :name="typeIcons[item.type] || 'transactions'" :size="20" /></span>
        <span class="transaction-card__copy"><strong>{{ item.title }}</strong><small>{{ item.description || item.referenceNumber }}</small></span>
        <StatusBadge domain="transaction" :status="item.status" />
        <span class="transaction-card__amount"><MoneyValue v-if="item.assetSymbol === 'IRT'" :value="item.amount" /><CryptoValue v-else :value="item.amount" :symbol="item.assetSymbol" /><MoneyValue v-if="item.tomanAmount && item.assetSymbol !== 'IRT'" class="transaction-card__equivalent" :value="item.tomanAmount" label="معادل تومان" /></span>
        <time :datetime="item.createdAt">{{ formatPersianDate(item.createdAt) }} · {{ formatTime(item.createdAt) }}<bdi v-if="item.networkCode" dir="ltr"> · {{ item.networkCode }}</bdi></time>
        <AppIcon class="transaction-card__chevron" name="chevronLeft" :size="16" />
      </RouterLink>
    </div>
  </div>
</template>

<style scoped>
.transactions-list { width: 100%; max-width: 100%; min-width: 0; container: transaction-data / inline-size; }
.transaction-table { width: 100%; border-collapse: collapse; table-layout: fixed; }
.column-transaction { width: 27%; }.column-amount { width: 19%; }.column-toman { width: 18%; }.column-date { width: 15%; }.column-status { width: 17%; }.column-detail { width: 4%; }
.transaction-table th { font-weight: inherit; text-align: start; }
.transaction-table thead th { height: 2.9rem; padding-inline: var(--space-5); border-block-end: 1px solid var(--color-border); background: color-mix(in srgb, var(--color-surface-2) 70%, transparent); color: var(--color-text-muted); font-size: var(--font-size-xs); font-weight: 500; white-space: nowrap; }
.transaction-table tbody th, .transaction-table tbody td { height: 5.35rem; padding: .72rem var(--space-5); border-block-end: 1px solid var(--color-border-soft); vertical-align: middle; transition: background var(--transition-fast); }
.transaction-table tbody tr:hover > * { background: var(--color-surface-2); }
.transaction-table tbody tr:last-child > * { border-block-end: 0; }
.transaction-main { display: flex; min-width: 0; align-items: center; gap: var(--space-3); }
.transaction-icon { display: grid; width: 2.75rem; height: 2.75rem; flex: 0 0 auto; border: 1px solid transparent; border-radius: .85rem; place-items: center; }
.transaction-icon.incoming { border-color: color-mix(in srgb, var(--color-success) 18%, transparent); background: var(--color-success-soft); color: var(--color-success); }
.transaction-icon.outgoing { border-color: color-mix(in srgb, var(--color-primary) 18%, transparent); background: var(--color-primary-soft); color: var(--color-primary); }
.transaction-icon.warning { border-color: color-mix(in srgb, var(--color-warning) 18%, transparent); background: var(--color-warning-soft); color: var(--color-warning); }
.transaction-copy, .transaction-value, .transaction-card__copy, .transaction-card__amount { display: grid; min-width: 0; gap: .12rem; line-height: 1.36; }
.transaction-copy strong, .transaction-card__copy strong { overflow: hidden; font-size: var(--font-size-sm); font-weight: 600; text-overflow: ellipsis; white-space: nowrap; }
.transaction-card__copy strong { overflow: visible; text-overflow: clip; white-space: normal; overflow-wrap: break-word; }
.transaction-value > :deep(.money-value), .transaction-value > :deep(.crypto-value) { min-width: 0; }
.transaction-value > :deep(.money-value strong), .transaction-value > :deep(.crypto-value strong) { font-weight: 600; }
.transaction-date strong, .empty-value { min-width: 0; font-size: var(--font-size-sm); font-weight: 500; line-height: 1.5; }
.transaction-copy small, .transaction-card__copy small { overflow: hidden; color: var(--color-text-muted); font-size: .68rem; text-overflow: ellipsis; white-space: nowrap; }
.transaction-value small, .transaction-card__amount small { color: var(--color-text-muted); font-size: .68rem; line-height: 1.5; overflow-wrap: break-word; }
.transaction-amount > :deep(.money-value strong), .transaction-amount > :deep(.crypto-value strong) { color: var(--color-text-primary); font-weight: 650; }
.transaction-toman > :deep(.money-value strong), .transaction-date strong { color: var(--color-text-secondary); font-weight: 500; }
.empty-value { display: grid; color: var(--color-text-secondary); }
.empty-value small { font-weight: 400; }
.details { display: grid; width: 1.8rem; height: 1.8rem; border-radius: var(--radius-sm); color: var(--color-text-muted); place-items: center; }
.transaction-row:hover .details { background: var(--color-surface-3); color: var(--color-primary); }
.compact .transaction-table thead, .compact .priority-secondary, .compact .priority-tertiary { display: none; }
.compact .transaction-table tbody th, .compact .transaction-table tbody td { height: 4.8rem; padding-inline: var(--space-4); }
.transaction-card { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: .2rem var(--space-3); min-height: 6.5rem; padding: var(--space-4); border-block-end: 1px solid var(--color-border-soft); background: var(--color-surface-1); }
.transaction-card:last-child { border-block-end: 0; }
.transaction-card > .transaction-icon { grid-row: 1 / span 2; grid-column: 1; }
.transaction-card__copy { grid-row: 1; grid-column: 2; }
.transaction-card > :deep(.status) { grid-row: 1; grid-column: 3; }
.transaction-card__amount { grid-row: 2; grid-column: 2 / span 2; margin-top: .15rem; }
.transaction-card__amount > :deep(.money-value strong), .transaction-card__amount > :deep(.crypto-value strong) { font-size: var(--font-size-sm); }
.transaction-card__equivalent { margin-top: .15rem; }
.transaction-card__equivalent :deep(strong) { color: var(--color-text-muted); font-size: .72rem; }
.transaction-card time { grid-row: 3; grid-column: 2 / span 2; overflow: hidden; margin-top: .25rem; color: var(--color-text-muted); font-size: .67rem; text-overflow: ellipsis; white-space: nowrap; }
.transaction-card__chevron { display: none; color: var(--color-primary); }
.compact .transaction-card { min-height: 5.75rem; }
.compact .transaction-card time { display: none; }
@container transaction-data (max-width: 64rem) {
  .priority-secondary { display: none; }
  .column-transaction { width: 34%; }.column-amount { width: 24%; }.column-date { width: 19%; }.column-status { width: 18%; }.column-detail { width: 5%; }
  .transaction-table thead th, .transaction-table tbody th, .transaction-table tbody td { padding-inline: var(--space-4); }
}
@container transaction-data (max-width: 52rem) {
  .priority-tertiary { display: none; }
  .column-transaction { width: 41%; }.column-amount { width: 29%; }.column-status { width: 24%; }.column-detail { width: 6%; }
}
@container transaction-data (max-width: 46rem) {
  .transaction-table.desktop-only { display: none !important; }
  .transaction-mobile.mobile-only { display: grid !important; width: 100%; max-width: 100%; min-width: 0; }
}
@container transaction-data (max-width: 24rem) {
  .transaction-card { grid-template-columns: auto minmax(0, 1fr) auto; gap-inline: var(--space-2); padding-inline: var(--space-3); }
  .transaction-card > :deep(.status) { padding-inline: .42rem; }
  .transaction-card > :deep(.status i) { display: none; }
}
</style>
