<script setup>
import { computed, ref } from 'vue'
import { AlertTriangle, ArrowUpRight, ShieldCheck, Wallet } from 'lucide-vue-next'
import PremiumSelect from '../components/PremiumSelect.vue'

const currency = ref('USDT')
const network = ref('TRC20')
const destination = ref('TQ5H8sA9nQX8D3r7mK9pL4cV2mY6dH9sW')
const amount = ref(1200)

const assetOptions = [
  { value: 'BTC', name: 'Bitcoin' },
  { value: 'ETH', name: 'Ethereum' },
  { value: 'USDT', name: 'Tether' },
  { value: 'TRX', name: 'Tron' },
]

const recentWithdrawals = [
  { asset: 'USDT', amount: '۱٬۲۰۰', network: 'TRC20', destination: 'TQ5H8sA...', status: 'موفق', time: 'امروز • ۱۴:۳۲' },
  { asset: 'BTC', amount: '۰.۰۱۲', network: 'Bitcoin', destination: 'bc1q8x...', status: 'در انتظار', time: 'دیروز • ۱۰:۴۸' },
  { asset: 'ETH', amount: '۰.۲', network: 'ERC20', destination: '0xD9E1...', status: 'رد شده', time: '۱۴۰۳/۰۵/۲۲ • ۱۹:۰۰' },
]

const fee = computed(() => Number(amount.value || 0) * 0.0005)
const received = computed(() => Number(amount.value || 0) - fee.value)
const availableBalance = computed(() => {
  const map = { BTC: '1.25 BTC', ETH: '3.80 ETH', USDT: '12,000 USDT', TRX: '18,000 TRX' }
  return map[currency.value] || '0 BTC'
})
const addressValid = computed(() => destination.value.trim().length >= 10)
</script>

<template>
  <div class="withdraw-shell">
    <header class="page-header">
      <div>
        <div class="page-kicker">پلتفرم OTC</div>
        <h1 class="page-title">برداشت</h1>
        <p class="page-subtitle">انتقال دارایی از حساب شما به یک آدرس دیگر</p>
      </div>
      <div class="header-status">
        <ShieldCheck :size="14" />
        حفاظت فعال
      </div>
    </header>

    <main class="panel withdraw-panel">
      <div class="panel-head">
        <div>
          <div class="panel-label">انتقال دارایی</div>
          <h2>ثبت درخواست برداشت</h2>
        </div>
        <div class="header-meta">
          <Wallet :size="14" />
          موجودی قابل استفاده: {{ availableBalance }}
        </div>
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

      <div class="field-block">
        <label>آدرس مقصد</label>
        <input v-model="destination" class="premium-input" :class="{ invalid: !addressValid }" type="text" placeholder="آدرس مقصد را وارد کنید" />
        <div v-if="destination" class="validation-row" :class="addressValid ? 'valid' : 'invalid'">
          {{ addressValid ? '✓ آدرس معتبر است' : 'آدرس واردشده معتبر نیست' }}
        </div>
      </div>

      <div class="amount-row">
        <div class="field-block grow">
          <label>مقدار برداشت</label>
          <div class="amount-input-shell">
            <input v-model.number="amount" type="number" class="premium-input no-pad" min="0" />
            <span class="input-suffix">{{ currency }}</span>
          </div>
        </div>

        <div class="balance-box">
          <small>موجودی قابل استفاده</small>
          <strong>{{ availableBalance }}</strong>
        </div>
      </div>

      <div class="summary-block">
        <div class="summary-row">
          <span>کارمزد شبکه</span>
          <strong>{{ Number(fee).toLocaleString('fa-IR') }} {{ currency }}</strong>
        </div>
        <div class="summary-row highlight">
          <span>مبلغ نهایی دریافتی</span>
          <strong>{{ Number(received).toLocaleString('fa-IR') }} {{ currency }}</strong>
        </div>
      </div>

      <div class="cta-row">
        <button type="button" class="primary-btn">ثبت درخواست برداشت</button>
      </div>

      <div class="security-warning">
        <div class="warning-head">
          <AlertTriangle :size="15" />
          هشدار امنیتی
        </div>
        <p>
          اطمینان حاصل کنید که آدرس مقصد و شبکه انتخاب‌شده صحیح است. تراکنش‌های ثبت‌شده پس از ارسال قابل بازگشت نیستند.
        </p>
      </div>
    </main>

    <section class="panel recent-panel">
      <div class="panel-head compact">
        <div>
          <div class="panel-label">تاریخچه</div>
          <h2>برداشت‌های اخیر</h2>
        </div>
      </div>

      <div class="recent-list">
        <div v-for="item in recentWithdrawals" :key="item.asset + item.time" class="recent-item">
          <div class="recent-asset">
            <strong>{{ item.asset }}</strong>
            <small>{{ item.time }}</small>
          </div>
          <div class="recent-amount">
            <strong>{{ item.amount }}</strong>
            <small>{{ item.network }}</small>
          </div>
          <div class="recent-address">
            <small>{{ item.destination }}</small>
          </div>
          <span :class="['status-badge', item.status === 'موفق' ? 'success' : item.status === 'در انتظار' ? 'warning' : 'neutral']">{{ item.status }}</span>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.withdraw-shell {
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

.withdraw-panel,
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

.panel-head h2 {
  margin: 6px 0 0;
  font-size: clamp(1.45rem, 1.8vw, 1.9rem);
  letter-spacing: -0.04em;
  color: var(--text);
}

.header-meta {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--text-muted);
  font-size: 0.74rem;
  font-weight: 600;
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

.premium-select,
.premium-input {
  width: 100%;
  height: 52px;
  border-radius: 16px;
  padding: 0 18px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: var(--text);
  outline: none;
  transition: all 0.2s ease;
}

.premium-select {
  appearance: none;
  background-image: linear-gradient(45deg, transparent 50%, rgba(212, 169, 90, 0.8) 50%), linear-gradient(135deg, rgba(212, 169, 90, 0.8) 50%, transparent 50%);
  background-position: calc(100% - 18px) calc(50% - 2px), calc(100% - 13px) calc(50% - 2px);
  background-size: 6px 6px;
  background-repeat: no-repeat;
}

.premium-select:focus,
.premium-input:focus {
  border-color: rgba(212, 169, 90, 0.38);
  box-shadow: 0 0 0 3px rgba(212, 169, 90, 0.08);
}

.premium-input {
  color: var(--text);
}

.premium-input.invalid {
  border-color: rgba(234, 57, 67, 0.4);
  box-shadow: 0 0 0 3px rgba(234, 57, 67, 0.05);
}

.validation-row {
  font-size: 0.76rem;
  font-weight: 600;
}

.validation-row.valid {
  color: #8ef1c2;
}

.validation-row.invalid {
  color: #f7a8ad;
}

.amount-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 200px;
  gap: 18px;
  align-items: end;
  margin-top: 22px;
}

