<script setup lang="ts">
import {computed, onBeforeUnmount, onMounted, ref, watch,} from 'vue'
import {type LocationQueryRaw, useRoute, useRouter,} from 'vue-router'

import type {Transaction, TransactionFilters,} from '@/types'

import {transactionService} from '@/services/transaction.service'

import {
  formatCrypto,
  formatPersianDate,
  formatPersianDateTime,
  formatToman,
  normalizeDigits,
  toPersianDigits,
} from '@/utils/formatters'

import {persianDateBoundaryIso, serializePersianDateInput,} from '@/utils/persianDateInput'
import PersianDatePicker from '@/components/ui/PersianDatePicker.vue'
import AppButton from '@/components/ui/AppButton.vue'
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
import CryptoValue from '@/components/finance/CryptoValue.vue'
import MoneyValue from '@/components/finance/MoneyValue.vue'



const PAGE_SIZE = 8

const transactionTypes = new Set([
  'buy',
  'sell',
  'toman_deposit',
  'toman_withdrawal',
  'crypto_deposit',
  'crypto_withdrawal',
  'fee',
  'refund',
  'reversal',
])

const transactionStatuses = new Set([
  'pending',
  'processing',
  'completed',
  'failed',
  'cancelled',
  'reversed',
])

const transactionTypeOptions = [
  {
    value: 'all',
    label: 'همه نوع‌ها',
  },
  {
    value: 'buy',
    label: 'خرید',
  },
  {
    value: 'sell',
    label: 'فروش',
  },
  {
    value: 'toman_deposit',
    label: 'واریز تومان',
  },
  {
    value: 'toman_withdrawal',
    label: 'برداشت تومان',
  },
  {
    value: 'crypto_deposit',
    label: 'واریز رمزارز',
  },
  {
    value: 'crypto_withdrawal',
    label: 'برداشت رمزارز',
  },
  {
    value: 'fee',
    label: 'کارمزد',
  },
  {
    value: 'refund',
    label: 'بازپرداخت',
  },
  {
    value: 'reversal',
    label: 'برگشت تراکنش',
  },
]

const assetOptions = [
  {
    value: 'all',
    label: 'همه دارایی‌ها',
  },
  {
    value: 'IRT',
    label: 'تومان',
    description: 'IRT',
  },
  {
    value: 'USDT',
    label: 'تتر',
    description: 'USDT',
  },
  {
    value: 'BTC',
    label: 'بیت‌کوین',
    description: 'BTC',
  },
  {
    value: 'ETH',
    label: 'اتریوم',
    description: 'ETH',
  },
  {
    value: 'TRX',
    label: 'ترون',
    description: 'TRX',
  },
]

const transactionStatusOptions = [
  {
    value: 'all',
    label: 'همه وضعیت‌ها',
  },
  {
    value: 'pending',
    label: 'در انتظار بررسی',
  },
  {
    value: 'processing',
    label: 'در حال پردازش',
  },
  {
    value: 'completed',
    label: 'تکمیل‌شده',
  },
  {
    value: 'failed',
    label: 'ناموفق',
  },
  {
    value: 'cancelled',
    label: 'لغوشده',
  },
  {
    value: 'reversed',
    label: 'برگشت‌خورده',
  },
]

const filterQueryKeys = [
  'q',
  'type',
  'status',
  'asset',
  'network',
  'from',
  'to',
  'page',
] as const



const route = useRoute()
const router = useRouter()

const transactions = ref<Transaction[]>([])
const detail = ref<Transaction | null>(null)

const loading = ref(true)
const error = ref('')
const totalResults = ref(0)

const page = ref(
    queryPage(route.query.page),
)

const totalPages = ref(1)

const search = ref(
    queryString(route.query.q),
)

const type = ref(
    validType(
        queryString(route.query.type),
    ),
)

const status = ref(
    validStatus(
        queryString(route.query.status),
    ),
)

const asset = ref(
    queryString(route.query.asset)
        .toUpperCase()
    || 'all',
)

const network = ref(
    queryString(route.query.network)
        .toUpperCase(),
)

const fromDate = ref(
    queryDateInput(route.query.from),
)

const toDate = ref(
    queryDateInput(route.query.to),
)

const mobileFiltersOpen = ref(false)

let commitTimer: number | undefined

let listRequestSequence = 0
let detailRequestSequence = 0

let syncingFromRoute = false



function queryString(
    value: unknown,
): string {
  return typeof value === 'string'
      ? value
      : ''
}

function queryPage(
    value: unknown,
): number {
  const parsed = Number(
      queryString(value),
  )

  return Number.isInteger(parsed)
  && parsed > 0
      ? parsed
      : 1
}

function validType(
    value: string,
): string {
  return transactionTypes.has(value)
      ? value
      : 'all'
}

function validStatus(
    value: string,
): string {
  return transactionStatuses.has(value)
      ? value
      : 'all'
}

