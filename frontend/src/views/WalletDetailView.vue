<script setup>
import {computed, onMounted, ref} from 'vue'
import {ArrowDownLeft, ArrowRightLeft, ArrowUpRight, ChevronLeft, Search} from 'lucide-vue-next'
import {useWalletStore} from '../stores/wallet'

const walletStore = useWalletStore()
const searchQuery = ref('')

onMounted(() => walletStore.fetchWallets())

const totalBalance = computed(() =>
    walletStore.wallets.reduce((sum, wallet) => sum + Number(wallet.balance || 0), 0),
)

const totalAvailable = computed(() =>
    walletStore.wallets.reduce((sum, wallet) => sum + Number(wallet.available || 0), 0),
)

const totalPending = computed(() =>
    walletStore.wallets.reduce((sum, wallet) => sum + Number(wallet.pending || 0), 0),
)

const assetCount = computed(() => walletStore.wallets.length)

const filteredWallets = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  if (!query) return walletStore.wallets

  return walletStore.wallets.filter((wallet) =>
      [wallet.symbol, wallet.name, wallet.network]
          .filter(Boolean)
          .some((value) => String(value).toLowerCase().includes(query)),
  )
})

const quickActions = [
  {label: 'واریز', icon: ArrowDownLeft, tone: 'primary', to: '/deposit'},
  {label: 'برداشت', icon: ArrowUpRight, tone: 'secondary', to: '/withdraw'},
  {label: 'انتقال', icon: ArrowRightLeft, tone: 'secondary', to: null},
]

const formatAmount = (value) => Number(value || 0).toLocaleString('fa-IR', {
  maximumFractionDigits: 8,
})

const shortAddress = (address) => {
  if (!address) return 'ثبت نشده'
  if (address.length <= 18) return address
  return `${address.slice(0, 8)}...${address.slice(-6)}`
}
</script>

<template>
  <div class="wallet-shell">
    <header class="page-header">
      <div>
        <div class="page-kicker">پلتفرم OTC</div>
        <h1 class="page-title">کیف پول</h1>
        <p class="page-subtitle">مدیریت دارایی‌ها و موجودی کیف پول شما</p>
      </div>
    </header>

    <section class="panel summary-panel">
      <div class="summary-head">
        <div>
          <div class="panel-label">دارایی کل</div>
          <h2>مجموع ارزش دارایی‌ها</h2>
        </div>
        <span class="inline-pill success">+۲.۴۸٪</span>
      </div>

      <div class="portfolio-value">
        {{ Number(totalBalance).toLocaleString('fa-IR') }} تومان
      </div>

      <div class="summary-meta-grid">
        <div class="meta-box">
          <small>موجودی قابل استفاده</small>
          <strong>{{ Number(totalAvailable).toLocaleString('fa-IR') }}</strong>
        </div>
        <div class="meta-box">
          <small>دارایی‌های قفل شده</small>
          <strong>{{ Number(totalPending).toLocaleString('fa-IR') }}</strong>
        </div>
        <div class="meta-box">
          <small>تعداد دارایی‌ها</small>
          <strong>{{ assetCount.toLocaleString('fa-IR') }}</strong>
        </div>
      </div>
    </section>

    <section class="action-panel">
      <div class="action-intro">
        <span class="panel-label">دسترسی سریع</span>
        <strong>مدیریت دارایی</strong>
      </div>

      <div class="action-row">
        <router-link
            v-for="action in quickActions"
            :key="action.label"
            :to="action.to || undefined"
            :class="['quick-action', action.tone, { disabled: !action.to }]"
            :aria-disabled="!action.to"
            @click.prevent="!action.to"
        >
          <component :is="action.icon" :size="17" :stroke-width="1.9"/>
          <span>{{ action.label }}</span>
        </router-link>
      </div>
    </section>

    <section class="panel asset-panel">
      <div class="panel-header">
        <div>
          <div class="panel-label">دارایی‌ها</div>
          <h2>دارایی‌های شما</h2>
        </div>

        <label class="search-box" aria-label="جستجوی دارایی">
          <Search :size="16"/>
          <input v-model="searchQuery" type="search" placeholder="جستجوی دارایی..."/>
        </label>
      </div>

      <div v-if="walletStore.loading" class="asset-list loading-list">
        <div v-for="n in 4" :key="n" class="skeleton-row"/>
      </div>

      <div v-else-if="filteredWallets.length" class="asset-list">
        <router-link
            v-for="wallet in filteredWallets"
            :key="wallet.id"
            :to="`/wallet/${wallet.id}`"
            class="asset-row"
        >
          <div class="asset-identity">
            <span class="coin-badge">{{ wallet.symbol?.slice(0, 1) }}</span>
            <div class="asset-copy">
              <strong>{{ wallet.symbol }}</strong>
              <small>{{ wallet.name }}</small>
            </div>
          </div>

          <div class="asset-network">
            <span v-if="wallet.network" class="chip neutral">{{ wallet.network }}</span>
            <small>موجودی کل</small>
          </div>

          <div class="asset-balance">
            <small>موجودی</small>
            <strong>{{ formatAmount(wallet.balance) }}</strong>
          </div>

          <div class="asset-balance">
            <small>در دسترس</small>
            <strong>{{ formatAmount(wallet.available) }}</strong>
          </div>

          <div class="asset-address" dir="ltr">
            <small>آدرس</small>
            <strong>{{ shortAddress(wallet.address) }}</strong>
          </div>

          <div class="asset-arrow" aria-hidden="true">
            <ChevronLeft :size="17"/>
          </div>
        </router-link>
      </div>

      <div v-else class="empty-state">
        <div class="empty-icon">
          <Search :size="20"/>
        </div>
        <strong>دارایی‌ای پیدا نشد</strong>
        <span>عبارت جستجو را تغییر دهید.</span>
      </div>
    </section>
  </div>
