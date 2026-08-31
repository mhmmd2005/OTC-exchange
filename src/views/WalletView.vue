<script setup>
import { computed, onMounted } from 'vue'
import { ArrowDownLeft, ArrowUpRight, ArrowRightLeft, Plus } from 'lucide-vue-next'
import { useWalletStore } from '../stores/wallet'
import LoadingSkeleton from '../components/LoadingSkeleton.vue'

const walletStore = useWalletStore()
onMounted(() => walletStore.fetchWallets())

const totalBalance = computed(() => walletStore.wallets.reduce((sum, wallet) => sum + Number(wallet.balance || 0), 0))
const totalAvailable = computed(() => walletStore.wallets.reduce((sum, wallet) => sum + Number(wallet.available || 0), 0))
const totalPending = computed(() => walletStore.wallets.reduce((sum, wallet) => sum + Number(wallet.pending || 0), 0))
const assetCount = computed(() => walletStore.wallets.length)

const quickActions = [
  { label: 'واریز', icon: ArrowDownLeft, tone: 'primary' },
  { label: 'برداشت', icon: ArrowUpRight, tone: 'secondary' },
  { label: 'انتقال', icon: ArrowRightLeft, tone: 'secondary' },
]
</script>

<template>
  <div class="wallet-shell">
    <header class="page-header">
      <div>
        <div class="page-kicker">پلتفرم OTC</div>
        <h1 class="page-title">کیف پول</h1>
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

      <div class="portfolio-value">{{ Number(totalBalance).toLocaleString('fa-IR') }} تومان</div>

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
          <strong>{{ assetCount }}</strong>
        </div>
      </div>
    </section>

    <div class="action-row">
      <button v-for="action in quickActions" :key="action.label" type="button" :class="['quick-action', action.tone]">
        <component :is="action.icon" :size="16" />
        <span>{{ action.label }}</span>
      </button>
    </div>

    <section class="panel asset-panel">
      <div class="panel-header">
        <div>
          <div class="panel-label">دارایی‌ها</div>
          <h2>دارایی‌های شما</h2>
        </div>
        <label class="search-box" aria-label="جستجوی دارایی">
          <Plus :size="14" />
          <input type="text" placeholder="جستجوی دارایی..." />
        </label>
      </div>

      <div v-if="walletStore.loading" class="wallet-grid loading-grid">
        <div v-for="n in 4" :key="n" class="skeleton-card" />
      </div>

      <div v-else class="wallet-grid">
        <router-link
          v-for="wallet in walletStore.wallets"
          :key="wallet.id"
          :to="`/wallet/${wallet.id}`"
          class="asset-card"
        >
          <div class="asset-top">
            <div class="asset-identity">
              <span class="coin-badge">{{ wallet.symbol.slice(0, 1) }}</span>
              <div>
                <strong>{{ wallet.symbol }}</strong>
                <small>{{ wallet.name }}</small>
              </div>
            </div>
            <span class="chip neutral">{{ wallet.network }}</span>
          </div>

          <div class="asset-body">
            <div>
              <small>موجودی</small>
              <strong>{{ Number(wallet.balance).toLocaleString('fa-IR') }}</strong>
            </div>
            <div>
              <small>در دسترس</small>
              <strong>{{ Number(wallet.available).toLocaleString('fa-IR') }}</strong>
            </div>
          </div>

          <div class="asset-foot">
            <span>آدرس: {{ wallet.address }}</span>
          </div>
        </router-link>
      </div>
    </section>
  </div>
</template>

<style scoped>
.wallet-shell {
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

.wallet-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.primary-btn,
.secondary-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 42px;
  padding: 0 16px;
  border-radius: 12px;
  font-weight: 700;
  transition: all 0.2s ease;
}

.primary-btn {
  background: linear-gradient(135deg, rgba(212,169,90,0.18), rgba(212,169,90,0.08));
  border: 1px solid rgba(212,169,90,0.24);
  color: #f4d89a;
}

.secondary-btn {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.08);
  color: #dfe7ff;
}

.panel {
  background: rgba(12, 18, 30, 0.82);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 20px;
  box-shadow: 0 24px 50px rgba(2, 6, 23, 0.28);
  backdrop-filter: blur(18px);
}