function queryDateInput(
    value: unknown,
): string {
  const raw = queryString(value).trim()

  if (!raw) {
    return ''
  }

  const normalized =
      normalizeDigits(raw)

  if (
      /^1[2-7]\d{2}[-/]\d{1,2}[-/]\d{1,2}$/
          .test(normalized)
  ) {
    return toPersianDigits(
        normalized.replace(
            /-/g,
            '/',
        ),
    )
  }

  const date = new Date(raw)

  if (Number.isNaN(date.getTime())) {
    return toPersianDigits(
        normalized,
    )
  }

  return formatPersianDate(date)
}



const parsedDateRange = computed(() => {
  const from =
      fromDate.value.trim()
          ? persianDateBoundaryIso(
              fromDate.value,
              'start',
          )
          : undefined

  const to =
      toDate.value.trim()
          ? persianDateBoundaryIso(
              toDate.value,
              'end',
          )
          : undefined

  let fromError =
      fromDate.value.trim() && !from
          ? 'تاریخ شروع معتبر نیست؛ نمونه: ۱۴۰۵/۰۶/۰۱'
          : ''

  let toError =
      toDate.value.trim() && !to
          ? 'تاریخ پایان معتبر نیست؛ نمونه: ۱۴۰۵/۰۶/۳۱'
          : ''

  if (
      !fromError
      && !toError
      && from
      && to
      && Date.parse(from) > Date.parse(to)
  ) {
    fromError =
        'تاریخ شروع باید پیش از تاریخ پایان باشد.'

    toError =
        'تاریخ پایان باید پس از تاریخ شروع باشد.'
  }

  return {
    from,
    to,
    fromError,
    toError,
    valid:
        !fromError
        && !toError,
  }
})



const hasActiveFilters = computed(() =>
        type.value !== 'all'
        || asset.value !== 'all'
        || status.value !== 'all'
        || Boolean(
            network.value
            || search.value
            || fromDate.value
            || toDate.value,
        ),
)



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

  const requestId =
      ++listRequestSequence

  loading.value = true
  error.value = ''

  const filters: TransactionFilters = {
    page: page.value,
    pageSize: PAGE_SIZE,
    search: search.value.trim(),
  }

  if (type.value !== 'all') {
    filters.type =
        type.value as TransactionFilters['type']
  }

  if (status.value !== 'all') {
    filters.status =
        status.value as TransactionFilters['status']
  }

  if (asset.value !== 'all') {
    filters.assetSymbol =
        asset.value
  }

  if (network.value) {
    filters.networkCode =
        network.value
  }

  if (parsedDateRange.value.from) {
    filters.from =
        parsedDateRange.value.from
  }

  if (parsedDateRange.value.to) {
    filters.to =
        parsedDateRange.value.to
  }

  try {
    const result =
        await transactionService.list(
            filters,
        )

    if (
        requestId
        !== listRequestSequence
    ) {
      return
    }

    transactions.value =
        result.items

    totalResults.value =
        result.total

    totalPages.value =
        Math.max(
            1,
            result.totalPages,
        )

    const resolvedPage =
        Math.max(
            1,
            Math.min(
                result.page,
                totalPages.value,
            ),
        )

    if (
        page.value
        !== resolvedPage
    ) {
      page.value =
          resolvedPage
    }
  } catch (reason) {
    if (
        requestId
        === listRequestSequence
    ) {
      error.value =
          reason instanceof Error
              ? reason.message
              : 'دریافت تراکنش‌ها ممکن نشد.'
    }
  } finally {
    if (
        requestId
        === listRequestSequence
    ) {
      loading.value = false
    }
  }
}


const openDetail = async (
    id: string | null,
) => {
  const requestId =
      ++detailRequestSequence

  if (!id) {
    detail.value = null
    return
  }

  try {
    const response =
        await transactionService.getById(
            id,
        )

    if (
        requestId
        === detailRequestSequence
    ) {
      detail.value = response
    }
  } catch {
    if (
        requestId
        === detailRequestSequence
    ) {
      detail.value = null
    }
  }
}

const closeDetail = () => {
  detailRequestSequence += 1
  detail.value = null

  const query = {
    ...route.query,
  }

  delete query.detail

  void router.replace({
    query,
  })
}


function sameFilterQuery(
    next: LocationQueryRaw,
): boolean {
  return filterQueryKeys.every(
      (key) =>
          String(
              next[key] ?? '',
          )
          === queryString(
              route.query[key],
          ),
  )
}

function commitFilters() {
  if (!parsedDateRange.value.valid) {
    return
  }

  const query: LocationQueryRaw = {
    ...route.query,
  }

  filterQueryKeys.forEach(
      (key) => {
        delete query[key]
      },
  )

  if (search.value.trim()) {
    query.q =
        search.value.trim()
  }

  if (type.value !== 'all') {
    query.type =
        type.value
  }

  if (status.value !== 'all') {
    query.status =
        status.value
  }

  if (asset.value !== 'all') {
    query.asset =
        asset.value
  }

  if (network.value.trim()) {
    query.network =
        network.value
            .trim()
            .toUpperCase()
  }

  const serializedFrom =
      serializePersianDateInput(
          fromDate.value,
      )

  const serializedTo =
      serializePersianDateInput(
          toDate.value,
      )

  if (serializedFrom) {
    query.from =
        serializedFrom
  }

  if (serializedTo) {
    query.to =
        serializedTo
  }

  if (page.value > 1) {
    query.page =
        String(page.value)
  }

  if (sameFilterQuery(query)) {
    void load()
    return
  }

  void router.replace({
    query,
  })
}

