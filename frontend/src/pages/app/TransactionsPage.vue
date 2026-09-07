<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter, type LocationQueryRaw } from 'vue-router'
import type { Transaction, TransactionFilters } from '@/types'
import { transactionService } from '@/services/transaction.service'
import {
  formatCrypto,
  formatPersianDate,
  formatPersianDateTime,
  formatToman,
  normalizeDigits,
  toPersianDigits,
} from '@/utils/formatters'
import {
  persianDateBoundaryIso,
  serializePersianDateInput,
} from '@/utils/persianDateInput'
import AppCard from '@/components/ui/AppCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import AppInput from '@/components/ui/AppInput.vue'
import AppModal from '@/components/ui/AppModal.vue'
import AppPagination from '@/components/ui/AppPagination.vue'
import AppSelect from '@/components/ui/AppSelect.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import CopyButton from '@/components/ui/CopyButton.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import TransactionList from '@/components/transactions/TransactionList.vue'
import CryptoValue from '@/components/finance/CryptoValue.vue'
import MoneyValue from '@/components/finance/MoneyValue.vue'

const transactionTypes = new Set([
  'buy', 'sell', 'toman_deposit', 'toman_withdrawal', 'crypto_deposit',
  'crypto_withdrawal', 'fee', 'refund', 'reversal',
])
const transactionStatuses = new Set([
  'pending', 'processing', 'completed', 'failed', 'cancelled', 'reversed',
])
const transactionTypeOptions = [
  { value: 'all', label: 'همه نوع‌ها' },
  { value: 'buy', label: 'خرید' },
  { value: 'sell', label: 'فروش' },
  { value: 'toman_deposit', label: 'واریز تومان' },
  { value: 'toman_withdrawal', label: 'برداشت تومان' },
  { value: 'crypto_deposit', label: 'واریز رمزارز' },
  { value: 'crypto_withdrawal', label: 'برداشت رمزارز' },
  { value: 'fee', label: 'کارمزد' },
  { value: 'refund', label: 'بازپرداخت' },
  { value: 'reversal', label: 'برگشت تراکنش' },
]
const assetOptions = [
  { value: 'all', label: 'همه دارایی‌ها' },
  { value: 'IRT', label: 'تومان', description: 'IRT' },
  { value: 'USDT', label: 'تتر', description: 'USDT' },
  { value: 'BTC', label: 'بیت‌کوین', description: 'BTC' },
  { value: 'ETH', label: 'اتریوم', description: 'ETH' },
  { value: 'TRX', label: 'ترون', description: 'TRX' },
  { value: 'TON', label: 'تون‌کوین', description: 'TON' },
]
const transactionStatusOptions = [
  { value: 'all', label: 'همه وضعیت‌ها' },
  { value: 'pending', label: 'در انتظار بررسی' },
  { value: 'processing', label: 'در حال پردازش' },
  { value: 'completed', label: 'تکمیل‌شده' },
  { value: 'failed', label: 'ناموفق' },
  { value: 'cancelled', label: 'لغوشده' },
  { value: 'reversed', label: 'برگشت‌خورده' },
]
const filterQueryKeys = ['q', 'type', 'status', 'asset', 'network', 'from', 'to', 'page'] as const

const route = useRoute(), router = useRouter()
const transactions = ref<Transaction[]>([]), detail = ref<Transaction | null>(null)
const loading = ref(true), error = ref(''), totalResults = ref(0)
const page = ref(queryPage(route.query.page)), totalPages = ref(1)
const search = ref(queryString(route.query.q))
const type = ref(validType(queryString(route.query.type)))
const status = ref(validStatus(queryString(route.query.status)))
const asset = ref(queryString(route.query.asset).toUpperCase() || 'all')
const network = ref(queryString(route.query.network).toUpperCase())
const fromDate = ref(queryDateInput(route.query.from))
const toDate = ref(queryDateInput(route.query.to))
const mobileFiltersOpen = ref(false)
let commitTimer: number | undefined
let listRequestSequence = 0
let detailRequestSequence = 0
let syncingFromRoute = false