</template>

<style scoped>
.wallet-shell {
  display: flex;
  flex-direction: column;
  gap: 18px;
  min-width: 0;
}

.page-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 18px;
  padding: 2px 2px 0;
}

.page-kicker,
.panel-label {
  color: #f1d089;
  font-size: 0.69rem;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.page-kicker {
  text-transform: uppercase;
}

.page-title {
  margin: 7px 0 0;
  color: var(--text, #fff);
  font-size: clamp(1.9rem, 2.7vw, 2.4rem);
  line-height: 1.15;
  letter-spacing: -0.035em;
}

.page-subtitle {
  margin: 8px 0 0;
  color: #8f9ab0;
  font-size: 0.82rem;
}

.panel {
  background: rgba(12, 18, 30, 0.82);
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 20px;
  box-shadow: 0 24px 50px rgba(2, 6, 23, 0.28);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
}

.summary-panel {
  position: relative;
  overflow: hidden;
  padding: 24px;
}

.summary-panel::before {
  content: '';
  position: absolute;
  inset: auto 15% -55% 10%;
  height: 220px;
  background: radial-gradient(circle, rgba(212, 169, 90, 0.09), transparent 68%);
  pointer-events: none;
}

.summary-head,
.panel-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.summary-head h2,
.panel-header h2 {
  margin: 6px 0 0;
  color: #eef3ff;
  font-size: 1.2rem;
  font-weight: 600;
  letter-spacing: -0.025em;
}

.inline-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 30px;
  padding: 0 11px;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 700;
}

.inline-pill.success {
  color: #8ef1c2;
  background: rgba(22, 199, 132, 0.08);
  border: 1px solid rgba(22, 199, 132, 0.18);
}

.portfolio-value {
  position: relative;
  z-index: 1;
  margin: 22px 0 20px;
  color: #f2f6ff;
  font-size: clamp(2rem, 3.2vw, 3.1rem);
  font-weight: 700;
  line-height: 1.1;
  letter-spacing: -0.05em;
}

.summary-meta-grid {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.meta-box {
  min-width: 0;
  padding: 13px 14px;
  border: 1px solid rgba(255, 255, 255, 0.055);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.018);
}

.meta-box small,
.asset-balance small,
.asset-address small,
.asset-network small {
  display: block;
  color: #7f8ca5;
  font-size: 0.66rem;
}

.meta-box small {
  margin-bottom: 7px;
}

.meta-box strong {
  color: #edf3ff;
  font-size: 0.95rem;
}

.action-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 4px 2px;
}

.action-intro {
  display: flex;
  flex-direction: column;
  gap: 5px;
  flex: 0 0 auto;
}

.action-intro strong {
  color: #eef3ff;
  font-size: 0.95rem;
  font-weight: 600;
}

.action-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.quick-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-width: 108px;
  height: 42px;
  padding: 0 16px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.03);
  color: #dfe7ff;
  font-size: 0.78rem;
  font-weight: 700;
  transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
}

.quick-action:hover:not(.disabled) {
  transform: translateY(-2px);
  border-color: rgba(212, 169, 90, 0.22);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.16);
}

.quick-action.primary {
  background: linear-gradient(135deg, rgba(212, 169, 90, 0.18), rgba(212, 169, 90, 0.08));
  border-color: rgba(212, 169, 90, 0.24);
  color: #f4d89a;
}

.quick-action.disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.asset-panel {
  padding: 22px;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 9px;
  width: min(280px, 100%);
  height: 44px;
  padding: 0 13px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 13px;
  background: rgba(255, 255, 255, 0.028);
  color: #9ca8bd;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
}

.search-box:focus-within {
  border-color: rgba(212, 169, 90, 0.28);
  background: rgba(255, 255, 255, 0.038);
  box-shadow: 0 0 0 3px rgba(212, 169, 90, 0.05);
}