function queueCommit(
    delay = 0,
) {
  window.clearTimeout(
      commitTimer,
  )

  commitTimer =
      window.setTimeout(
          commitFilters,
          delay,
      )
}

function resetPageAndCommit(
    delay = 0,
) {
  if (syncingFromRoute) {
    return
  }

  listRequestSequence += 1

  if (page.value !== 1) {
    page.value = 1
  }

  if (!parsedDateRange.value.valid) {
    window.clearTimeout(
        commitTimer,
    )

    void load()
    return
  }

  queueCommit(delay)
}

function applyRouteFilters() {
  syncingFromRoute = true

  search.value =
      queryString(route.query.q)

  type.value =
      validType(
          queryString(
              route.query.type,
          ),
      )

  status.value =
      validStatus(
          queryString(
              route.query.status,
          ),
      )

  asset.value =
      queryString(
          route.query.asset,
      )
          .toUpperCase()
      || 'all'

  network.value =
      queryString(
          route.query.network,
      )
          .toUpperCase()

  fromDate.value =
      queryDateInput(
          route.query.from,
      )

  toDate.value =
      queryDateInput(
          route.query.to,
      )

  page.value =
      queryPage(
          route.query.page,
      )

  syncingFromRoute = false

  void load()
}



function normalizeNetwork() {
  network.value =
      normalizeDigits(
          network.value,
      )
          .trim()
          .toUpperCase()
          .replace(
              /[^A-Z0-9_-]/g,
              '',
          )
}


function clearFilters() {
  window.clearTimeout(
      commitTimer,
  )

  syncingFromRoute = true

  search.value = ''
  type.value = 'all'
  status.value = 'all'
  asset.value = 'all'
  network.value = ''
  fromDate.value = ''
  toDate.value = ''
  page.value = 1

  syncingFromRoute = false

  listRequestSequence += 1

  detailRequestSequence += 1
  detail.value = null

  const query: LocationQueryRaw = {
    ...route.query,
  }

  filterQueryKeys.forEach(
      (key) => {
        delete query[key]
      },
  )

  delete query.detail

  void router.replace({
    query,
  })
}


watch(
    [type, status, asset, network],
    () => {
      resetPageAndCommit()
    },
    {
      flush: 'sync',
    },
)

watch(
    [search, fromDate, toDate],
    () => {
      resetPageAndCommit(350)
    },
    {
      flush: 'sync',
    },
)

watch(
    page,
    () => {
      if (!syncingFromRoute) {
        listRequestSequence += 1
        queueCommit()
      }
    },
    {
      flush: 'sync',
    },
)

watch(
    () =>
        filterQueryKeys
            .map((key) => {
              const value =
                  route.query[key]

              return Array.isArray(value)
                  ? value.join(',')
                  : String(value ?? '')
            })
            .join('\u001f'),
    applyRouteFilters,
)

watch(
    () => route.query.detail,
    (value) => {
      void openDetail(
          typeof value === 'string'
              ? value
              : null,
      )
    },
)


onMounted(() => {
  void load()

  void openDetail(
      typeof route.query.detail === 'string'
          ? route.query.detail
          : null,
  )
})

onBeforeUnmount(() => {
  listRequestSequence += 1
  detailRequestSequence += 1

  window.clearTimeout(
      commitTimer,
  )
})
</script>