function queryString(value: unknown): string {
  return typeof value === 'string' ? value : ''
}

function queryPage(value: unknown): number {
  const parsed = Number(queryString(value))
  return Number.isInteger(parsed) && parsed > 0 ? parsed : 1
}

function validType(value: string): string {
  return transactionTypes.has(value) ? value : 'all'
}

function validStatus(value: string): string {
  return transactionStatuses.has(value) ? value : 'all'
}

function queryDateInput(value: unknown): string {
  const raw = queryString(value).trim()
  if (!raw) return ''
  const normalized = normalizeDigits(raw)
  if (/^1[2-7]\d{2}[-/]\d{1,2}[-/]\d{1,2}$/.test(normalized)) {
    return toPersianDigits(normalized.replace(/-/g, '/'))
  }
  const date = new Date(raw)
  return Number.isNaN(date.getTime()) ? toPersianDigits(normalized) : formatPersianDate(date)
}

const parsedDateRange = computed(() => {
  const from = fromDate.value.trim() ? persianDateBoundaryIso(fromDate.value, 'start') : undefined
  const to = toDate.value.trim() ? persianDateBoundaryIso(toDate.value, 'end') : undefined
  let fromError = fromDate.value.trim() && !from ? 'تاریخ شروع معتبر نیست؛ نمونه: ۱۴۰۵/۰۶/۰۱' : ''
  let toError = toDate.value.trim() && !to ? 'تاریخ پایان معتبر نیست؛ نمونه: ۱۴۰۵/۰۶/۳۱' : ''
  if (!fromError && !toError && from && to && Date.parse(from) > Date.parse(to)) {
    fromError = 'تاریخ شروع باید پیش از تاریخ پایان باشد.'
    toError = 'تاریخ پایان باید پس از تاریخ شروع باشد.'
  }
  return { from, to, fromError, toError, valid: !fromError && !toError }
})

const hasActiveFilters = computed(() => type.value !== 'all'
  || asset.value !== 'all'
  || status.value !== 'all'
  || Boolean(network.value || search.value || fromDate.value || toDate.value))

const load = async () => {
  if (!parsedDateRange.value.valid) {
    listRequestSequence += 1
    loading.value = false
    error.value = ''
    transactions.value = []
    totalResults.value = 0
    totalPages.value = 1
    return
  }
  const requestId = ++listRequestSequence
  loading.value = true
  error.value = ''
  const filters: TransactionFilters = { page: page.value, pageSize: 8, search: search.value }
  if (type.value !== 'all') filters.type = type.value as TransactionFilters['type']
  if (status.value !== 'all') filters.status = status.value as TransactionFilters['status']
  if (asset.value !== 'all') filters.assetSymbol = asset.value
  if (network.value) filters.networkCode = network.value
  if (parsedDateRange.value.from) filters.from = parsedDateRange.value.from
  if (parsedDateRange.value.to) filters.to = parsedDateRange.value.to
  try {
    const result = await transactionService.list(filters)
    if (requestId !== listRequestSequence) return
    transactions.value = result.items
    totalResults.value = result.total
    totalPages.value = Math.max(1, result.totalPages)
    const resolvedPage = Math.max(1, Math.min(result.page, totalPages.value))
    if (page.value !== resolvedPage) page.value = resolvedPage
  } catch (reason) {
    if (requestId === listRequestSequence) {
      error.value = reason instanceof Error ? reason.message : 'دریافت تراکنش‌ها ممکن نشد.'
    }
  } finally {
    if (requestId === listRequestSequence) loading.value = false
  }
}

const openDetail = async (id: string | null) => {
  const requestId = ++detailRequestSequence
  if (!id) {
    detail.value = null
    return
  }
  try {
    const response = await transactionService.getById(id)
    if (requestId === detailRequestSequence) detail.value = response
  } catch {
    if (requestId === detailRequestSequence) detail.value = null
  }
}

