<script setup>
import { computed, onMounted, ref } from 'vue'
import { Search } from 'lucide-vue-next'
import { useOrderStore } from '../stores/order'
import EmptyState from '../components/EmptyState.vue'
import Pagination from '../components/Pagination.vue'
import PremiumSelect from '../components/PremiumSelect.vue'

const store = useOrderStore()
const search = ref('')
const activeTab = ref('all')
const statusFilter = ref('all')
const assetFilter = ref('all')

const tabOptions = [
  { value: 'all', label: 'همه' },
  { value: 'واریز', label: 'واریز' },
  { value: 'برداشت', label: 'برداشت' },
  { value: 'انتقال', label: 'انتقال' },
]

onMounted(() => store.fetchTransactions())

const summaryStats = computed(() => {
  const list = store.transactions || []
  return [
    { label: 'کل تراکنش‌ها', value: list.length, tone: 'default' },
    { label: 'واریزها', value: list.filter((item) => item.type === 'واریز').length, tone: 'success' },
    { label: 'برداشت‌ها', value: list.filter((item) => item.type === 'برداشت').length, tone: 'warning' },
    { label: 'انتقال‌ها', value: list.filter((item) => item.type === 'انتقال').length, tone: 'info' },
  ]
})

const filteredTransactions = computed(() => {
  const list = store.transactions || []
  return list.filter((item) => {
    const matchesText = `${item.type} ${item.asset} ${item.id} ${item.status}`.toLowerCase().includes(search.value.trim().toLowerCase())
    const matchesTab = activeTab.value === 'all' || item.type === activeTab.value
    const matchesStatus = statusFilter.value === 'all' || item.status === statusFilter.value
    const matchesAsset = assetFilter.value === 'all' || item.asset === assetFilter.value
    return matchesText && matchesTab && matchesStatus && matchesAsset
  })
})

const uniqueAssets = computed(() => {
  return [...new Set((store.transactions || []).map((item) => item.asset))]
})

function typeClass(type) {
  if (type === 'واریز') return 'deposit'
  if (type === 'برداشت') return 'withdraw'
  if (type === 'انتقال') return 'transfer'
  return 'neutral'
}

function statusClass(status) {
  if (status === 'تأیید شده') return 'success'
  if (status === 'در انتظار' || status === 'در حال بررسی') return 'warning'
  if (status === 'رد شده' || status === 'لغو شده') return 'danger'
  return 'neutral'
}

function amountClass(type) {
  if (type === 'واریز') return 'amount positive'
  if (type === 'برداشت') return 'amount negative'
  return 'amount neutral'
}
</script>

