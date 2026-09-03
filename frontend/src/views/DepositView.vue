<script setup>
import { ref } from 'vue'
import { ArrowDownLeft, Check, Copy, QrCode, ShieldCheck } from 'lucide-vue-next'
import { useNotificationStore } from '../stores/notification'
import PremiumSelect from '../components/PremiumSelect.vue'

const notification = useNotificationStore()
const currency = ref('USDT')
const network = ref('TRC20')
const address = ref('TQ5H8sA9nQX8D3r7mK9pL4cV2mY6dH9sW')
const status = ref('تأیید شده')
const copied = ref(false)

const assetOptions = [
  { value: 'BTC', name: 'Bitcoin' },
  { value: 'ETH', name: 'Ethereum' },
  { value: 'USDT', name: 'Tether' },
  { value: 'TRX', name: 'Tron' },
]

const recentDeposits = [
  { asset: 'USDT', amount: '۱٬۰۰۰', network: 'TRC20', status: 'تأیید شده', time: 'امروز • ۱۴:۳۲' },
  { asset: 'BTC', amount: '۰.۰۱۲', network: 'Bitcoin', status: 'در انتظار', time: 'دیروز • ۱۰:۴۸' },
  { asset: 'ETH', amount: '۰.۲', network: 'ERC20', status: 'تأیید شده', time: '۱۴۰۳/۰۵/۲۲ • ۱۹:۰۰' },
]

function copyAddress() {
  copied.value = true
  notification.addToast({ title: 'کپی شد', text: 'آدرس واریز کپی شد.', type: 'success' })
  setTimeout(() => {
    copied.value = false
  }, 1400)
}

function statusClass(value) {
  if (value === 'تأیید شده') return 'success'
  if (value === 'در انتظار') return 'warning'
  return 'neutral'
}
</script>

<template>
  <div class="deposit-shell">
    <header class="page-header">
      <div>
        <div class="page-kicker">پلتفرم OTC</div>
        <h1 class="page-title">واریز</h1>
        <p class="page-subtitle">افزایش موجودی دارایی‌های شما</p>
      </div>
      <div class="header-status">
        <ShieldCheck :size="14" />
        وضعیت ایمن
      </div>
    </header>

    <main class="panel deposit-panel">
      <div class="panel-head">
        <div>
          <div class="panel-label">واریز دارایی</div>
          <h2>ثبت واریز</h2>
        </div>
        <span class="inline-pill success">{{ status }}</span>
      </div>

      <div class="field-block">
        <label>انتخاب دارایی</label>
        <div class="asset-grid">
          <button
            v-for="asset in assetOptions"
            :key="asset.value"
            type="button"
            :class="['asset-option', { active: currency === asset.value }]"
            @click="currency = asset.value"
          >
            <span class="asset-icon">{{ asset.value.slice(0, 1) }}</span>
            <span class="asset-copy">
              <strong>{{ asset.value }}</strong>
              <small>{{ asset.name }}</small>
            </span>
          </button>
        </div>
      </div>

      <div class="field-block network-block">
        <label>شبکه</label>
        <div class="network-select-wrap">
          <PremiumSelect v-model="network" :options="[
            { value: 'TRC20', label: 'TRC20' },
            { value: 'ERC20', label: 'ERC20' },
            { value: 'Bitcoin', label: 'Bitcoin' },
            { value: 'Ethereum', label: 'Ethereum' },
          ]" placeholder="انتخاب شبکه" />
        </div>
      </div>

      <div class="workflow-grid">
        <div class="qr-panel">
          <div class="qr-box">
            <QrCode :size="84" />
          </div>
        </div>

        <div class="address-panel">
          <div class="address-head">
            <div>
              <div class="panel-label">آدرس واریز</div>
              <h3>{{ currency }} / {{ network }}</h3>
            </div>
            <span class="network-chip">{{ network }}</span>
          </div>

          <div class="address-box" aria-label="آدرس واریز">
            {{ address }}
          </div>

          <button type="button" class="copy-button" @click="copyAddress">
            <component :is="copied ? Check : Copy" :size="15" />
            <span>{{ copied ? 'کپی شد' : 'کپی آدرس' }}</span>
          </button>
        </div>
      </div>

      <div class="security-warning">
        <div class="warning-head">
          <ShieldCheck :size="15" />
          هشدار امنیتی
        </div>
        <p>
          فقط دارایی موردنظر را از طریق شبکه انتخاب‌شده به این آدرس ارسال کنید.
          شبکه مبدا باید با <strong>{{ network }}</strong> یکسان باشد.
        </p>
      </div>
    </main>

    <section class="panel recent-panel">
      <div class="panel-head compact">
        <div>
          <div class="panel-label">تاریخچه</div>
          <h2>واریزهای اخیر</h2>
        </div>
      </div>

      <div class="recent-list">
        <div v-for="item in recentDeposits" :key="item.asset + item.time" class="recent-item">
          <div class="recent-asset">
            <strong>{{ item.asset }}</strong>
            <small>{{ item.time }}</small>
          </div>
          <div class="recent-amount">
            <strong>{{ item.amount }}</strong>
            <small>{{ item.network }}</small>
          </div>
          <span :class="['status-badge', statusClass(item.status)]">{{ item.status }}</span>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.deposit-shell {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  padding: 4px 4px 0;
}