const closeDetail = () => {
  detailRequestSequence += 1
  detail.value = null
  const query = { ...route.query }
  delete query.detail
  void router.replace({ query })
}

function sameFilterQuery(next: LocationQueryRaw): boolean {
  return filterQueryKeys.every((key) => String(next[key] ?? '') === queryString(route.query[key]))
}

function commitFilters() {
  if (!parsedDateRange.value.valid) return
  const query: LocationQueryRaw = { ...route.query }
  filterQueryKeys.forEach((key) => { delete query[key] })
  if (search.value.trim()) query.q = search.value.trim()
  if (type.value !== 'all') query.type = type.value
  if (status.value !== 'all') query.status = status.value
  if (asset.value !== 'all') query.asset = asset.value
  if (network.value.trim()) query.network = network.value.trim().toUpperCase()
  const serializedFrom = serializePersianDateInput(fromDate.value)
  const serializedTo = serializePersianDateInput(toDate.value)
  if (serializedFrom) query.from = serializedFrom
  if (serializedTo) query.to = serializedTo
  if (page.value > 1) query.page = String(page.value)

  if (sameFilterQuery(query)) {
    void load()
    return
  }
  void router.replace({ query })
}

function queueCommit(delay = 0) {
  window.clearTimeout(commitTimer)
  commitTimer = window.setTimeout(commitFilters, delay)
}

function resetPageAndCommit(delay = 0) {
  if (syncingFromRoute) return
  listRequestSequence += 1
  if (page.value !== 1) page.value = 1
  if (!parsedDateRange.value.valid) {
    window.clearTimeout(commitTimer)
    void load()
    return
  }
  queueCommit(delay)
}

function applyRouteFilters() {
  syncingFromRoute = true
  search.value = queryString(route.query.q)
  type.value = validType(queryString(route.query.type))
  status.value = validStatus(queryString(route.query.status))
  asset.value = queryString(route.query.asset).toUpperCase() || 'all'
  network.value = queryString(route.query.network).toUpperCase()
  fromDate.value = queryDateInput(route.query.from)
  toDate.value = queryDateInput(route.query.to)
  page.value = queryPage(route.query.page)
  syncingFromRoute = false
  void load()
}

function normalizeDateField(field: 'from' | 'to') {
  const target = field === 'from' ? fromDate : toDate
  const serialized = serializePersianDateInput(target.value)
  if (serialized) target.value = toPersianDigits(serialized.replace(/-/g, '/'))
}

function normalizeNetwork() {
  network.value = normalizeDigits(network.value).trim().toUpperCase().replace(/[^A-Z0-9_-]/g, '')
}

function clearFilters() {
  search.value = ''
  type.value = 'all'
  status.value = 'all'
  asset.value = 'all'
  network.value = ''
  fromDate.value = ''
  toDate.value = ''
}

watch([type, status, asset, network], () => { resetPageAndCommit() }, { flush: 'sync' })
watch([search, fromDate, toDate], () => { resetPageAndCommit(350) }, { flush: 'sync' })
watch(page, () => {
  if (!syncingFromRoute) {
    listRequestSequence += 1
    queueCommit()
  }
}, { flush: 'sync' })
watch(
  () => filterQueryKeys.map((key) => {
    const value = route.query[key]
    return Array.isArray(value) ? value.join(',') : String(value ?? '')
  }).join('\u001f'),
  applyRouteFilters,
)
watch(() => route.query.detail, (value) => { void openDetail(typeof value === 'string' ? value : null) })
onMounted(() => {
  void load()
  void openDetail(typeof route.query.detail === 'string' ? route.query.detail : null)
})
onBeforeUnmount(() => {
  listRequestSequence += 1
  detailRequestSequence += 1
  window.clearTimeout(commitTimer)
})
</script>

