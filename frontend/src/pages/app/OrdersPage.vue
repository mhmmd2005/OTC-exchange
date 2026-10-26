<script setup lang="ts">
import {computed, onBeforeUnmount, onMounted, ref, watch} from 'vue'
import type {OrderFilters, OtcOrder} from '@/types'
import {orderService} from '@/services/order.service'
import AppCard from '@/components/ui/AppCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import AppInput from '@/components/ui/AppInput.vue'
import AppPagination from '@/components/ui/AppPagination.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import AppTabs from '@/components/ui/AppTabs.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import OrderList from '@/components/orders/OrderList.vue'
import AppButton from '@/components/ui/AppButton.vue'

const orders = ref<OtcOrder[]>([])
const filter = ref('all')
const search = ref('')
const page = ref(1)
const totalPages = ref(1)

// loading is reserved for the initial page load. Subsequent requests only
// display a loading state over the order list, keeping the rest of the page stable.
const loading = ref(true)
const tableLoading = ref(false)
const hasLoadedOrders = ref(false)
const error = ref('')

let searchTimer: number | undefined
let requestSequence = 0

const activeOnPage = computed(() =>
    orders.value.filter(
        (order) => order.status === 'processing'
    ).length
)

const completedOnPage = computed(() =>
    orders.value.filter((order) => order.status === 'completed').length,
)

const pageVolume = computed(() =>
    orders.value.reduce(
        (total, order) => total + Number(order.finalTomanAmount || 0),
        0,
    ),
)

const buildFilters = (): OrderFilters => {
  const filters: OrderFilters = {
    page: page.value,
    pageSize: 8,
    search: search.value.trim(),
  }

  if (filter.value === 'buy' || filter.value === 'sell') {
    filters.side = filter.value
  } else if (filter.value === 'active') {
    filters.status = 'active'
  } else if (filter.value === 'completed' || filter.value === 'cancelled') {
    filters.status = filter.value
  }

  return filters
}

const load = async (): Promise<void> => {
  const currentRequestId = ++requestSequence
  const isInitialLoad = !hasLoadedOrders.value

  if (isInitialLoad) {
    loading.value = true
  } else {
    tableLoading.value = true
  }

  error.value = ''

  try {
    const result = await orderService.list(buildFilters())

    // Ignore stale responses when the user changes the page, filter, or search.
    if (currentRequestId !== requestSequence) return

    orders.value = result.items
    totalPages.value = Math.max(1, result.totalPages)
    hasLoadedOrders.value = true

    const resolvedPage = Math.max(1, Math.min(result.page, totalPages.value))
    if (page.value !== resolvedPage) {
      page.value = resolvedPage
    }
  } catch (reason) {
    if (currentRequestId === requestSequence) {
      error.value = reason instanceof Error
          ? reason.message
          : 'دریافت سفارش‌ها ممکن نشد.'
    }
  } finally {
    if (currentRequestId === requestSequence) {
      if (isInitialLoad) {
        loading.value = false
      }
      tableLoading.value = false
    }
  }
}

function resetPageAndLoad(): void {
  if (page.value !== 1) {
    page.value = 1
  } else {
    void load()
  }
}

watch(filter, () => {
  // Invalidate an in-flight request before starting the updated query.
  requestSequence += 1
  resetPageAndLoad()
})

watch(page, () => {
  void load()
})

watch(search, () => {
  // Do not render results for a search value that has already changed.
  requestSequence += 1
  window.clearTimeout(searchTimer)
  searchTimer = window.setTimeout(resetPageAndLoad, 350)
})

onMounted(() => {
  void load()
})

onBeforeUnmount(() => {
  requestSequence += 1
  window.clearTimeout(searchTimer)
})
</script>