.page-kicker {
  margin: 0;
  color: #f1d089;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.page-title {
  margin: 10px 0 0;
  font-size: clamp(2rem, 3vw, 2.7rem);
  line-height: 1.15;
  letter-spacing: -0.05em;
  color: var(--text);
}

.page-subtitle {
  margin: 8px 0 0;
  color: var(--text-muted);
  font-size: 0.85rem;
}

.header-status {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 999px;
  border: 1px solid rgba(22, 199, 132, 0.22);
  background: rgba(22, 199, 132, 0.08);
  color: #9ce9c3;
  font-size: 0.74rem;
  font-weight: 700;
}

.panel {
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: 26px;
  box-shadow: var(--shadow-card);
  backdrop-filter: blur(18px);
}

.deposit-panel,
.recent-panel {
  padding: 24px;
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 22px;
}

.panel-label {
  color: #a9b0c3;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.panel-head h2,
.address-head h3 {
  margin: 6px 0 0;
  font-size: clamp(1.45rem, 1.8vw, 1.9rem);
  letter-spacing: -0.04em;
  color: var(--text);
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
  background: rgba(22, 199, 132, 0.08);
  border: 1px solid rgba(22, 199, 132, 0.18);
  color: #8ef1c2;
}

.field-block {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.field-block label {
  color: var(--text-soft);
  font-size: 0.8rem;
  font-weight: 700;
}

.asset-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.asset-option {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 12px 12px;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.02);
  color: var(--text);
  transition: all 0.2s ease;
}

.asset-option:hover {
  border-color: rgba(212, 169, 90, 0.18);
  background: rgba(212, 169, 90, 0.03);
}

.asset-option.active {
  border-color: rgba(212, 169, 90, 0.4);
  background: linear-gradient(180deg, rgba(212, 169, 90, 0.08), rgba(212, 169, 90, 0.02));
  box-shadow: inset 0 0 0 1px rgba(212, 169, 90, 0.18), 0 0 0 3px rgba(212, 169, 90, 0.05);
}

.asset-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 12px;
  background: rgba(212, 169, 90, 0.12);
  border: 1px solid rgba(212, 169, 90, 0.18);
  color: #f3d59c;
  font-size: 0.9rem;
  font-weight: 800;
}

.asset-copy {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 3px;
}

.asset-copy strong {
  font-size: 0.9rem;
  color: var(--text);
}

.asset-copy small {
  color: var(--text-muted);
  font-size: 0.68rem;
}

.network-block {
  margin-top: 22px;
}

.network-select-wrap {
  position: relative;
}

.premium-select {
  width: 100%;
  height: 52px;
  border-radius: 16px;
  padding: 0 18px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: var(--text);
  outline: none;
  appearance: none;
  background-image: linear-gradient(45deg, transparent 50%, rgba(212, 169, 90, 0.8) 50%), linear-gradient(135deg, rgba(212, 169, 90, 0.8) 50%, transparent 50%);
  background-position: calc(100% - 18px) calc(50% - 2px), calc(100% - 13px) calc(50% - 2px);
  background-size: 6px 6px;
  background-repeat: no-repeat;
}