<template>
  <div class="page transactions-page">
    <PageHeader title="تراکنش‌ها" description="گردش کامل تومان و رمزارز در حساب شما" />
    <AppCard padding="none">
      <div class="transaction-toolbar">
        <AppInput v-model="search" class="transaction-search" label="جست‌وجو" icon="search" type="search" inputmode="search" placeholder="شماره پیگیری یا TXID…" />
        <button class="mobile-filter-toggle" type="button" :aria-expanded="mobileFiltersOpen" aria-controls="transaction-advanced-filters" @click="mobileFiltersOpen = !mobileFiltersOpen"><AppIcon name="filter" :size="17" />فیلترها<span v-if="hasActiveFilters">فعال</span></button>
        <div id="transaction-advanced-filters" class="transaction-filter-controls" :class="{ 'is-mobile-open': mobileFiltersOpen }">
          <AppSelect v-model="type" :options="transactionTypeOptions" label="نوع تراکنش" searchable search-placeholder="جست‌وجوی نوع تراکنش" />
          <AppSelect v-model="asset" :options="assetOptions" label="دارایی" searchable search-placeholder="جست‌وجوی نام یا نماد دارایی" />
          <AppSelect v-model="status" :options="transactionStatusOptions" label="وضعیت" />
        </div>
      </div>
      <div class="date-range-toolbar" :class="{ 'is-mobile-open': mobileFiltersOpen }" aria-label="بازه زمانی تراکنش‌ها">
        <div class="date-range-heading"><AppIcon name="calendar" :size="19" /><span><strong>بازه تاریخ شمسی</strong><small>تاریخ‌ها بر اساس زمان تهران محاسبه می‌شوند.</small></span></div>
        <AppInput v-model="fromDate" label="از تاریخ" icon="calendar" inputmode="numeric" ltr maxlength="10" placeholder="۱۴۰۵/۰۶/۰۱" :error="parsedDateRange.fromError" @blur="normalizeDateField('from')" />
        <AppInput v-model="toDate" label="تا تاریخ" icon="calendar" inputmode="numeric" ltr maxlength="10" placeholder="۱۴۰۵/۰۶/۳۱" :error="parsedDateRange.toError" @blur="normalizeDateField('to')" />
        <AppInput v-model="network" label="شبکه (اختیاری)" inputmode="text" ltr maxlength="20" placeholder="TRC20" @blur="normalizeNetwork" />
      </div>
      <div class="filter-summary"><span><AppIcon name="filter" :size="16" /> {{ totalResults.toLocaleString('fa-IR') }} نتیجه</span><button v-if="hasActiveFilters" type="button" @click="clearFilters">پاک کردن فیلترها</button></div>
      <div v-if="loading" class="skeleton"><AppSkeleton v-for="i in 6" :key="i" height="4.9rem" /></div>
      <TransactionList v-else-if="transactions.length" :transactions="transactions" />
      <EmptyState v-else-if="!error" icon="transactions" title="هنوز تراکنشی با این مشخصات ندارید" description="فیلترها را تغییر دهید یا اولین واریز تومان خود را انجام دهید."><RouterLink class="empty-action" to="/app/deposit/toman">واریز تومان</RouterLink></EmptyState>
      <EmptyState v-else icon="warning" title="تراکنش‌ها دریافت نشد" :description="error"><button class="empty-action" type="button" @click="load">تلاش دوباره</button></EmptyState>
      <AppPagination v-model="page" :total-pages="totalPages" />
    </AppCard>

    <AppModal :model-value="!!detail" title="جزئیات تراکنش" size="md" @update:model-value="!$event && closeDetail()">
      <template v-if="detail">
        <div class="detail-top"><span class="detail-icon"><AppIcon :name="detail.type.includes('deposit') ? 'arrowDown' : detail.type.includes('withdrawal') ? 'arrowUp' : 'trade'" :size="25" /></span><div><span>{{ detail.title }}</span><MoneyValue v-if="detail.assetSymbol === 'IRT'" :value="detail.amount" /><CryptoValue v-else :value="detail.amount" :symbol="detail.assetSymbol" /></div><StatusBadge domain="transaction" :status="detail.status" /></div>
        <dl class="transaction-details"><div><dt>شماره پیگیری</dt><dd><bdi>{{ detail.referenceNumber }}</bdi><CopyButton :value="detail.referenceNumber" label="" /></dd></div><div v-if="detail.tomanAmount"><dt>ارزش تومان</dt><dd>{{ formatToman(detail.tomanAmount) }}</dd></div><div v-if="detail.fee"><dt>{{ detail.networkCode ? 'کارمزد شبکه' : 'کارمزد' }}</dt><dd>{{ detail.assetSymbol === 'IRT' ? formatToman(detail.fee) : formatCrypto(detail.fee, { symbol: detail.assetSymbol }) }}</dd></div><div v-if="detail.networkCode"><dt>شبکه</dt><dd dir="ltr">{{ detail.networkCode }}</dd></div><div v-if="detail.address" class="technical"><dt>آدرس مقصد</dt><dd><bdi>{{ detail.address }}</bdi><CopyButton :value="detail.address" label="" /></dd></div><div v-if="detail.txId" class="technical"><dt>TXID</dt><dd><bdi>{{ detail.txId }}</bdi><CopyButton :value="detail.txId" label="" /></dd></div><div v-if="detail.confirmations !== undefined"><dt>تأییدهای شبکه</dt><dd>{{ detail.confirmations?.toLocaleString('fa-IR') }} از {{ detail.requiredConfirmations?.toLocaleString('fa-IR') }}</dd></div><div><dt>زمان ثبت</dt><dd>{{ formatPersianDateTime(detail.createdAt) }}</dd></div></dl>
        <div v-if="detail.txId" class="network-note"><AppIcon name="info" :size="18" /> شناسه تراکنش برای پیگیری روی شبکه عمومی نمایش داده می‌شود.</div>
      </template>
      <template #footer><button class="close-detail" type="button" @click="closeDetail">بستن</button><RouterLink class="support-link" to="/app/support" @click="closeDetail">پیگیری از پشتیبانی</RouterLink></template>
    </AppModal>
  </div>