.search-box input {
  width: 100%;
  min-width: 0;
  border: 0;
  outline: 0;
  background: transparent;
  color: #edf3ff;
  font: inherit;
  font-size: 0.78rem;
}

.search-box input::placeholder {
  color: #71809a;
}

.asset-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 18px;
}

.asset-row {
  display: grid;
  grid-template-columns: minmax(180px, 1.35fr) minmax(90px, 0.75fr) minmax(110px, 0.8fr) minmax(110px, 0.8fr) minmax(135px, 0.9fr) 28px;
  align-items: center;
  gap: 14px;
  min-width: 0;
  padding: 13px 12px;
  border: 1px solid transparent;
  border-radius: 15px;
  color: inherit;
  background: rgba(255, 255, 255, 0.012);
  transition: background 0.2s ease, border-color 0.2s ease, transform 0.2s ease;
}

.asset-row:hover {
  transform: translateY(-1px);
  border-color: rgba(212, 169, 90, 0.14);
  background: rgba(212, 169, 90, 0.028);
}

.asset-identity {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.coin-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  flex: 0 0 36px;
  border: 1px solid rgba(212, 169, 90, 0.2);
  border-radius: 11px;
  background: linear-gradient(145deg, rgba(212, 169, 90, 0.13), rgba(255, 255, 255, 0.02));
  color: #f4d89a;
  font-size: 0.86rem;
  font-weight: 800;
}

.asset-copy {
  min-width: 0;
}

.asset-copy strong {
  display: block;
  overflow: hidden;
  color: #eef3ff;
  font-size: 0.92rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.asset-copy small {
  display: block;
  margin-top: 2px;
  overflow: hidden;
  color: #7f8ca5;
  font-size: 0.68rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.asset-network {
  min-width: 0;
}

.asset-network .chip {
  margin-bottom: 4px;
}

.chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  max-width: 100%;
  padding: 5px 9px;
  border-radius: 999px;
  font-size: 0.62rem;
  line-height: 1;
  white-space: nowrap;
}

.chip.neutral {
  color: #b8c2d8;
  border: 1px solid rgba(255, 255, 255, 0.07);
  background: rgba(255, 255, 255, 0.035);
}

.asset-balance,
.asset-address {
  min-width: 0;
}

.asset-balance strong,
.asset-address strong {
  display: block;
  margin-top: 4px;
  overflow: hidden;
  color: #edf3ff;
  font-size: 0.84rem;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.asset-address strong {
  color: #bfc9db;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace;
  font-size: 0.72rem;
}

.asset-arrow {
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  border-radius: 9px;
  color: #6f7c95;
  border: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(255, 255, 255, 0.018);
  transition: all 0.2s ease;
}

.asset-row:hover .asset-arrow {
  color: #f1d089;
  border-color: rgba(212, 169, 90, 0.18);
  background: rgba(212, 169, 90, 0.06);
}

.skeleton-row {
  height: 64px;
  border-radius: 15px;
  background: linear-gradient(90deg, rgba(255, 255, 255, 0.025), rgba(255, 255, 255, 0.055), rgba(255, 255, 255, 0.025));
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite linear;
}

.empty-state {
  display: flex;
  min-height: 180px;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 6px;
  margin-top: 18px;
  border: 1px dashed rgba(255, 255, 255, 0.07);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.012);
}

.empty-state strong {
  color: #e8edf8;
  font-size: 0.9rem;
}

.empty-state span {
  color: #78859c;
  font-size: 0.72rem;
}

.empty-icon {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  margin-bottom: 4px;
  border: 1px solid rgba(212, 169, 90, 0.14);
  border-radius: 12px;
  color: #d4a95a;
  background: rgba(212, 169, 90, 0.05);
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

@media (max-width: 1100px) {
  .asset-row {
    grid-template-columns: minmax(160px, 1.2fr) minmax(80px, 0.7fr) minmax(100px, 0.8fr) minmax(100px, 0.8fr) 28px;
  }

  .asset-address {
    display: none;
  }
}

@media (max-width: 820px) {
  .summary-meta-grid {
    grid-template-columns: 1fr;
  }

  .action-panel {
    align-items: flex-start;
    flex-direction: column;
  }

  .action-row {
    width: 100%;
    justify-content: flex-start;
  }

  .quick-action {
    flex: 1;
  }

  .asset-row {
    grid-template-columns: minmax(150px, 1.1fr) minmax(100px, 0.9fr) minmax(100px, 0.8fr) 28px;
  }

  .asset-network {
    display: none;
  }
}

@media (max-width: 620px) {
  .summary-panel,
  .asset-panel {
    padding: 18px;
  }

  .summary-head,
  .panel-header {
    flex-direction: column;
  }

  .search-box {
    width: 100%;
  }

  .asset-row {
    grid-template-columns: minmax(145px, 1fr) minmax(95px, 0.75fr) 28px;
    gap: 10px;
  }

  .asset-balance:nth-of-type(4) {
    display: none;
  }
}
</style>