<script setup>
import { computed, ref } from 'vue'
import { useOrdersStore } from '../stores/orders'
import { useNotificationStore } from '../stores/notification'
import BaseInput from '../components/BaseInput.vue'
import BaseSelect from '../components/BaseSelect.vue'
import BaseButton from '../components/BaseButton.vue'
import PremiumSelect from '../components/PremiumSelect.vue'

const orderStore = useOrdersStore()
const notification = useNotificationStore()
const mode = ref('buy')
const selectedAsset = ref('USDT')
const amount = ref(2500)
const settlement = ref('wire')
const currentRate = ref(610500)
const quoteExpiry = ref(180)

const estimatedAmount = computed(() => Number(amount.value || 0) * currentRate.value)
const fee = computed(() => estimatedAmount.value * 0.0015)
const finalAmount = computed(() => estimatedAmount.value - fee.value)
const minLimit = computed(() => mode.value === 'buy' ? 1000000 : 500000)
const maxLimit = computed(() => mode.value === 'buy' ? 1500000000 : 1000000000)

const statusOptions = [
  { value: 'waiting', label: 'در انتظار بررسی' },
  { value: 'processing', label: 'در حال پردازش' },
  { value: 'completed', label: 'انجام شد' },
  { value: 'rejected', label: 'رد شد' },
  { value: 'cancelled', label: 'لغو شد' },
]

const marketRows = [
  { ticker: 'BTC', price: '۱٬۲۵۶٬۴۰۰٬۰۰۰', change: '+۱.۸٪', positive: true },
  { ticker: 'ETH', price: '۷۹٬۶۰۰٬۰۰۰', change: '+۲.۴٪', positive: true },
  { ticker: 'USDT', price: '۵۵٬۵۰۰', change: '+۰.۰۷٪', positive: true },
  { ticker: 'TRX', price: '۴٬۶۵۰', change: '-۰.۶٪', positive: false },
]

const liquidityStats = [
  { label: 'نقدینگی', value: '۳.۴ میلیارد' },
  { label: 'حداقل معامله', value: '۲۵۰٬۰۰۰ تومان' },
  { label: 'حداکثر معامله', value: '۲.۵ میلیارد تومان' },
  { label: 'زمان اجرا', value: 'T+1' },
]

const list = [
  { id: 'OTC-24082', type: 'خرید', asset: 'USDT', amount: '۲۵۰۰', status: 'waiting', price: '۶۱٬۰۵۰٬۰۰۰', money: '۱۵۲٬۶۲۵٬۰۰۰' },
  { id: 'OTC-24090', type: 'فروش', asset: 'USDT', amount: '۹۰۰۰', status: 'processing', price: '۶۱٬۰۲۰٬۰۰۰', money: '۵۴۹٬۱۷۸٬۰۰۰' },
  { id: 'OTC-24108', type: 'خرید', asset: 'BTC', amount: '۰.۱۲', status: 'completed', price: '۱٬۲۵۶٬۴۰۰٬۰۰۰', money: '۱۵۰٬۷۶۸٬۰۰۰' },
  { id: 'OTC-24128', type: 'فروش', asset: 'ETH', amount: '۰.۸', status: 'rejected', price: '۷۹٬۶۰۰٬۰۰۰', money: '۶۳٬۶۸۰٬۰۰۰' },
]

async function submitRequest() {
  const payload = {
    mode: mode.value,
    asset: selectedAsset.value,
    amount: Number(amount.value),
    settlement: settlement.value,
    finalAmount: finalAmount.value,
  }
  await orderStore.createOrder(payload)
  notification.addToast({ title: 'درخواست ثبت شد', text: 'درخواست OTC شما با موفقیت ثبت شد و در زمان مناسب بررسی می‌شود.', type: 'success' })
}

const assetOptions = [
  { value: 'USDT', label: 'USDT' },
  { value: 'BTC', label: 'BTC' },
  { value: 'ETH', label: 'ETH' },
  { value: 'SOL', label: 'SOL' },
]
</script>