</template>

<style scoped>
.transactions-page { max-width: 86rem; }
.transaction-toolbar { display: grid; grid-template-columns: minmax(15rem, 1fr) minmax(33rem, 1.6fr); align-items: end; gap: var(--space-3); padding: var(--space-5); }
.transaction-filter-controls { display: grid; min-width: 0; grid-template-columns: repeat(3, minmax(10rem, 1fr)); align-items: start; gap: var(--space-3); }
.mobile-filter-toggle { display: none; min-height: 2.75rem; align-items: center; justify-content: center; gap: var(--space-2); padding-inline: var(--space-3); border: 1px solid var(--control-border); border-radius: var(--radius-md); background: var(--color-surface-2); color: var(--color-text-secondary); font-size: var(--font-size-xs); font-weight: 650; white-space: nowrap; }
.mobile-filter-toggle span { padding: .12rem .42rem; border-radius: var(--radius-pill); background: var(--color-primary-soft); color: var(--color-primary); font-size: .62rem; }
.date-range-toolbar { display: grid; grid-template-columns: minmax(12rem, .8fr) repeat(3, minmax(10rem, 1fr)); align-items: start; gap: var(--space-3); padding: 0 var(--space-5) var(--space-5); }
.date-range-heading { display: flex; min-height: var(--control-height); align-items: center; gap: var(--space-2); margin-top: 1.65rem; color: var(--color-primary); }
.date-range-heading span { display: grid; }
.date-range-heading strong { color: var(--color-text-secondary); font-size: var(--font-size-sm); }
.date-range-heading small { color: var(--color-text-muted); font-size: var(--font-size-xs); }
.filter-summary { display: flex; align-items: center; justify-content: space-between; gap: var(--space-3); padding: .65rem var(--space-5); border-block: 1px solid var(--color-border-soft); background: var(--color-surface-2); color: var(--color-text-muted); font-size: var(--font-size-xs); }
.filter-summary span { display: inline-flex; align-items: center; gap: var(--space-2); }
.filter-summary button { border: 0; background: transparent; color: var(--color-primary); font-size: inherit; }
.skeleton { display: grid; gap: 1px; padding: var(--space-3); }
.empty-action, .close-detail, .support-link { display: inline-flex; min-height: 2.65rem; align-items: center; justify-content: center; padding-inline: var(--space-4); border: 1px solid var(--action-primary); border-radius: var(--radius-sm); background: var(--action-primary); color: var(--on-primary); font-weight: 600; }
.detail-top { display: grid; grid-template-columns: auto 1fr auto; align-items: center; gap: var(--space-3); padding: var(--space-4); border-radius: var(--radius-lg); background: var(--color-surface-2); }
.detail-icon { display: grid; width: 3.3rem; height: 3.3rem; border-radius: 1rem; background: var(--color-primary-soft); color: var(--color-primary); place-items: center; }
.detail-top > div { display: grid; }
.detail-top > div span { color: var(--color-text-muted); font-size: var(--font-size-xs); }
.detail-top > div > :deep(.money-value strong), .detail-top > div > :deep(.crypto-value strong) { color: var(--color-text-primary); font-size: var(--font-size-lg); font-weight: 700; }
.transaction-details { display: grid; gap: var(--space-3); margin: var(--space-5) 0; }
.transaction-details > div { display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); padding-bottom: var(--space-3); border-block-end: 1px solid var(--color-border-soft); }
.transaction-details dt { flex: 0 0 auto; color: var(--color-text-muted); }
.transaction-details dd { display: flex; min-width: 0; flex-wrap: wrap; align-items: center; justify-content: flex-end; gap: var(--space-2); margin: 0; line-height: 1.6; text-align: end; }
.transaction-details bdi { overflow: hidden; direction: ltr; text-overflow: ellipsis; white-space: nowrap; }
.technical dd { max-width: 70%; }
.technical :deep(.copy-button span) { display: none; }
.network-note { display: flex; gap: var(--space-2); padding: var(--space-3); border-radius: var(--radius-md); background: var(--color-info-soft); color: var(--color-info); font-size: var(--font-size-xs); }
.close-detail { border-color: var(--color-border); background: var(--color-surface-2); color: var(--color-text-secondary); }
.support-link { flex: 1; }
@media (max-width: 1050px) {
  .transaction-toolbar { grid-template-columns: 1fr; }
  .date-range-toolbar { grid-template-columns: 1fr 1fr; }
  .transaction-filter-controls { grid-column: 1 / -1; grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .date-range-heading { grid-column: 1 / -1; margin-top: 0; }
}
@media (max-width: 767px) {
  .transaction-toolbar { grid-template-columns: minmax(0, 1fr) auto; padding: var(--space-4); }
  .mobile-filter-toggle { display: inline-flex; }
  .transaction-filter-controls { display: none; grid-column: 1 / -1; grid-template-columns: 1fr 1fr; }
  .transaction-filter-controls.is-mobile-open { display: grid; }
  .date-range-toolbar { display: none; grid-template-columns: 1fr 1fr; padding: 0 var(--space-4) var(--space-4); }
  .date-range-toolbar.is-mobile-open { display: grid; }
  .date-range-heading, .date-range-toolbar > :last-child { grid-column: 1 / -1; }
  .detail-top { grid-template-columns: auto 1fr; }
  .detail-top :deep(.status) { grid-column: 2; }
  .transaction-details { font-size: var(--font-size-sm); }
  .technical { align-items: flex-start !important; flex-direction: column; }
  .technical dd { width: 100%; max-width: 100%; }
  .filter-summary { padding-inline: var(--space-4); }
}
@media (max-width: 560px) {
  .transaction-filter-controls, .date-range-toolbar { grid-template-columns: minmax(0, 1fr); }
  .date-range-heading, .date-range-toolbar > :last-child { grid-column: auto; }
  .filter-summary { flex-wrap: wrap; }
  .filter-summary button { min-height: 2.75rem; }
}
</style>
