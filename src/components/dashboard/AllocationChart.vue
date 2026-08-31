<script setup>
const segments = [
  { label: 'USDT', value: 42.1, color: '#d4a95a' },
  { label: 'BTC', value: 28.3, color: '#7eb6ff' },
  { label: 'ETH', value: 17.8, color: '#6ad7c6' },
  { label: 'TRX', value: 7.2, color: '#f3b67d' },
  { label: 'سایر', value: 4.6, color: '#868ca4' },
]

const gradientValue = (() => {
  let current = 0
  return segments
    .map((item) => {
      const start = current
      current += item.value
      return `${item.color} ${start}% ${current}%`
    })
    .join(', ')
})()
</script>

<template>
  <section class="allocation-card panel-surface">
    <div class="panel-header-lite">
      <div>
        <span class="kicker">تخصیص دارایی</span>
        <h3>سهم دارایی‌ها</h3>
      </div>
    </div>

    <div class="allocation-body">
      <div class="donut-wrap">
        <div class="donut-chart" :style="{ background: `conic-gradient(${gradientValue})` }">
          <div class="donut-center">
            <strong>۶۸.۵٪</strong>
            <span>دارایی نقد</span>
          </div>
        </div>
      </div>

      <div class="allocation-list">
        <div v-for="item in segments" :key="item.label" class="alloc-item">
          <span class="swatch" :style="{ background: item.color }" />
          <span class="label">{{ item.label }}</span>
          <strong>{{ item.value }}%</strong>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.allocation-card {
  padding: 18px 16px;
}

.panel-header-lite {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.kicker {
  display: block;
  color: rgba(212,169,90,0.9);
  font-size: 0.62rem;
  font-weight: 700;
  margin-bottom: 6px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.panel-header-lite h3 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 800;
}

.allocation-body {
  display: grid;
  grid-template-columns: 180px 1fr;
  gap: 18px;
  align-items: center;
}

.donut-wrap {
  display: flex;
  justify-content: center;
}

.donut-chart {
  width: 160px;
  height: 160px;
  border-radius: 50%;
  position: relative;
  box-shadow: inset 0 0 18px rgba(255,255,255,0.03);
}

.donut-chart::before {
  content: '';
  position: absolute;
  inset: 18px;
  border-radius: 50%;
  background: rgba(9, 14, 22, 0.93);
  border: 1px solid rgba(255,255,255,0.04);
}

.donut-center {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 1;
}

.donut-center strong {
  color: #fff;
  font-size: 1.4rem;
  font-weight: 800;
}

.donut-center span {
  color: rgba(169,176,195,0.9);
  font-size: 0.62rem;
}

.allocation-list {
  display: grid;
  gap: 10px;
}

.alloc-item {
  display: grid;
  grid-template-columns: 12px 1fr auto;
  align-items: center;
  gap: 10px;
  color: rgba(169,176,195,0.9);
  font-size: 0.76rem;
}

.swatch {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}

.label {
  color: rgba(169,176,195,0.9);
}

.alloc-item strong {
  color: #fff;
  font-size: 0.76rem;
  font-weight: 800;
}
</style>
