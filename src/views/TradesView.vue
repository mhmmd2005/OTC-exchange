<script setup>
import { computed, ref } from 'vue'
import { Search } from 'lucide-vue-next'
import PremiumSelect from '../components/PremiumSelect.vue'

const trades = [
  {
    id: 'TRD-10001',
    asset: 'BTC',
    assetName: 'Bitcoin',
    side: 'buy',
    amount: 0.25,
    price: 108500,
    total: 27125000,
    status: 'completed',
    type: 'OTC',
    time: '۱۴۰۳/۰۵/۲۳ • ۱۲:۳۴',
  },
  {
    id: 'TRD-10002',
    asset: 'ETH',
    assetName: 'Ethereum',
    side: 'sell',
    amount: 2,
    price: 4200,
    total: 8400000,
    status: 'completed',
    type: 'Market',
    time: '۱۴۰۳/۰۵/۲۳ • ۱۱:۰۷',
  },
  {
    id: 'TRD-10003',
    asset: 'USDT',
    assetName: 'Tether',
    side: 'buy',
    amount: 20000,
    price: 610500,
    total: 12210000000,
    status: 'pending',
    type: 'OTC',
    time: '۱۴۰۳/۰۵/۲۳ • ۰۹:۲۸',
  },
  {
    id: 'TRD-10004',
    asset: 'SOL',
    assetName: 'Solana',
    side: 'sell',
    amount: 15,
    price: 2980000,
    total: 44700000,
    status: 'cancelled',
    type: 'Limit',
    time: '۱۴۰۳/۰۵/۲۲ • ۲۱:۵۴',
  },
]

const tabOptions = [
  { value: 'all', label: 'همه' },
  { value: 'buy', label: 'خرید' },
  { value: 'sell', label: 'فروش' },
  { value: 'completed', label: 'تکمیل شده' },
  { value: 'pending', label: 'در انتظار' },
]

const search = ref('')
const activeTab = ref('all')
const assetFilter = ref('all')

const filteredTrades = computed(() => {
  return trades.filter((trade) => {
    const query = `${trade.id} ${trade.asset} ${trade.assetName} ${trade.type}`.toLowerCase()
    const matchesQuery = query.includes(search.value.trim().toLowerCase())
    const matchesAsset = assetFilter.value === 'all' || trade.asset === assetFilter.value
    if (!matchesQuery || !matchesAsset) return false

    if (activeTab.value === 'all') return true
    if (activeTab.value === 'buy') return trade.side === 'buy'
    if (activeTab.value === 'sell') return trade.side === 'sell'
    return trade.status === activeTab.value
  })
})

const summary = computed(() => {
  const total = trades.length
  const buy = trades.filter((trade) => trade.side === 'buy').length
  const sell = trades.filter((trade) => trade.side === 'sell').length
  const completed = trades.filter((trade) => trade.status === 'completed').length

  return [
    { label: 'کل معاملات', value: total, tone: 'default' },
    { label: 'خرید', value: buy, tone: 'success' },
    { label: 'فروش', value: sell, tone: 'danger' },
    { label: 'تکمیل شده', value: completed, tone: 'info' },
  ]
})

function sideClass(side) {
  return side === 'buy' ? 'buy' : 'sell'
}

function statusClass(status) {
  if (status === 'completed') return 'success'
  if (status === 'pending') return 'warning'
  if (status === 'cancelled') return 'danger'
  return 'neutral'
}

function statusLabel(status) {
  if (status === 'completed') return 'تکمیل شده'
  if (status === 'pending') return 'در انتظار'
  if (status === 'cancelled') return 'لغو شده'
  return 'پاسخ داده شد'
}
</script>

