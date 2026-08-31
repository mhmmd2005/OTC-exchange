<script setup>
import { computed, onMounted, ref } from 'vue'
import { Search } from 'lucide-vue-next'
import { useOrderStore } from '../stores/order'
import EmptyState from '../components/EmptyState.vue'
import Pagination from '../components/Pagination.vue'
import PremiumSelect from '../components/PremiumSelect.vue'

const store = useOrderStore()
const filters = ref('all')
const search = ref('')

const tabOptions = [
  { value: 'all', label: 'همه' },
  { value: 'buy', label: 'خرید' },
  { value: 'sell', label: 'فروش' },
  { value: 'completed', label: 'تکمیل شده' },
  { value: 'waiting', label: 'در انتظار' },
  { value: 'cancelled', label: 'لغو شده' },
]

onMounted(() => store.fetchOrders())

const filteredOrders = computed(() => {
  const list = store.orders.filter((item) => {
    const matchesSearch = `${item.id} ${item.type} ${item.asset}`.toLowerCase().includes(search.value.toLowerCase())
    if (!matchesSearch) return false
    if (filters.value === 'all') return true
    if (filters.value === 'buy') return item.type === 'خرید'
    if (filters.value === 'sell') return item.type === 'فروش'
    if (filters.value === 'completed') return item.status === 'انجام شد'
    if (filters.value === 'waiting') return item.status === 'در انتظار بررسی'
    if (filters.value === 'cancelled') return item.status === 'لغو شد'
    return true
  })
  return list
})

const summaryStats = computed(() => {
  const all = store.orders.length
  const active = store.orders.filter((item) => ['در انتظار بررسی', 'در حال پردازش'].includes(item.status)).length
  const completed = store.orders.filter((item) => item.status === 'انجام شد').length
  const cancelled = store.orders.filter((item) => item.status === 'لغو شد').length

  return [
    { label: 'کل سفارش‌ها', value: all, tone: 'default' },
    { label: 'فعال', value: active, tone: 'info' },
    { label: 'تکمیل شده', value: completed, tone: 'success' },
    { label: 'لغو شده', value: cancelled, tone: 'danger' },
  ]
})

function statusClass(status) {
  if (status === 'انجام شد') return 'success'
  if (status === 'در انتظار بررسی') return 'warning'
  if (status === 'در حال پردازش') return 'info'
  if (status === 'لغو شد' || status === 'رد شد') return 'danger'
  return 'neutral'
}

function sideClass(type) {
  return type === 'خرید' ? 'buy' : 'sell'
}
</script>

<template>
  <div class="orders-shell">
    <header class="page-header">
      <div>
        <div class="page-kicker">پلتفرم OTC</div>
        <h1 class="page-title">سفارش‌ها</h1>
      </div>
      <button type="button" class="ghost-btn">گزارش سفارش‌ها</button>
    </header>

    <div class="summary-grid">
      <div v-for="item in summaryStats" :key="item.label" class="summary-card panel">
        <small>{{ item.label }}</small>
        <strong>{{ item.value }}</strong>
      </div>
    </div>

    <section class="panel orders-panel">
      <div class="panel-header">
        <div>
          <div class="panel-label">مدیریت سفارش</div>
          <h2>لیست سفارش‌ها</h2>
        </div>
        <div class="toolbar-small">
          <PremiumSelect v-model="filters" :options="[
            { value: 'all', label: 'همه' },
            { value: 'buy', label: 'خرید' },
            { value: 'sell', label: 'فروش' },
            { value: 'completed', label: 'تکمیل شده' },
            { value: 'waiting', label: 'در انتظار' },
            { value: 'cancelled', label: 'لغو شده' },
          ]" placeholder="فیلتر سفارش‌ها" />
        </div>
      </div>

      <div class="tabs-row">
        <button v-for="tab in tabOptions" :key="tab.value" type="button" :class="['tab-button', { active: filters === tab.value } ]" @click="filters = tab.value">
          {{ tab.label }}
        </button>
      </div>

      <div class="toolbar-row">
        <label class="search-box" aria-label="جستجوی سفارش">
          <Search :size="16" />
          <input v-model="search" type="text" placeholder="جستجوی سفارش..." />
        </label>

        <div class="toolbar-actions">
          <button type="button" class="secondary-btn">فیلتر</button>
          <button type="button" class="secondary-btn muted">بازنشانی</button>
        </div>
      </div>

      <div v-if="store.loading" class="skeleton-table">
        <div class="skeleton-row" v-for="n in 5" :key="n" />
      </div>

      <div v-else-if="filteredOrders.length === 0">
        <EmptyState title="سفارشی پیدا نشد" message="داده‌ای مطابق با فیلتر انتخابی وجود ندارد." />
      </div>

      <div v-else class="table-wrap">
        <table class="premium-table">
          <thead>
            <tr>
              <th>شماره سفارش</th>
              <th>نوع معامله</th>
              <th>ارز</th>
              <th>مقدار</th>
              <th>قیمت</th>
              <th>مبلغ</th>
              <th>وضعیت</th>
              <th>زمان</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="order in filteredOrders" :key="order.id">
              <td>{{ order.id }}</td>
              <td>
                <span :class="['side-badge', sideClass(order.type)]">{{ order.type }}</span>
              </td>
              <td>{{ order.asset }}</td>
              <td>{{ Number(order.amount).toLocaleString('fa-IR') }}</td>
              <td>{{ Number(order.price).toLocaleString('fa-IR') }}</td>
              <td>{{ Number(order.total).toLocaleString('fa-IR') }}</td>
              <td>
                <span :class="['status-badge', statusClass(order.status)]">{{ order.status }}</span>
              </td>
              <td>{{ order.time }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="footer-row">
        <span class="meta-text">{{ filteredOrders.length }} سفارش نمایش داده می‌شود</span>
        <Pagination :page="1" :total="3" />
      </div>
    </section>
  </div>
</template>

<style scoped>
.orders-shell {
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 4px 4px 0;
}

.page-kicker {
  color: #f1d089;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.page-title {
  margin: 8px 0 0;
  font-size: clamp(2rem, 3vw, 2.75rem);
  line-height: 1.15;
  letter-spacing: -0.04em;
  color: var(--text);
}

.ghost-btn,
.secondary-btn {
  height: 44px;
  padding: 0 18px;
  border-radius: 12px;
  border: 1px solid rgba(212,169,90,0.24);
  background: rgba(212,169,90,0.06);
  color: #f3d99f;
  font-weight: 700;
}

.secondary-btn.muted {
  border-color: rgba(255,255,255,0.08);
  background: rgba(255,255,255,0.03);
  color: #dfe7ff;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.summary-card {
  padding: 18px 18px 16px;
  min-height: 110px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.summary-card small {
  color: #8d98b1;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.summary-card strong {
  margin-top: 8px;
  font-size: clamp(1.5rem, 2vw, 2.1rem);
  color: #edf3ff;
  letter-spacing: -0.04em;
}

.orders-panel {
  padding: 22px;
}

.panel {
  background: rgba(12, 18, 30, 0.82);
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 20px;
  box-shadow: 0 24px 50px rgba(2, 6, 23, 0.28);
  backdrop-filter: blur(18px);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 20px;
}

.panel-label {
  color: #a9b0c3;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.panel-header h2 {
  margin: 6px 0 0;
  font-size: 1.55rem;
  letter-spacing: -0.03em;
}

.toolbar-small {
  display: flex;
  justify-content: flex-end;
}

.mini-select {
  width: 160px;
  height: 42px;
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.08);
  background: rgba(255,255,255,0.03);
  color: #edf3ff;
  padding: 0 12px;
}

.tabs-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 8px;
  border-radius: 16px;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.06);
  margin-bottom: 16px;
}