<template>
  <div class="otc-shell">
    <header class="page-header">
      <div>
        <div class="page-kicker">پلتفرم OTC</div>
        <h1 class="page-title">میز OTC</h1>
      </div>
      <div class="header-status">
        <span class="status-dot" />
        وضعیت میز OTC: فعال
      </div>
    </header>

    <div class="otc-layout">
      <section class="panel otc-panel">
        <div class="panel-header">
          <div>
            <div class="panel-label">معاملات اختصاصی</div>
            <h2>{{ mode === 'buy' ? 'ثبت درخواست خرید' : 'ثبت درخواست فروش' }}</h2>
          </div>
          <div class="countdown-chip">زمان باقیمانده: {{ quoteExpiry }} ثانیه</div>
        </div>

        <div class="mode-switcher">
          <button type="button" :class="['mode-button', { active: mode === 'buy' } ]" @click="mode = 'buy'">خرید</button>
          <button type="button" :class="['mode-button', { active: mode === 'sell' } ]" @click="mode = 'sell'">فروش</button>
        </div>

        <div class="form-grid">
          <BaseSelect label="دارایی" v-model="selectedAsset" :options="assetOptions" />
          <BaseInput label="مقدار" v-model="amount" type="number" placeholder="مثلاً ۲۵۰۰" />
        </div>

        <div class="quote-card">
          <div class="quote-row">
            <span>قیمت پیشنهادی</span>
            <strong>{{ Number(currentRate).toLocaleString('fa-IR') }} تومان</strong>
          </div>
          <div class="quote-row">
            <span>مبلغ تقریبی</span>
            <strong>{{ Number(estimatedAmount).toLocaleString('fa-IR') }} تومان</strong>
          </div>
          <div class="quote-row">
            <span>کارمزد</span>
            <strong>{{ Number(fee).toLocaleString('fa-IR') }} تومان</strong>
          </div>
          <div class="quote-row total-row">
            <span>مبلغ نهایی</span>
            <strong>{{ Number(finalAmount).toLocaleString('fa-IR') }} تومان</strong>
          </div>
          <div class="quote-row muted-row">
            <span>حداقل معامله</span>
            <strong>{{ Number(minLimit).toLocaleString('fa-IR') }}</strong>
          </div>
          <div class="quote-row muted-row">
            <span>حداکثر معامله</span>
            <strong>{{ Number(maxLimit).toLocaleString('fa-IR') }}</strong>
          </div>
        </div>

        <div class="settlement-block">
          <label class="field-label">روش تسویه</label>
          <PremiumSelect v-model="settlement" :options="[
            { value: 'wire', label: 'حواله بانکی' },
            { value: 'cash', label: 'نقدی' },
            { value: 'escrow', label: 'Escrow' },
          ]" placeholder="انتخاب روش تسویه" />
        </div>

        <div class="action-row">
          <button type="button" class="secondary-btn">ذخیره کوئوت</button>
          <BaseButton @click="submitRequest">{{ mode === 'buy' ? 'ثبت درخواست خرید' : 'ثبت درخواست فروش' }}</BaseButton>
        </div>
      </section>

      <aside class="otc-sidebar-col">
        <section class="panel market-panel">
          <div class="panel-header small-header">
            <div>
              <div class="panel-label">خلاصه بازار</div>
              <h3>نرخ لحظه‌ای</h3>
            </div>
            <span class="inline-pill neutral">آخرین وضعیت</span>
          </div>

          <div class="market-price-box">
            <div class="market-headline">
              <span>قیمت فعلی</span>
              <strong>{{ Number(currentRate).toLocaleString('fa-IR') }}</strong>
            </div>
            <div class="market-grid">
              <div>
                <small>تغییر 24h</small>
                <strong class="positive">+۱.۸٪</strong>
              </div>
              <div>
                <small>حجم</small>
                <strong>۱۲.۶ میلیارد</strong>
              </div>
              <div>
                <small>موجودی</small>
                <strong>۸۵۰۰ USDT</strong>
              </div>
              <div>
                <small>تسویه</small>
                <strong>T+1</strong>
              </div>
            </div>
          </div>

          <div class="market-list">
            <div v-for="item in marketRows" :key="item.ticker" class="market-row">
              <div class="coin-meta">
                <span class="coin-badge">{{ item.ticker.slice(0, 1) }}</span>
                <div>
                  <strong>{{ item.ticker }}</strong>
                  <small>{{ item.ticker === 'USDT' ? 'Tether' : item.ticker }}</small>
                </div>
              </div>
              <div class="market-values">
                <strong>{{ item.price }}</strong>
                <span :class="item.positive ? 'positive' : 'negative'">{{ item.change }}</span>
              </div>
            </div>
          </div>
        </section>

        <section class="panel liquidity-panel">
          <div class="panel-header small-header">
            <div>
              <div class="panel-label">نقدینگی</div>
              <h3>دسترس‌پذیری</h3>
            </div>
          </div>

          <div class="liquidity-grid">
            <div v-for="stat in liquidityStats" :key="stat.label" class="liquidity-item">
              <small>{{ stat.label }}</small>
              <strong>{{ stat.value }}</strong>
            </div>
          </div>
        </section>
      </aside>
    </div>

    <section class="panel orders-panel">
      <div class="table-header">
        <div>
          <div class="panel-label">ثبت‌نام‌ها</div>
          <h3>معاملات اخیر OTC</h3>
        </div>
        <span class="inline-pill neutral">۴ درخواست</span>
      </div>

      <div class="table-wrap">
        <table class="premium-table">
          <thead>
            <tr>
              <th>شناسه</th>
              <th>نوع</th>
              <th>دارایی</th>
              <th>مقدار</th>
              <th>قیمت</th>
              <th>مبلغ</th>
              <th>وضعیت</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in list" :key="item.id">
              <td>{{ item.id }}</td>
              <td>{{ item.type }}</td>
              <td>{{ item.asset }}</td>
              <td>{{ item.amount }}</td>
              <td>{{ item.price }}</td>
              <td>{{ item.money }}</td>
              <td>
                <span :class="['status-badge', item.status === 'completed' ? 'success' : item.status === 'processing' ? 'info' : item.status === 'waiting' ? 'warning' : item.status === 'rejected' ? 'danger' : 'neutral']">
                  {{ statusOptions.find(s => s.value === item.status)?.label }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<style scoped>
.otc-shell {
  display: flex;
  flex-direction: column;
  gap: 22px;
  padding-bottom: 18px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 4px 4px 0;
}

.page-kicker {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #f1d089;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  opacity: 0.9;
}

.page-title {
  margin: 8px 0 0;
  font-size: clamp(2rem, 3vw, 2.7rem);
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

.panel {
  background: rgba(12, 18, 30, 0.82);
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 20px;
  box-shadow: 0 24px 50px rgba(2, 6, 23, 0.28);
  backdrop-filter: blur(18px);
}

.otc-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(280px, 0.8fr);
  gap: 20px;
}

.otc-panel,
.market-panel,
.liquidity-panel,
.orders-panel {
  padding: 22px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 20px;
}

.panel-header h2,
.panel-header h3 {
  margin: 4px 0 0;
  font-size: 1.6rem;
  font-weight: 700;
  letter-spacing: -0.03em;
}

.small-header h3 {
  font-size: 1.2rem;
}

.panel-label {
  color: #a9b0c3;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.countdown-chip,
.inline-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  padding: 7px 10px;
  font-size: 0.7rem;
  font-weight: 700;
  line-height: 1;
}

.countdown-chip {
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.03);
  color: #dfe7ff;
}