<template>
  <div class="page transactions-page">

    <!-- ------------------------------------------------------------------ -->
    <!-- Header                                                             -->
    <!-- ------------------------------------------------------------------ -->

    <PageHeader
        title="تراکنش‌ها"
        description="گردش کامل تومان و رمزارز در حساب شما"
    >
      <template #actions>
        <AppButton
            variant="secondary"
            size="sm"
            icon="refresh"
            :loading="loading"
            @click="load"
        >
          به‌روزرسانی
        </AppButton>
      </template>
    </PageHeader>


    <AppCard padding="none">

      <!-- --------------------------------------------------------------- -->
      <!-- Filters                                                         -->
      <!-- --------------------------------------------------------------- -->

      <section
          class="transaction-filters"
          aria-label="فیلتر تراکنش‌ها"
      >

        <div class="filters-header">

          <div class="filters-title">
    <span class="filters-title-icon">
      <AppIcon
          name="filter"
          :size="17"
      />
    </span>

            <div>
              <strong>
                فیلتر تراکنش‌ها
              </strong>

              <small>
                جست‌وجو و محدود کردن نتایج بر اساس مشخصات تراکنش
              </small>
            </div>
          </div>

          <div class="filters-header-actions">

            <button
                class="reset-filters-button"
                :class="{ 'is-disabled': !hasActiveFilters }"
                type="button"
                :disabled="!hasActiveFilters"
                @click="clearFilters"
            >
              <AppIcon
                  name="refresh"
                  :size="15"
              />

              ریست فیلترها
            </button>

            <button
                class="mobile-filter-toggle"
                type="button"
                :aria-expanded="mobileFiltersOpen"
                aria-controls="transaction-filter-panel"
                @click="
        mobileFiltersOpen =
          !mobileFiltersOpen
      "
            >
              <AppIcon
                  name="filter"
                  :size="17"
              />

              فیلترها

              <span
                  v-if="hasActiveFilters"
              >
        فعال
      </span>
            </button>

          </div>

        </div>


        <div
            id="transaction-filter-panel"
            class="transaction-filter-panel"
            :class="{
            'is-mobile-open':
              mobileFiltersOpen,
          }"
        >

          <div class="filter-field search-field">
            <AppInput
                v-model="search"
                label="جست‌وجو"
                icon="search"
                type="search"
                inputmode="search"
                placeholder="شماره پیگیری یا TXID…"
            />
          </div>


          <div class="filter-field">
            <AppSelect
                v-model="type"
                :options="
                transactionTypeOptions
              "
                label="نوع تراکنش"
                searchable
                search-placeholder="جست‌وجوی نوع تراکنش"
            />
          </div>


          <div class="filter-field">
            <AppSelect
                v-model="asset"
                :options="assetOptions"
                label="دارایی"
                searchable
                search-placeholder="جست‌وجوی نام یا نماد دارایی"
            />
          </div>


          <div class="filter-field">
            <AppSelect
                v-model="status"
                :options="
                transactionStatusOptions
              "
                label="وضعیت"
            />
          </div>

        </div>


        <div
            class="date-range-section"
            :class="{
            'is-mobile-open':
              mobileFiltersOpen,
          }"
        >

          <div class="date-range-heading">

            <span class="date-range-icon">
              <AppIcon
                  name="calendar"
                  :size="18"
              />
            </span>

            <div>
              <strong>
                بازه زمانی
              </strong>

              <small>
                تاریخ‌ها بر اساس زمان تهران محاسبه می‌شوند.
              </small>
            </div>

          </div>


          <div class="filter-field">
            <PersianDatePicker
                v-model="fromDate"
                label="از تاریخ"
                placeholder="۱۴۰۵/۰۶/۰۱"
                :error="parsedDateRange.fromError"
            />
          </div>

          <div class="filter-field">
            <PersianDatePicker
                v-model="toDate"
                label="تا تاریخ"
                placeholder="۱۴۰۵/۰۶/۳۱"
                :error="parsedDateRange.toError"
            />
          </div>


          <div class="filter-field">
            <AppInput
                v-model="network"
                label="شبکه"
                inputmode="text"
                ltr
                maxlength="20"
                placeholder="مثلاً TRC20"
                @blur="normalizeNetwork"
            />
          </div>

        </div>


        <div class="filter-summary">

          <div class="filter-summary-left">
            <span class="result-indicator">
              <AppIcon
                  name="filter"
                  :size="15"
              />

              <strong>
                {{ totalResults.toLocaleString('fa-IR') }}
              </strong>

              <span>
                نتیجه
              </span>
            </span>

            <span
                v-if="hasActiveFilters"
                class="active-filter-indicator"
            >
              فیلتر فعال است
            </span>
          </div>


        </div>

      </section>


      <div
          v-if="loading"
          class="transaction-loading"
      >
        <div
            v-for="i in 6"
            :key="i"
            class="transaction-loading-row"
        >
          <AppSkeleton
              height="4.4rem"
          />
        </div>
      </div>


      <div
          v-else-if="transactions.length"
          class="transactions-table-wrap"
      >

        <div class="transactions-table">

          <!-- Table header -->

          <div class="transactions-table-head">

            <div class="head-transaction">
              تراکنش
            </div>

            <div class="head-amount">
              مبلغ
            </div>

            <div class="head-toman">
              معادل تومان
            </div>

            <div class="head-date">
              زمان ثبت
            </div>

            <div class="head-status">
              وضعیت
            </div>

            <div class="head-action"></div>

          </div>


          <!-- Table rows -->

          <button
              v-for="transaction in transactions"
              :key="transaction.id"
              class="transaction-row"
              type="button"
              @click="
              openDetail(
                String(transaction.id),
              )
            "
          >

            <!-- Transaction -->

            <div class="transaction-primary">

              <span class="transaction-icon">
                <AppIcon
                    :name="
                    transaction.type.includes('deposit')
                      ? 'arrowDown'
                      : transaction.type.includes('withdrawal')
                        ? 'arrowUp'
                        : 'trade'
                  "
                    :size="18"
                />
              </span>


              <span class="transaction-main-text">

                <strong>
                  {{ transaction.title }}
                </strong>

                <small>
                  <bdi>
                    {{ transaction.referenceNumber }}
                  </bdi>
                </small>

              </span>

            </div>


            <!-- Amount -->

            <div class="transaction-amount-cell">

              <MoneyValue
                  v-if="
                  transaction.assetSymbol
                  === 'IRT'
                "
                  :value="
                  transaction.amount
                "
              />

              <CryptoValue
                  v-else
                  :value="
                  transaction.amount
                "
                  :symbol="
                  transaction.assetSymbol
                "
              />

            </div>


            <!-- Toman -->

            <div class="transaction-toman-cell">

              <span
                  v-if="
                  transaction.tomanAmount
                  && transaction.tomanAmount
                  !== '0'
                "
              >
                {{
                  formatToman(
                      transaction.tomanAmount,
                  )
                }}
              </span>

              <span
                  v-else
                  class="muted-value"
              >
                —
              </span>

            </div>


            <!-- Date -->

            <div class="transaction-date-cell">

              <strong>
                {{
                  formatPersianDate(
                      transaction.createdAt,
                  )
                }}
              </strong>

              <small>
                {{
                  formatPersianDateTime(
                      transaction.createdAt,
                  )
                }}
              </small>

            </div>


            <!-- Status -->

            <div class="transaction-status-cell">

              <StatusBadge
                  domain="transaction"
                  :status="
                  transaction.status
                "
              />

            </div>


            <!-- Action -->

            <div class="transaction-action-cell">

              <span class="transaction-details-link">
                مشاهده

                <AppIcon
                    name="chevronLeft"
                    :size="15"
                />
              </span>

            </div>

          </button>

        </div>

      </div>


      <EmptyState
          v-else-if="!error"
          icon="transactions"
          title="هنوز تراکنشی با این مشخصات ندارید"
          description="فیلترها را تغییر دهید یا اولین واریز تومان خود را انجام دهید."
      >
        <RouterLink
            class="empty-action"
            to="/app/deposit/toman"
        >
          واریز تومان
        </RouterLink>
      </EmptyState>


      <EmptyState
          v-else
          icon="warning"
          title="تراکنش‌ها دریافت نشد"
          :description="error"
      >
        <button
            class="empty-action"
            type="button"
            @click="load"
        >
          تلاش دوباره
        </button>
      </EmptyState>


      <div
          v-if="
          !loading
          && transactions.length
        "
          class="pagination-wrap"
      >
        <AppPagination
            v-model="page"
            :total-pages="totalPages"
        />
      </div>

    </AppCard>


    <!-- ================================================================== -->
    <!-- Detail Modal                                                       -->
    <!-- ================================================================== -->

    <AppModal
        :model-value="!!detail"
        title="جزئیات تراکنش"
        size="md"
        @update:model-value="
        !$event && closeDetail()
      "
    >

      <template v-if="detail">

        <div class="detail-top">

          <span class="detail-icon">
            <AppIcon
                :name="
                detail.type.includes('deposit')
                  ? 'arrowDown'
                  : detail.type.includes('withdrawal')
                    ? 'arrowUp'
                    : 'trade'
              "
                :size="25"
            />
          </span>


          <div class="detail-heading">

            <span>
              {{ detail.title }}
            </span>

            <MoneyValue
                v-if="
                detail.assetSymbol === 'IRT'
              "
                :value="detail.amount"
            />

            <CryptoValue
                v-else
                :value="detail.amount"
                :symbol="detail.assetSymbol"
            />

          </div>


          <StatusBadge
              domain="transaction"
              :status="detail.status"
          />

        </div>


        <dl class="transaction-details">

          <!-- Reference -->

          <div>

            <dt>
              شماره پیگیری
            </dt>

            <dd>

              <bdi>
                {{ detail.referenceNumber }}
              </bdi>

              <CopyButton
                  :value="
                  detail.referenceNumber
                "
                  label=""
              />

            </dd>

          </div>


          <!-- Toman value -->

          <div
              v-if="
              detail.tomanAmount
              && detail.tomanAmount
              !== '0'
            "
          >

            <dt>
              ارزش تومان
            </dt>

            <dd>
              {{
                formatToman(
                    detail.tomanAmount,
                )
              }}
            </dd>

          </div>


          <!-- Fee -->

          <div
              v-if="
              detail.fee
              && detail.fee !== '0'
            "
          >

            <dt>
              {{
                detail.networkCode
                    ? 'کارمزد شبکه'
                    : 'کارمزد'
              }}
            </dt>

            <dd>
              {{
                detail.assetSymbol === 'IRT'
                    ? formatToman(
                        detail.fee,
                    )
                    : formatCrypto(
                        detail.fee,
                        {
                          symbol:
                          detail.assetSymbol,
                        },
                    )
              }}
            </dd>

          </div>


          <!-- Network -->

          <div
              v-if="detail.networkCode"
          >

            <dt>
              شبکه
            </dt>

            <dd>
              <bdi dir="ltr">
                {{ detail.networkCode }}
              </bdi>
            </dd>

          </div>


          <!-- Address -->

          <div
              v-if="detail.address"
              class="technical"
          >

            <dt>
              آدرس مقصد
            </dt>

            <dd>

              <bdi>
                {{ detail.address }}
              </bdi>

              <CopyButton
                  :value="detail.address"
                  label=""
              />

            </dd>

          </div>


          <!-- TXID -->

          <div
              v-if="detail.txId"
              class="technical"
          >

            <dt>
              TXID
            </dt>

            <dd>

              <bdi>
                {{ detail.txId }}
              </bdi>

              <CopyButton
                  :value="detail.txId"
                  label=""
              />

            </dd>

          </div>


          <!-- Confirmations -->

          <div
              v-if="
              detail.confirmations
              !== undefined
            "
          >

            <dt>
              تأییدهای شبکه
            </dt>

            <dd>
              {{
                detail.confirmations
                    ?.toLocaleString(
                        'fa-IR',
                    )
              }}
              از
              {{
                detail.requiredConfirmations
                    ?.toLocaleString(
                        'fa-IR',
                    )
              }}
            </dd>

          </div>


          <!-- Created -->

          <div>

            <dt>
              زمان ثبت
            </dt>

            <dd>
              {{
                formatPersianDateTime(
                    detail.createdAt,
                )
              }}
            </dd>

          </div>

        </dl>


        <div
            v-if="detail.description"
            class="detail-description"
        >
          <AppIcon
              name="info"
              :size="17"
          />

          <span>
            {{ detail.description }}
          </span>
        </div>


        <div
            v-if="detail.txId"
            class="network-note"
        >
          <AppIcon
              name="info"
              :size="18"
          />

          <span>
            شناسه تراکنش برای پیگیری روی شبکه عمومی نمایش داده می‌شود.
          </span>

        </div>

      </template>


      <template #footer>

        <button
            class="close-detail"
            type="button"
            @click="closeDetail"
        >
          بستن
        </button>

        <RouterLink
            class="support-link"
            to="/app/support"
            @click="closeDetail"
        >
          پیگیری از پشتیبانی
        </RouterLink>

      </template>

    </AppModal>

  </div>