<template>
  <div class="transactions-shell">
    <header class="page-header">
      <div>
        <div class="page-kicker">پلتفرم OTC</div>
        <h1 class="page-title">تراکنش‌ها</h1>
        <p class="page-subtitle">تاریخچه و گردش دارایی‌های حساب شما</p>
      </div>
    </header>

    <div class="summary-grid">
      <div v-for="item in summaryStats" :key="item.label" class="summary-card panel">
        <small>{{ item.label }}</small>
        <strong>{{ item.value }}</strong>
      </div>
    </div>

    <section class="panel transactions-panel">
      <div class="panel-header">
        <div>
          <div class="panel-label">گزارش‌گیری</div>
          <h2>تراکنش‌های اخیر</h2>
        </div>
      </div>

      <div class="tabs-row">
        <button v-for="tab in tabOptions" :key="tab.value" type="button" :class="['tab-button', { active: activeTab === tab.value } ]" @click="activeTab = tab.value">
          {{ tab.label }}
        </button>
      </div>

      <div class="toolbar-row">
        <label class="search-box" aria-label="جستجوی تراکنش">
          <Search :size="16" />
          <input v-model="search" type="text" placeholder="جستجوی تراکنش..." />
        </label>

        <div class="toolbar-actions">
          <PremiumSelect v-model="assetFilter" :options="[{ value: 'all', label: 'همه دارایی‌ها' }, ...uniqueAssets.map((asset) => ({ value: asset, label: asset }))]" placeholder="دارایی" />

          <PremiumSelect v-model="statusFilter" :options="[
            { value: 'all', label: 'همه وضعیت‌ها' },
            { value: 'تأیید شده', label: 'تأیید شده' },
            { value: 'در انتظار', label: 'در انتظار' },
            { value: 'در حال بررسی', label: 'در حال بررسی' },
            { value: 'رد شده', label: 'رد شده' },
            { value: 'لغو شده', label: 'لغو شده' },
          ]" placeholder="وضعیت" />
        </div>
      </div>

      <div v-if="store.loading" class="skeleton-table">
        <div v-for="n in 5" :key="n" class="skeleton-row" />
      </div>

      <div v-else-if="filteredTransactions.length === 0">
        <EmptyState title="تراکنشی وجود ندارد" message="در حال حاضر تراکنشی برای نمایش وجود ندارد." />
      </div>

      <div v-else class="table-wrap">
        <table class="premium-table">
          <thead>
            <tr>
              <th>نوع</th>
              <th>دارایی</th>
              <th>مقدار</th>
              <th>شبکه</th>
              <th>شناسه</th>
              <th>وضعیت</th>
              <th>تاریخ</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="transaction in filteredTransactions" :key="transaction.id">
              <td>
                <span :class="['type-badge', typeClass(transaction.type)]">
                  {{ transaction.type }}
                </span>
              </td>
              <td>
                <div class="asset-cell">
                  <span class="coin-badge">{{ transaction.asset.slice(0, 1) }}</span>
                  <div>
                    <strong>{{ transaction.asset }}</strong>
                    <small>{{ transaction.asset === 'IRT' ? 'تومان' : transaction.asset }}</small>
                  </div>
                </div>
              </td>
              <td>
                <span :class="amountClass(transaction.type)">
                  {{ transaction.type === 'برداشت' ? '-' : '+' }}{{ Number(transaction.amount).toLocaleString('fa-IR') }} {{ transaction.asset }}
                </span>
              </td>
              <td>
                <span class="network-chip">TRC20</span>
              </td>
              <td class="txid-cell">{{ transaction.id }}</td>
              <td>
                <span :class="['status-badge', statusClass(transaction.status)]">{{ transaction.status }}</span>
              </td>
              <td>{{ transaction.date }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="footer-row">
        <span class="meta-text">{{ filteredTransactions.length }} تراکنش نمایش داده می‌شود</span>
        <Pagination :page="1" :total="3" />
      </div>
    </section>
  </div>
</template>

<style scoped>
.transactions-shell {
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

.page-subtitle {
  margin: 8px 0 0;
  color: var(--text-muted);
  font-size: 0.85rem;
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

.panel {
  background: rgba(12, 18, 30, 0.82);
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 20px;
  box-shadow: 0 24px 50px rgba(2, 6, 23, 0.28);
  backdrop-filter: blur(18px);
}

.transactions-panel {
  padding: 22px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 18px;
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

.tabs-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 16px;
}

.tab-button {
  height: 38px;
  padding: 0 14px;
  border-radius: 12px;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.06);
  color: var(--text-soft);
  font-weight: 700;
  transition: all 0.2s ease;
}

.tab-button.active {
  border-color: rgba(212,169,90,0.32);
  background: rgba(212,169,90,0.06);
  color: #f4d89a;
  box-shadow: 0 0 0 2px rgba(212,169,90,0.08);
}

.toolbar-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin: 0 0 18px;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1 1 auto;
  min-height: 46px;
  padding: 0 14px;
  border-radius: 14px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.08);
  color: var(--text-muted);
}

.search-box input {
  width: 100%;
  border: none;
  background: transparent;
  color: var(--text);
  outline: none;
}