.inline-pill.neutral {
  border: 1px solid rgba(255,255,255,0.08);
  background: rgba(255,255,255,0.02);
  color: #b9c3d8;
}

.mode-switcher {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  padding: 8px;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 16px;
  margin-bottom: 18px;
}

.mode-button {
  border: 1px solid transparent;
  background: transparent;
  color: #c8d1e2;
  border-radius: 12px;
  min-height: 48px;
  font-weight: 700;
  transition: all 0.2s ease;
}

.mode-button.active {
  background: linear-gradient(135deg, rgba(212,169,90,0.18), rgba(58,111,248,0.1));
  border-color: rgba(212,169,90,0.26);
  color: #f4d89a;
  box-shadow: inset 0 0 0 1px rgba(212,169,90,0.15);
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.quote-card {
  margin-top: 18px;
  padding: 18px 16px;
  border-radius: 18px;
  border: 1px solid rgba(255,255,255,0.06);
  background: rgba(255,255,255,0.015);
  display: grid;
  gap: 10px;
}

.quote-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: #b6c0d5;
  font-size: 0.85rem;
}

.quote-row strong {
  color: #edf3ff;
  font-weight: 700;
}

.total-row {
  padding-top: 12px;
  border-top: 1px solid rgba(255,255,255,0.06);
  color: #f8dca6;
}

.total-row strong {
  color: #f1d089;
}

.muted-row {
  color: #9aa9c4;
}

.settlement-block {
  margin-top: 18px;
}

.field-label {
  display: block;
  margin-bottom: 8px;
  color: #a9b0c3;
  font-size: 0.8rem;
  font-weight: 600;
}