<template>
  <div class="trades-shell">
    <header class="page-header">
      <div>
        <div class="page-kicker">پلتفرم OTC</div>
        <h1 class="page-title">معاملات</h1>
      </div>
      <div class="header-status">
        <span class="status-dot" />
        بازار فعال
      </div>
    </header>

    <div class="summary-grid">
      <div v-for="item in summary" :key="item.label" class="summary-card panel">
        <small>{{ item.label }}</small>
        <strong>{{ item.value }}</strong>
      </div>
    </div>

    <section class="panel trades-panel">
      <div class="panel-header">
        <div>
          <div class="panel-label">تاریخچه</div>
          <h2>معاملات اخیر</h2>
        </div>
        <div class="panel-actions">
          <button type="button" class="secondary-btn muted">فیلتر</button>
        </div>
      </div>

      <div class="tabs-row">
        <button v-for="tab in tabOptions" :key="tab.value" type="button" :class="['tab-button', { active: activeTab === tab.value }]" @click="activeTab = tab.value">
          {{ tab.label }}
        </button>
      </div>

      <div class="toolbar-row">
        <label class="search-box" aria-label="جستجوی معامله">
          <Search :size="16" />
          <input v-model="search" type="text" placeholder="جستجوی معامله..." />
        </label>

        <div class="toolbar-actions">
          <PremiumSelect v-model="assetFilter" :options="[
            { value: 'all', label: 'همه دارایی‌ها' },
            { value: 'BTC', label: 'BTC' },
            { value: 'ETH', label: 'ETH' },
            { value: 'USDT', label: 'USDT' },
            { value: 'SOL', label: 'SOL' },
          ]" placeholder="همه دارایی‌ها" />
        </div>
      </div>

      <div class="table-wrap">
        <table class="premium-table">
          <thead>
            <tr>
              <th>شناسه معامله</th>
              <th>دارایی</th>
              <th>سمت</th>
              <th>نوع</th>
              <th>مقدار</th>
              <th>قیمت اجرا</th>
              <th>مبلغ</th>
              <th>وضعیت</th>
              <th>زمان</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="trade in filteredTrades" :key="trade.id">
              <td>{{ trade.id }}</td>
              <td>
                <div class="asset-cell">
                  <span class="coin-badge">{{ trade.asset.slice(0, 1) }}</span>
                  <div>
                    <strong>{{ trade.asset }}</strong>
                    <small>{{ trade.assetName }}</small>
                  </div>
                </div>
              </td>
              <td>
                <span :class="['side-badge', sideClass(trade.side)]">{{ trade.side === 'buy' ? 'خرید' : 'فروش' }}</span>
              </td>
              <td>
                <span class="neutral-badge">{{ trade.type }}</span>
              </td>
              <td>{{ Number(trade.amount).toLocaleString('fa-IR') }}</td>
              <td>{{ Number(trade.price).toLocaleString('fa-IR') }}</td>
              <td>{{ Number(trade.total).toLocaleString('fa-IR') }}</td>
              <td>
                <span :class="['status-badge', statusClass(trade.status)]">{{ statusLabel(trade.status) }}</span>
              </td>
              <td>{{ trade.time }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<style scoped>
.trades-shell {
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

.header-status {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 9px 14px;
  border-radius: 999px;
  border: 1px solid rgba(22, 199, 132, 0.24);
  background: rgba(22, 199, 132, 0.08);
  color: #a7f0d0;
  font-size: 0.76rem;
  font-weight: 700;
}

.status-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #16c784;
  box-shadow: 0 0 12px rgba(22, 199, 132, 0.9);
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.summary-card {
  padding: 18px 18px 16px;
  min-height: 108px;
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
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 20px;
  box-shadow: 0 24px 50px rgba(2, 6, 23, 0.28);
  backdrop-filter: blur(18px);
}

.trades-panel {
  padding: 22px;
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

.panel-actions {
  display: flex;
  align-items: center;
}

.secondary-btn {
  height: 42px;
  padding: 0 14px;
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.08);
  background: rgba(255,255,255,0.03);
  color: #dfe7ff;
  font-weight: 700;
}

.secondary-btn.muted {
  border-color: rgba(255,255,255,0.08);
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
  background: transparent;
  border-radius: 10px;
  min-height: 40px;
  padding: 0 14px;
  color: #b7c1d6;
  font-weight: 700;
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
  width: 100%;
  border: 0;
  outline: none;
  background: transparent;
  color: #edf3ff;
  font: inherit;
}

.search-box input::placeholder {
  color: #7f8ca8;
}

.toolbar-actions {
  display: flex;
  align-items: center;
}

.mini-select {
  width: 170px;
  height: 42px;
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.08);
  background: rgba(255,255,255,0.03);
  color: #edf3ff;
  padding: 0 12px;
}

.table-wrap {
  overflow-x: auto;
}

.premium-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 940px;
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

.asset-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.coin-badge {
  width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: rgba(212,169,90,0.12);
  border: 1px solid rgba(212,169,90,0.22);
  color: #f1d089;
  font-size: 0.8rem;
  font-weight: 800;
}

.asset-cell strong {
  display: block;
  color: #edf3ff;
}

.asset-cell small {
  display: block;
  color: #8894ac;
  font-size: 0.68rem;
}

.side-badge,
.status-badge,
.neutral-badge {
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
  background: rgba(22, 199, 132, 0.08);
  color: #8ef1c2;
  border: 1px solid rgba(22, 199, 132, 0.15);
}

.side-badge.sell {
  background: rgba(234, 57, 67, 0.08);
  color: #ff8d96;
  border: 1px solid rgba(234, 57, 67, 0.15);
}

.neutral-badge {
  background: rgba(255,255,255,0.04);
  color: #dfe7ff;
  border: 1px solid rgba(255,255,255,0.08);
}

.status-badge.success {
  background: rgba(22, 199, 132, 0.10);
  color: #8ef1c2;
  border: 1px solid rgba(22, 199, 132, 0.18);
}

.status-badge.warning {
  background: rgba(212, 169, 90, 0.10);
  color: #f4d89a;
  border: 1px solid rgba(212, 169, 90, 0.2);
}

.status-badge.danger {
  background: rgba(234, 57, 67, 0.09);
  color: #ff8d96;
  border: 1px solid rgba(234, 57, 67, 0.18);
}

.status-badge.neutral {
  background: rgba(58, 111, 248, 0.08);
  color: #9ec1ff;
  border: 1px solid rgba(58, 111, 248, 0.2);
}

@media (max-width: 1024px) {
  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .page-header,
  .panel-header,
  .toolbar-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .summary-grid {
    grid-template-columns: 1fr;
  }

  .toolbar-actions,
  .search-box,
  .mini-select {
    width: 100%;
  }
}
</style>