<template>
  <div class="page orders-page">
    <PageHeader
        title="سفارش‌ها"
        description="همه خرید و فروش‌های مستقیم OTC شما"
    >
      <template #actions>
        <div class="orders-header-actions">
          <AppButton
              variant="secondary"
              size="sm"
              icon="refresh"
              :loading="loading || tableLoading"
              @click="load"
          >
            به‌روزرسانی
          </AppButton>

          <RouterLink
              to="/app/trade"
              class="new-order"
          >
            <AppIcon name="plus" :size="18"/>
            <span>سفارش جدید</span>
          </RouterLink>
        </div>
      </template>
    </PageHeader>

    <section
        v-if="orders.length && hasLoadedOrders"
        class="orders-snapshot"
        aria-label="نمای کلی سفارش‌های این صفحه"
    >
      <article>
        <span class="snapshot-icon">
          <AppIcon name="orders" :size="19"/>
        </span>
        <span>
          <small>سفارش‌های این صفحه</small>
          <strong>{{ orders.length.toLocaleString('fa-IR') }} سفارش</strong>
        </span>
      </article>

      <article>
        <span class="snapshot-icon snapshot-icon--active"><i/></span>
        <span>
          <small>در حال انجام</small>
          <strong>{{ activeOnPage.toLocaleString('fa-IR') }} سفارش</strong>
        </span>
      </article>

      <article>
        <span class="snapshot-icon snapshot-icon--success">
          <AppIcon name="check" :size="18"/>
        </span>
        <span>
          <small>حجم این صفحه</small>
          <strong>{{ pageVolume.toLocaleString('fa-IR') }} تومان</strong>
        </span>
        <em>{{ completedOnPage.toLocaleString('fa-IR') }} تکمیل‌شده</em>
      </article>
    </section>

    <AppCard class="orders-workspace" padding="none">
      <div class="orders-panel-head">
        <div>
          <span><AppIcon name="orders" :size="20"/></span>
          <div>
            <h2>تاریخچه سفارش‌ها</h2>
            <p>جست‌وجو و پیگیری وضعیت خرید و فروش‌های مستقیم</p>
          </div>
        </div>
        <small>
          صفحه {{ page.toLocaleString('fa-IR') }} از {{ totalPages.toLocaleString('fa-IR') }}
        </small>
      </div>

      <div class="orders-toolbar">
        <AppTabs
            v-model="filter"
            :items="[
            {label: 'همه', value: 'all'},
            {label: 'خرید', value: 'buy'},
            {label: 'فروش', value: 'sell'},
            {label: 'در حال انجام', value: 'active'},
            {label: 'تکمیل‌شده', value: 'completed'},
            {label: 'لغوشده', value: 'cancelled'},
          ]"
        />
        <AppInput
            v-model="search"
            icon="search"
            type="search"
            inputmode="search"
            placeholder="جست‌وجوی شماره سفارش…"
        />
      </div>

      <div class="orders-table-region" :aria-busy="tableLoading">
        <div
            v-if="error && orders.length && !loading"
            class="orders-inline-error"
            role="alert"
        >
          <span>{{ error }}</span>
          <button type="button" @click="load">تلاش دوباره</button>
        </div>

        <div class="orders-table-content" :class="{'orders-table-content--refreshing': tableLoading}">
          <div v-if="loading" class="skeleton">
            <AppSkeleton v-for="i in 6" :key="i" height="5rem"/>
          </div>

          <OrderList v-else-if="orders.length" :orders="orders"/>

          <EmptyState
              v-else-if="error"
              icon="warning"
              title="سفارش‌ها دریافت نشد"
              :description="error"
          >
            <button class="empty-action" type="button" @click="load">
              تلاش دوباره
            </button>
          </EmptyState>

          <EmptyState
              v-else
              icon="orders"
              title="هنوز سفارشی با این مشخصات ندارید"
              description="برای شروع، اولین خرید یا فروش مستقیم خود را ثبت کنید."
          >
            <RouterLink class="empty-action" to="/app/trade">اولین خرید</RouterLink>
          </EmptyState>
        </div>

        <div
            v-if="tableLoading"
            class="orders-table-loading"
            role="status"
            aria-live="polite"
        >
          <span class="orders-table-spinner" aria-hidden="true"/>
          <span>در حال به‌روزرسانی سفارش‌ها…</span>
        </div>
      </div>

      <AppPagination v-model="page" :total-pages="totalPages"/>
    </AppCard>
  </div>
</template>

<style scoped>
.orders-page {
  max-width: 84rem;
}

.orders-header-actions {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
}

.new-order,
.empty-action {
  display: inline-flex;
  min-height: 2.65rem;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding-inline: var(--space-4);
  border: 1px solid var(--action-primary);
  border-radius: var(--radius-md);
  background: var(--action-primary);
  color: var(--on-primary);
  font-size: var(--font-size-sm);
  font-weight: 650;
  box-shadow: 0 8px 20px color-mix(in srgb, var(--action-primary) 18%, transparent);
}

.orders-snapshot {
  display: grid;
  grid-template-columns: .75fr .75fr 1.5fr;
  gap: var(--space-3);
  margin-bottom: var(--space-5);
}

.orders-snapshot article {
  display: flex;
  min-width: 0;
  min-height: 4.6rem;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: linear-gradient(
      135deg,
      var(--color-surface-1),
      color-mix(in srgb, var(--color-surface-2) 64%, transparent)
  );
}

.orders-snapshot article > span:nth-child(2) {
  display: grid;
  min-width: 0;
  flex: 1;
}

.orders-snapshot small {
  color: var(--color-text-muted);
  font-size: .68rem;
}

.orders-snapshot strong {
  min-width: 0;
  font-size: var(--font-size-sm);
  font-weight: 650;
  line-height: 1.5;
  overflow-wrap: anywhere;
  white-space: normal;
}

.orders-snapshot em {
  padding: .22rem .55rem;
  border-radius: var(--radius-pill);
  background: var(--color-success-soft);
  color: var(--color-success);
  font-size: .67rem;
  font-style: normal;
  white-space: nowrap;
}