</template>


<style scoped>

.transactions-page {
  width: 100%;
  max-width: 86rem;
  margin-inline: auto;
}


.transaction-filters {
  width: 100%;
}

.filters-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-5);
  border-bottom: 1px solid var(--color-border-soft);
}

.filters-title {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: var(--space-3);
}

.filters-title-icon {
  display: grid;
  flex: 0 0 auto;
  width: 2.55rem;
  height: 2.55rem;
  place-items: center;
  border: 1px solid var(--color-border);
  border-radius: .75rem;
  background: var(--color-surface-2);
  color: var(--color-primary);
}

.filters-title > div {
  display: grid;
  min-width: 0;
  gap: .2rem;
}

.filters-title strong {
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  font-weight: 700;
}

.filters-title small {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.transaction-filter-panel {
  display: grid;
  grid-template-columns: minmax(18rem, 1.5fr) repeat(3, minmax(11rem, 1fr));
  align-items: start;
  gap: var(--space-3);
  padding: var(--space-5);
}

.filter-field {
  min-width: 0;
}

.search-field {
  min-width: 0;
}

.mobile-filter-toggle {
  display: none;
  min-height: 2.65rem;
  align-items: center;
  justify-content: center;
  gap: .45rem;
  padding-inline: .8rem;
  border: 1px solid var(--control-border);
  border-radius: var(--radius-md);
  background: var(--color-surface-2);
  color: var(--color-text-secondary);
  font-size: var(--font-size-xs);
  font-weight: 650;
  white-space: nowrap;
  cursor: pointer;
}

.mobile-filter-toggle span {
  padding: .12rem .42rem;
  border-radius: var(--radius-pill);
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-size: .62rem;
}


.date-range-section {
  display: grid;
  grid-template-columns: minmax(15rem, 1.15fr) repeat(3, minmax(11rem, 1fr));
  align-items: start;
  gap: var(--space-3);
  padding: 0 var(--space-5) var(--space-5);
}

.date-range-heading {
  display: flex;
  min-width: 0;
  min-height: var(--control-height);
  align-items: center;
  gap: .7rem;
}

.date-range-icon {
  display: grid;
  flex: 0 0 auto;
  width: 2.4rem;
  height: 2.4rem;
  place-items: center;
  border-radius: .7rem;
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.date-range-heading > div {
  display: grid;
  min-width: 0;
  gap: .18rem;
}

.date-range-heading strong {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.date-range-heading small {
  color: var(--color-text-muted);
  font-size: .7rem;
  line-height: 1.55;
}


.filter-summary {
  display: flex;
  min-height: 3.25rem;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  padding: .6rem var(--space-5);
  border-block: 1px solid var(--color-border-soft);
  background: var(--color-surface-2);
}

.filter-summary-left {
  display: flex;
  min-width: 0;
  align-items: center;
  flex-wrap: wrap;
  gap: .65rem;
}

.result-indicator {
  display: inline-flex;
  align-items: center;
  gap: .35rem;
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.result-indicator strong {
  color: var(--color-text-primary);
  font-weight: 750;
}

.result-indicator svg {
  color: var(--color-primary);
}

.active-filter-indicator {
  display: inline-flex;
  min-height: 1.7rem;
  align-items: center;
  padding-inline: .55rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-pill);
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-size: .68rem;
  font-weight: 650;
}

.reset-filters-button {
  display: inline-flex;
  min-height: 2.2rem;
  align-items: center;
  gap: .42rem;
  padding-inline: .8rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-primary);
  font-size: var(--font-size-xs);
  font-weight: 650;
  white-space: nowrap;
  cursor: pointer;
  transition: background .16s ease,
  border-color .16s ease,
  transform .16s ease;
}

.reset-filters-button:hover {
  background: var(--color-primary-soft);
  border-color: var(--color-primary);
}

.reset-filters-button:active {
  transform: translateY(1px);
}


.transaction-loading {
  display: grid;
  gap: 1px;
  padding: var(--space-3);
}

.transaction-loading-row {
  width: 100%;
}


.transactions-table-wrap {
  width: 100%;
  overflow-x: auto;
}

.transactions-table {
  min-width: 920px;
}

.transactions-table-head,
.transaction-row {
  display: grid;
  grid-template-columns:
    minmax(235px, 1.65fr)
    minmax(130px, .9fr)
    minmax(135px, .95fr)
    minmax(150px, .95fr)
    minmax(125px, .8fr)
    minmax(80px, .5fr);

  align-items: center;
  gap: var(--space-3);
}

.transactions-table-head {
  min-height: 3.4rem;
  padding: 0 var(--space-5);
  border-bottom: 1px solid var(--color-border-soft);
  background: var(--color-surface-2);
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  font-weight: 650;
}

.transaction-row {
  width: 100%;
  min-height: 5.2rem;
  padding: .8rem var(--space-5);
  border: 0;
  border-bottom: 1px solid var(--color-border-soft);
  background: transparent;
  color: var(--color-text-primary);
  text-align: right;
  cursor: pointer;
  transition: background .16s ease,
  box-shadow .16s ease;
}

.transaction-row:hover {
  background: var(--color-surface-2);
}

.transaction-row:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: -2px;
}

.transaction-row:last-child {
  border-bottom: 0;
}


.transaction-primary {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: var(--space-3);
}

.transaction-icon {
  display: grid;
  flex: 0 0 auto;
  width: 2.8rem;
  height: 2.8rem;
  place-items: center;
  border: 1px solid var(--color-border);
  border-radius: .8rem;
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.transaction-main-text {
  display: grid;
  min-width: 0;
  gap: .24rem;
}

.transaction-main-text strong {
  overflow: hidden;
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  font-weight: 700;
  line-height: 1.5;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.transaction-main-text small {
  overflow: hidden;
  color: var(--color-text-muted);
  font-size: .68rem;
  line-height: 1.5;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.transaction-amount-cell,
.transaction-toman-cell,
.transaction-date-cell,
.transaction-status-cell,
.transaction-action-cell {
  min-width: 0;
}

.transaction-amount-cell {
  display: flex;
  min-width: 0;
  align-items: center;
  overflow: hidden;
}

.transaction-toman-cell {
  overflow: hidden;
  color: var(--color-text-secondary);
  font-size: var(--font-size-xs);
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.transaction-date-cell {
  display: grid;
  min-width: 0;
  gap: .18rem;
}

.transaction-date-cell strong {
  color: var(--color-text-secondary);
  font-size: var(--font-size-xs);
  font-weight: 650;
}

.transaction-date-cell small {
  overflow: hidden;
  color: var(--color-text-muted);
  font-size: .66rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.transaction-status-cell {
  display: flex;
  align-items: center;
}

.transaction-action-cell {
  display: flex;
  justify-content: flex-end;
}

.transaction-details-link {
  display: inline-flex;
  align-items: center;
  gap: .15rem;
  color: var(--color-primary);
  font-size: var(--font-size-xs);
  font-weight: 650;
  white-space: nowrap;
}

.muted-value {
  color: var(--color-text-muted);
}


.pagination-wrap {
  display: flex;
  justify-content: center;
  padding: var(--space-4) var(--space-5);
  border-top: 1px solid var(--color-border-soft);
}


.empty-action,
.close-detail,
.support-link {
  display: inline-flex;
  min-height: 2.65rem;
  align-items: center;
  justify-content: center;
  padding-inline: var(--space-4);
  border: 1px solid var(--action-primary);
  border-radius: var(--radius-sm);
  background: var(--action-primary);
  color: var(--on-primary);
  font-weight: 600;
}

.empty-action {
  text-decoration: none;
}


.detail-top {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4);
  border: 1px solid var(--color-border-soft);
  border-radius: var(--radius-lg);
  background: var(--color-surface-2);
}

.detail-icon {
  display: grid;
  width: 3.3rem;
  height: 3.3rem;
  place-items: center;
  border-radius: 1rem;
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.detail-heading {
  display: grid;
  min-width: 0;
  gap: .2rem;
}

.detail-heading > span {
  overflow: hidden;
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.detail-heading :deep(.money-value strong),
.detail-heading :deep(.crypto-value strong) {
  color: var(--color-text-primary);
  font-size: var(--font-size-lg);
  font-weight: 750;
}

.transaction-details {
  display: grid;
  gap: 0;
  margin: var(--space-5) 0;
}

.transaction-details > div {
  display: flex;
  min-width: 0;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  padding: .8rem 0;
  border-bottom: 1px solid var(--color-border-soft);
}

.transaction-details dt {
  flex: 0 0 auto;
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.transaction-details dd {
  display: flex;
  min-width: 0;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: var(--space-2);
  margin: 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-xs);
  line-height: 1.6;
  text-align: end;
}

.transaction-details bdi {
  max-width: min(28rem, 65vw);
  overflow: hidden;
  direction: ltr;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.technical {
  align-items: flex-start !important;
}

.technical dd {
  max-width: 70%;
}

.technical :deep(.copy-button span) {
  display: none;
}

.detail-description,
.network-note {
  display: flex;
  align-items: flex-start;
  gap: var(--space-2);
  padding: var(--space-3);
  border-radius: var(--radius-md);
  font-size: var(--font-size-xs);
  line-height: 1.7;
}

.detail-description {
  margin-bottom: var(--space-3);
  background: var(--color-surface-2);
  color: var(--color-text-secondary);
}

.detail-description svg {
  flex: 0 0 auto;
  color: var(--color-primary);
}

.network-note {
  background: var(--color-info-soft);
  color: var(--color-info);
}

.network-note svg {
  flex: 0 0 auto;
}

.close-detail {
  border-color: var(--color-border);
  background: var(--color-surface-2);
  color: var(--color-text-secondary);
}

.support-link {
  flex: 1;
  text-decoration: none;
}


@media (max-width: 1150px) {

  .transaction-filter-panel {
    grid-template-columns:
      minmax(16rem, 1.35fr)
      repeat(3, minmax(9.5rem, 1fr));
  }

  .date-range-section {
    grid-template-columns:
      minmax(13rem, 1fr)
      repeat(3, minmax(9.5rem, 1fr));
  }

  .transactions-table {
    min-width: 880px;
  }
}


@media (max-width: 950px) {

  .transaction-filter-panel {
    grid-template-columns:
      repeat(2, minmax(0, 1fr));
  }

  .search-field {
    grid-column: 1 / -1;
  }

  .date-range-section {
    grid-template-columns:
      repeat(2, minmax(0, 1fr));
  }

  .date-range-heading {
    grid-column: 1 / -1;
  }

  .date-range-heading {
    min-height: auto;
    padding-top: .2rem;
  }
}


@media (max-width: 767px) {

  .filters-header {
    padding: var(--space-4);
  }

  .filters-title small {
    display: none;
  }

  .mobile-filter-toggle {
    display: inline-flex;
  }

  .transaction-filter-panel {
    display: none;
    grid-template-columns:
      repeat(2, minmax(0, 1fr));
    padding: 0 var(--space-4) var(--space-4);
  }

  .transaction-filter-panel.is-mobile-open {
    display: grid;
  }

  .date-range-section {
    display: none;
    grid-template-columns:
      repeat(2, minmax(0, 1fr));
    padding: 0 var(--space-4) var(--space-4);
  }

  .date-range-section.is-mobile-open {
    display: grid;
  }

  .date-range-heading {
    padding-top: .25rem;
  }

  .filter-summary {
    padding-inline: var(--space-4);
  }

  .transaction-details bdi {
    max-width: 55vw;
  }

  .technical dd {
    width: 100%;
    max-width: 100%;
  }

  .technical {
    flex-direction: column;
    gap: .5rem !important;
  }

  .detail-top {
    grid-template-columns: auto 1fr;
  }

  .detail-top > :deep(.status) {
    grid-column: 2;
    justify-self: start;
  }
}


@media (max-width: 560px) {

  .transaction-filter-panel,
  .date-range-section {
    grid-template-columns:
      minmax(0, 1fr);
  }

  .search-field,
  .date-range-heading {
    grid-column: auto;
  }

  .filter-summary {
    flex-wrap: wrap;
  }

  .reset-filters-button {
    min-height: 2.5rem;
  }

  .filters-title-icon {
    width: 2.35rem;
    height: 2.35rem;
  }

  .transaction-details > div {
    align-items: flex-start;
    flex-direction: column;
    gap: .45rem;
  }

  .transaction-details dd {
    width: 100%;
    justify-content: flex-start;
    text-align: start;
  }

  .transaction-details bdi {
    max-width: 100%;
  }

  .detail-top {
    grid-template-columns: auto 1fr;
  }

  .detail-top > :deep(.status) {
    grid-column: 1 / -1;
    justify-self: start;
  }

  .support-link {
    flex: 1;
  }
}

.filters-header-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex: 0 0 auto;
}

.reset-filters-button {
  display: inline-flex;
  min-height: 2.3rem;
  align-items: center;
  justify-content: center;
  gap: .42rem;
  padding-inline: .8rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface-2);
  color: var(--color-primary);
  font-size: var(--font-size-xs);
  font-weight: 650;
  white-space: nowrap;
  cursor: pointer;
  transition: background .16s ease,
  border-color .16s ease,
  opacity .16s ease;
}

.reset-filters-button:hover:not(:disabled) {
  background: var(--color-primary-soft);
  border-color: var(--color-primary);
}

.reset-filters-button:disabled,
.reset-filters-button.is-disabled {
  opacity: .45;
  cursor: not-allowed;
}

@media (max-width: 767px) {
  .filters-header-actions {
    gap: .4rem;
  }

  .reset-filters-button {
    min-height: 2.55rem;
    padding-inline: .65rem;
  }
}
</style>