.premium-select:focus {
  border-color: rgba(212, 169, 90, 0.38);
  box-shadow: 0 0 0 3px rgba(212, 169, 90, 0.08);
}

.workflow-grid {
  display: grid;
  grid-template-columns: minmax(200px, 0.78fr) minmax(0, 1.5fr);
  gap: 18px;
  margin-top: 26px;
  align-items: stretch;
}

.qr-panel {
  display: flex;
  min-height: 220px;
}

.qr-box {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 220px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(212, 169, 90, 0.18);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.02);
  color: #f4d89a;
}

.address-panel {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 16px;
  padding: 18px 20px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.address-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.network-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(212, 169, 90, 0.08);
  border: 1px solid rgba(212, 169, 90, 0.18);
  color: #f4d89a;
  font-size: 0.7rem;
  font-weight: 700;
}

.address-box {
  padding: 16px 18px;
  border-radius: 16px;
  background: rgba(7, 12, 20, 0.78);
  border: 1px solid rgba(212, 169, 90, 0.18);
  direction: ltr;
  text-align: left;
  font-family: 'SFMono-Regular', 'Consolas', monospace;
  color: rgba(237, 243, 255, 0.96);
  font-size: 0.86rem;
  line-height: 1.8;
  word-break: break-all;
}

.copy-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: fit-content;
  min-height: 42px;
  padding: 0 14px;
  border-radius: 12px;
  border: 1px solid rgba(212, 169, 90, 0.22);
  background: rgba(212, 169, 90, 0.04);
  color: #f4d89a;
  font-weight: 700;
  transition: all 0.2s ease;
}

.copy-button:hover {
  background: rgba(212, 169, 90, 0.08);
  transform: translateY(-1px);
}

.security-warning {
  margin-top: 22px;
  padding: 18px 18px 16px;
  border-radius: 18px;
  background: rgba(212, 169, 90, 0.05);
  border: 1px solid rgba(212, 169, 90, 0.18);
}

.warning-head {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #f4d89a;
  font-size: 0.78rem;
  font-weight: 700;
  margin-bottom: 8px;
}

.security-warning p {
  margin: 0;
  color: var(--text-soft);
  line-height: 1.9;
  font-size: 0.82rem;
}

.security-warning strong {
  color: #f4d89a;
}

.recent-panel {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.panel-head.compact {
  margin-bottom: 0;
}

.recent-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.recent-item {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(100px, 0.7fr) auto;
  align-items: center;
  gap: 12px;
  padding: 14px 12px;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(255, 255, 255, 0.02);
  transition: background 0.2s ease;
}

.recent-item:hover {
  background: rgba(212, 169, 90, 0.025);
}

.recent-asset,
.recent-amount {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.recent-asset strong,
.recent-amount strong {
  color: var(--text);
  font-size: 0.85rem;
}

.recent-asset small,
.recent-amount small {
  color: var(--text-muted);
  font-size: 0.69rem;
}

.recent-amount {
  align-items: flex-start;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 0.68rem;
  font-weight: 700;
  white-space: nowrap;
}

.status-badge.success {
  background: rgba(22, 199, 132, 0.1);
  border: 1px solid rgba(22, 199, 132, 0.18);
  color: #8ef1c2;
}

.status-badge.warning {
  background: rgba(212, 169, 90, 0.1);
  border: 1px solid rgba(212, 169, 90, 0.2);
  color: #f4d89a;
}

.status-badge.neutral {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: #dfe7ff;
}

@media (max-width: 960px) {
  .asset-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .workflow-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .page-header,
  .panel-head,
  .address-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .deposit-panel,
  .recent-panel {
    padding: 18px 16px;
  }

  .asset-grid {
    grid-template-columns: 1fr;
  }

  .recent-item {
    grid-template-columns: 1fr;
    align-items: flex-start;
  }

  .copy-button {
    width: 100%;
  }
}
</style>