.snapshot-icon {
  display: grid;
  width: 2.55rem;
  height: 2.55rem;
  flex: 0 0 auto;
  border-radius: .8rem;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  place-items: center;
}

.snapshot-icon--active {
  background: var(--color-warning-soft);
}

.snapshot-icon--active i {
  width: .55rem;
  height: .55rem;
  border-radius: 50%;
  background: var(--color-warning);
  box-shadow: 0 0 0 .28rem color-mix(in srgb, var(--color-warning-soft) 82%, transparent);
}

.snapshot-icon--success {
  background: var(--color-success-soft);
  color: var(--color-success);
}

.orders-workspace {
  overflow: hidden;
}

.orders-panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-5) var(--space-5) 0;
}

.orders-panel-head > div {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.orders-panel-head > div > span {
  display: grid;
  width: 2.7rem;
  height: 2.7rem;
  border-radius: .85rem;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  place-items: center;
}

.orders-panel-head h2 {
  margin: 0;
  font-size: var(--font-size-lg);
}

.orders-panel-head p {
  margin: .1rem 0 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.orders-panel-head > small {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.orders-toolbar {
  display: grid;
  grid-template-columns: minmax(32rem, auto) minmax(14rem, 1fr);
  align-items: end;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-5) var(--space-5);
  border-block-end: 1px solid var(--color-border-soft);
}

.orders-table-region {
  position: relative;
  min-width: 0;
}

.orders-table-content {
  min-width: 0;
  transition: opacity 180ms ease;
}

.orders-table-content--refreshing {
  opacity: .42;
  pointer-events: none;
  user-select: none;
}

.orders-table-loading {
  position: absolute;
  inset: 0;
  z-index: 5;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: .65rem;
  min-height: 8rem;
  border-radius: inherit;
  background: color-mix(in srgb, var(--color-surface-1) 68%, transparent);
  color: var(--color-text);
  backdrop-filter: blur(2px);
}

.orders-table-spinner {
  width: 1.15rem;
  height: 1.15rem;
  flex: 0 0 auto;
  border: 2px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: orders-table-spin 700ms linear infinite;
}

.orders-inline-error {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding: .7rem var(--space-5);
  border-block-end: 1px solid var(--color-border-soft);
  background: var(--color-danger-soft);
  color: var(--color-danger);
  font-size: var(--font-size-xs);
}

.orders-inline-error button {
  flex: 0 0 auto;
  padding: .35rem .65rem;
  border: 1px solid currentColor;
  border-radius: var(--radius-md);
  background: transparent;
  color: inherit;
  font: inherit;
  cursor: pointer;
}

.skeleton {
  display: grid;
  gap: 1px;
  padding: var(--space-3);
}

@keyframes orders-table-spin {
  to {
    transform: rotate(360deg);
  }
}

@media (prefers-reduced-motion: reduce) {
  .orders-table-content {
    transition: none;
  }

  .orders-table-spinner {
    animation-duration: 1.5s;
  }
}

@media (max-width: 1050px) {
  .orders-toolbar {
    grid-template-columns: 1fr;
  }

  .orders-toolbar :deep(.tabs) {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    grid-auto-flow: row;
    grid-auto-columns: unset;
    overflow: visible;
  }

  .orders-snapshot {
    grid-template-columns: 1fr 1fr;
  }

  .orders-snapshot article:last-child {
    grid-column: 1 / -1;
  }
}

@media (max-width: 767px) {
  .orders-snapshot {
    grid-template-columns: 1fr 1fr;
    gap: var(--space-2);
    margin-bottom: var(--space-4);
  }

  .orders-snapshot article {
    min-height: 4.1rem;
    padding: var(--space-3);
  }

  .orders-snapshot article:last-child {
    display: none;
  }

  .snapshot-icon {
    width: 2.2rem;
    height: 2.2rem;
  }

  .orders-workspace {
    border-inline: 0;
    border-radius: var(--radius-xl);
    box-shadow: none;
  }

  .orders-panel-head {
    padding: var(--space-4) var(--space-4) 0;
  }

  .orders-panel-head p,
  .orders-panel-head > small {
    display: none;
  }

  .orders-panel-head h2 {
    font-size: var(--font-size-md);
  }

  .orders-toolbar {
    padding: var(--space-3) var(--space-4) var(--space-4);
  }

  .orders-toolbar :deep(.tabs) {
    margin-inline: calc(var(--space-2) * -1);
  }

  .new-order {
    width: 2.7rem;
    overflow: hidden;
    padding: 0;
  }

  .new-order span {
    display: none;
  }
}

@media (max-width: 480px) {
  .orders-toolbar :deep(.tabs) {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    margin-inline: 0;
  }

  .orders-toolbar :deep(.tabs button) {
    padding-inline: var(--space-2);
  }
}
</style>