.tab-button {
  border: 1px solid transparent;
  border-radius: 10px;
  background: transparent;
  min-height: 40px;
  padding: 0 14px;
  color: #b7c1d6;
  font-weight: 700;
  transition: all 0.2s ease;
}

.tab-button.active {
  background: linear-gradient(135deg, rgba(212,169,90,0.12), rgba(58,111,248,0.08));
  border-color: rgba(212,169,90,0.2);
  color: #f4d89a;
}

.toolbar-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 18px;
}

.search-box {
  flex: 1 1 auto;
  display: flex;
  align-items: center;
  gap: 10px;
  height: 48px;
  padding: 0 14px;
  border-radius: 14px;
  border: 1px solid rgba(255,255,255,0.08);
  background: rgba(255,255,255,0.03);
  color: #a9b0c3;
}

.search-box input {
  background: transparent;
  border: 0;
  outline: none;
  width: 100%;
  color: #edf3ff;
  font: inherit;
}

.search-box input::placeholder {
  color: #7f8ca8;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.skeleton-table {
  display: grid;
  gap: 12px;
  padding-top: 8px;
}

.skeleton-row {
  height: 54px;
  border-radius: 12px;
  background: linear-gradient(90deg, rgba(255,255,255,0.03), rgba(255,255,255,0.06), rgba(255,255,255,0.03));
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite linear;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.table-wrap {
  overflow-x: auto;
}

.premium-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 760px;
}

.premium-table th,
.premium-table td {
  padding: 14px 12px;
  text-align: right;
  border-bottom: 1px solid rgba(255,255,255,0.06);
  color: #dfe7ff;
  font-size: 0.82rem;
}

.premium-table thead th {
  color: #8d98b1;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.premium-table tbody tr {
  transition: background 0.2s ease;
}

.premium-table tbody tr:hover {
  background: rgba(212,169,90,0.04);
}

.side-badge,
.status-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 7px 10px;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 700;
  white-space: nowrap;
}

.side-badge.buy {
  background: rgba(22,199,132,0.08);
  color: #8ef1c2;
  border: 1px solid rgba(22,199,132,0.15);
}

.side-badge.sell {
  background: rgba(234,57,67,0.08);
  color: #ff8d96;
  border: 1px solid rgba(234,57,67,0.15);
}

.status-badge.success {
  background: rgba(22,199,132,0.10);
  color: #8ef1c2;
  border: 1px solid rgba(22,199,132,0.18);
}

.status-badge.warning {
  background: rgba(212,169,90,0.10);
  color: #f4d89a;
  border: 1px solid rgba(212,169,90,0.2);
}

.status-badge.info {
  background: rgba(58,111,248,0.08);
  color: #a9c7ff;
  border: 1px solid rgba(58,111,248,0.2);
}

.status-badge.danger {
  background: rgba(234,57,67,0.09);
  color: #ff8d96;
  border: 1px solid rgba(234,57,67,0.18);
}

.status-badge.neutral {
  background: rgba(255,255,255,0.04);
  color: #dfe7ff;
  border: 1px solid rgba(255,255,255,0.08);
}

.footer-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 16px;
}

.meta-text {
  color: #8d98b1;
  font-size: 0.74rem;
}

@media (max-width: 1024px) {
  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .page-header,
  .panel-header,
  .toolbar-row,
  .footer-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .summary-grid {
    grid-template-columns: 1fr;
  }

  .toolbar-actions,
  .toolbar-small {
    width: 100%;
  }

  .toolbar-actions {
    justify-content: stretch;
  }

  .toolbar-actions .secondary-btn {
    flex: 1;
  }

  .search-box {
    width: 100%;
  }
}
</style>