.premium-select {
  width: 100%;
  height: 50px;
  padding: 0 16px;
  border-radius: 14px;
  border: 1px solid rgba(255,255,255,0.08);
  background: rgba(255,255,255,0.03);
  color: #edf3ff;
  outline: none;
}

.premium-select:focus {
  border-color: rgba(212, 169, 90, 0.35);
  box-shadow: 0 0 0 3px rgba(212, 169, 90, 0.08);
}

.action-row {
  margin-top: 18px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
}

.secondary-btn {
  border: 1px solid rgba(212,169,90,0.28);
  background: rgba(212,169,90,0.06);
  color: #f2d79d;
  height: 46px;
  padding: 0 18px;
  border-radius: 12px;
  font-weight: 700;
}

.otc-sidebar-col {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.market-price-box {
  padding: 16px;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 16px;
}

.market-headline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: #a9b0c3;
  margin-bottom: 16px;
}

.market-headline strong {
  color: #f4f7ff;
  font-size: 1.15rem;
}

.market-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.market-grid div {
  padding: 10px 8px 0;
  border-top: 1px solid rgba(255,255,255,0.06);
}

.market-grid small,
.liquidity-item small {
  display: block;
  color: #8894ac;
  font-size: 0.68rem;
  margin-bottom: 6px;
}

.market-grid strong,
.liquidity-item strong {
  color: #edf3ff;
  font-size: 0.9rem;
}

.positive {
  color: #16c784;
}

.negative {
  color: #ea3943;
}

.market-list {
  margin-top: 16px;
  display: grid;
  gap: 12px;
}

.market-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 8px;
  border-radius: 12px;
  background: rgba(255,255,255,0.015);
  border: 1px solid rgba(255,255,255,0.04);
}

.coin-meta {
  display: flex;
  align-items: center;
  gap: 10px;
}

.coin-badge {
  width: 26px;
  height: 26px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: rgba(212,169,90,0.12);
  border: 1px solid rgba(212,169,90,0.22);
  color: #f1d089;
  font-weight: 800;
  font-size: 0.78rem;
}

.coin-meta strong {
  display: block;
  color: #edf3ff;
  font-size: 0.88rem;
}

.coin-meta small {
  display: block;
  color: #8894ac;
  font-size: 0.68rem;
}

.market-values {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.market-values strong {
  color: #edf3ff;
  font-size: 0.8rem;
}

.market-values span {
  font-size: 0.72rem;
  font-weight: 700;
}

.liquidity-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 10px;
}

.liquidity-item {
  padding: 14px 12px;
  border-radius: 14px;
  border: 1px solid rgba(255,255,255,0.06);
  background: rgba(255,255,255,0.02);
}

.table-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.table-header h3 {
  margin: 4px 0 0;
  font-size: 1.3rem;
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
  text-align: right;
  padding: 14px 12px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
  font-size: 0.82rem;
  color: #dfe7ff;
}

.premium-table thead th {
  color: #8d98b1;
  font-size: 0.7rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  font-weight: 700;
}

.premium-table tbody tr {
  transition: background 0.2s ease;
}

.premium-table tbody tr:hover {
  background: rgba(212,169,90,0.04);
}

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

.status-badge.success {
  background: rgba(22, 199, 132, 0.1);
  color: #8ef1c2;
  border: 1px solid rgba(22, 199, 132, 0.18);
}

.status-badge.warning {
  background: rgba(212, 169, 90, 0.1);
  color: #f4d89a;
  border: 1px solid rgba(212, 169, 90, 0.2);
}

.status-badge.info {
  background: rgba(58, 111, 248, 0.08);
  color: #9ec1ff;
  border: 1px solid rgba(58, 111, 248, 0.2);
}

.status-badge.danger {
  background: rgba(234, 57, 67, 0.09);
  color: #ff8d96;
  border: 1px solid rgba(234, 57, 67, 0.18);
}

.status-badge.neutral {
  background: rgba(255,255,255,0.04);
  color: #dbe7ff;
  border: 1px solid rgba(255,255,255,0.08);
}

@media (max-width: 1024px) {
  .otc-layout {
    grid-template-columns: 1fr;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }
}

@media (max-width: 640px) {
  .otc-panel,
  .market-panel,
  .liquidity-panel,
  .orders-panel {
    padding: 16px;
  }

  .form-grid,
  .liquidity-grid,
  .market-grid {
    grid-template-columns: 1fr;
  }

  .action-row {
    flex-direction: column;
    align-items: stretch;
  }

  .secondary-btn,
  .action-row :deep(button) {
    width: 100%;
  }
}
</style>