.grow {
  flex: 1;
}

.amount-input-shell {
  position: relative;
  display: flex;
  align-items: center;
}

.no-pad {
  padding-left: 72px;
}

.input-suffix {
  position: absolute;
  left: 16px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 46px;
  padding: 0 10px;
  height: 30px;
  border-radius: 10px;
  background: rgba(212, 169, 90, 0.08);
  border: 1px solid rgba(212, 169, 90, 0.18);
  color: #f4d89a;
  font-size: 0.74rem;
  font-weight: 700;
}

.balance-box {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: 52px;
  padding: 10px 14px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.balance-box small {
  color: var(--text-muted);
  font-size: 0.7rem;
}

.balance-box strong {
  margin-top: 6px;
  color: var(--text);
  font-size: 0.88rem;
}

.summary-block {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 22px;
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.summary-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: var(--text-soft);
  font-size: 0.8rem;
}

.summary-row strong {
  color: var(--text);
}

.summary-row.highlight {
  color: #f4d89a;
}

.summary-row.highlight strong {
  color: #f4d89a;
}

.cta-row {
  margin-top: 24px;
}

.primary-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 48px;
  padding: 0 18px;
  border-radius: 14px;
  border: 1px solid rgba(212, 169, 90, 0.22);
  color: #101827;
  background: linear-gradient(135deg, #f2d89d, #d4a95a);
  box-shadow: 0 10px 26px rgba(212, 169, 90, 0.22);
  font-weight: 800;
  transition: all 0.2s ease;
}

.primary-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 16px 30px rgba(212, 169, 90, 0.16);
}

.security-warning {
  margin-top: 18px;
  padding: 16px 18px;
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
  grid-template-columns: minmax(0, 1fr) minmax(100px, 0.6fr) minmax(100px, 0.9fr) auto;
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
.recent-amount,
.recent-address {
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
.recent-amount small,
.recent-address small {
  color: var(--text-muted);
  font-size: 0.69rem;
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

  .amount-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .page-header,
  .panel-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .withdraw-panel,
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
}
</style>