.summary-panel,
.asset-panel {
  padding: 22px;
}

.summary-head,
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

.summary-head h2,
.panel-header h2 {
  margin: 6px 0 0;
  font-size: 1.55rem;
  letter-spacing: -0.03em;
}

.inline-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 30px;
  padding: 0 12px;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 700;
}

.inline-pill.success {
  background: rgba(22,199,132,0.08);
  color: #8ef1c2;
  border: 1px solid rgba(22,199,132,0.18);
}

.portfolio-value {
  font-size: clamp(2rem, 2.6vw, 3rem);
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: -0.05em;
  color: #edf3ff;
  margin-bottom: 18px;
}

.summary-meta-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.meta-box {
  padding: 14px 14px 12px;
  border-radius: 14px;
  border: 1px solid rgba(255,255,255,0.06);
  background: rgba(255,255,255,0.02);
}

.meta-box small {
  display: block;
  color: #8894ac;
  font-size: 0.68rem;
  margin-bottom: 8px;
}

.meta-box strong {
  color: #edf3ff;
  font-size: 1rem;
}

.action-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.quick-action {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 42px;
  padding: 0 16px;
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.08);
  background: rgba(255,255,255,0.03);
  color: #dfe7ff;
  font-weight: 700;
}

.quick-action.primary {
  background: linear-gradient(135deg, rgba(212,169,90,0.18), rgba(212,169,90,0.08));
  border-color: rgba(212,169,90,0.24);
  color: #f4d89a;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  width: min(260px, 100%);
  height: 42px;
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.08);
  background: rgba(255,255,255,0.03);
  padding: 0 12px;
  color: #a9b0c3;
}

.search-box input {
  width: 100%;
  background: transparent;
  border: 0;
  color: #edf3ff;
  font: inherit;
  outline: none;
}

.search-box input::placeholder {
  color: #7f8ca8;
}

.wallet-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 16px;
}

.asset-card {
  display: block;
  padding: 18px;
  border-radius: 18px;
  border: 1px solid rgba(255,255,255,0.06);
  background: rgba(255,255,255,0.015);
  transition: all 0.2s ease;
}

.asset-card:hover {
  transform: translateY(-2px);
  border-color: rgba(212,169,90,0.2);
  box-shadow: 0 18px 30px rgba(0,0,0,0.18);
}

.asset-top,
.asset-body,
.asset-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.asset-top {
  margin-bottom: 16px;
}

.asset-identity {
  display: flex;
  align-items: center;
  gap: 12px;
}

.coin-badge {
  width: 32px;
  height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: rgba(212,169,90,0.12);
  border: 1px solid rgba(212,169,90,0.22);
  color: #f4d89a;
  font-weight: 800;
}

.asset-identity strong {
  color: #edf3ff;
  display: block;
  font-size: 0.95rem;
}

.asset-identity small,
.asset-foot,
.asset-body small {
  color: #8d98b1;
  font-size: 0.68rem;
}

.chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  padding: 6px 10px;
  font-size: 0.65rem;
  line-height: 1;
  color: #dfe7ff;
}

.chip.neutral {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
}

.asset-body {
  margin-bottom: 14px;
}

.asset-body small {
  display: block;
  margin-bottom: 6px;
}

.asset-body strong {
  color: #edf3ff;
  font-size: 1rem;
}

.asset-foot {
  justify-content: flex-start;
  color: #9aa9c4;
  font-size: 0.7rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.skeleton-card {
  height: 190px;
  border-radius: 18px;
  background: linear-gradient(90deg, rgba(255,255,255,0.03), rgba(255,255,255,0.06), rgba(255,255,255,0.03));
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite linear;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

@media (max-width: 1024px) {
  .summary-meta-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .page-header,
  .summary-head,
  .panel-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .summary-meta-grid,
  .wallet-grid {
    grid-template-columns: 1fr;
  }

  .action-row,
  .wallet-actions {
    width: 100%;
  }

  .quick-action,
  .primary-btn,
  .secondary-btn {
    flex: 1;
  }
}
</style>