.search-box input::placeholder {
  color: var(--text-muted);
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.mini-select {
  min-height: 46px;
  padding: 0 16px;
  border-radius: 14px;
  border: 1px solid rgba(255,255,255,0.08);
  background: rgba(255,255,255,0.03);
  color: var(--text);
  outline: none;
}

.skeleton-table {
  display: grid;
  gap: 10px;
}

.skeleton-row {
  height: 56px;
  border-radius: 12px;
  background: linear-gradient(90deg, rgba(148,163,184,0.06), rgba(255,255,255,0.04), rgba(148,163,184,0.06));
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
  min-width: 860px;
}

.premium-table th,
.premium-table td {
  padding: 16px 12px;
  text-align: right;
  border-bottom: 1px solid rgba(255,255,255,0.05);
  vertical-align: middle;
}

.premium-table th {
  color: #a9b0c3;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.premium-table tbody tr {
  transition: background 0.2s ease;
}

.premium-table tbody tr:hover {
  background: rgba(212,169,90,0.035);
}

.asset-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.coin-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: 10px;
  background: rgba(212,169,90,0.12);
  border: 1px solid rgba(212,169,90,0.18);
  color: #f4d89a;
  font-weight: 800;
  font-size: 0.86rem;
}

.asset-cell strong {
  display: block;
  font-size: 0.86rem;
  color: #edf3ff;
}

.asset-cell small {
  display: block;
  margin-top: 2px;
  color: var(--text-muted);
  font-size: 0.66rem;
}

.type-badge,
.status-badge,
.network-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 0.68rem;
  font-weight: 700;
}

.type-badge.deposit {
  background: rgba(22,199,132,0.10);
  border: 1px solid rgba(22,199,132,0.18);
  color: #8ef1c2;
}

.type-badge.withdraw {
  background: rgba(234,57,67,0.10);
  border: 1px solid rgba(234,57,67,0.18);
  color: #f9b1b7;
}

.type-badge.transfer {
  background: rgba(58,111,248,0.10);
  border: 1px solid rgba(58,111,248,0.18);
  color: #b2d0ff;
}

.type-badge.neutral {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  color: #dfe7ff;
}

.amount {
  font-weight: 700;
  font-size: 0.85rem;
}

.amount.positive {
  color: #8ef1c2;
}

.amount.negative {
  color: #f9b1b7;
}

.amount.neutral {
  color: #dfe7ff;
}

.network-chip {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  color: #dfe7ff;
}

.txid-cell {
  direction: ltr;
  font-family: 'SFMono-Regular', 'Consolas', monospace;
  color: var(--text-soft);
}

.status-badge.success {
  background: rgba(22,199,132,0.10);
  border: 1px solid rgba(22,199,132,0.18);
  color: #8ef1c2;
}

.status-badge.warning {
  background: rgba(212,169,90,0.10);
  border: 1px solid rgba(212,169,90,0.2);
  color: #f4d89a;
}

.status-badge.danger {
  background: rgba(234,57,67,0.10);
  border: 1px solid rgba(234,57,67,0.18);
  color: #f9b1b7;
}

.status-badge.neutral {
  background: rgba(58,111,248,0.10);
  border: 1px solid rgba(58,111,248,0.18);
  color: #b2d0ff;
}

.footer-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 16px;
}

.meta-text {
  color: var(--text-muted);
  font-size: 0.8rem;
}

@media (max-width: 980px) {
  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .toolbar-row {
    flex-direction: column;
    align-items: stretch;
  }

  .toolbar-actions {
    justify-content: space-between;
  }
}

@media (max-width: 640px) {
  .page-header,
  .panel-header,
  .footer-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .summary-grid {
    grid-template-columns: 1fr;
  }

  .transactions-panel {
    padding: 18px 16px;
  }

  .toolbar-actions {
    width: 100%;
    flex-direction: column;
    align-items: stretch;
  }

  .mini-select,
  .search-box {
    width: 100%;
  }
}
</style>
