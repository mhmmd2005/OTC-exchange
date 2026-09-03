<script setup>
const markets = [
  { symbol: 'BTC', name: 'Bitcoin', price: '$43,812.00', change: '+1.24%', up: true, points: '10,18,14,20,17,19,22,21,25,26' },
  { symbol: 'ETH', name: 'Ethereum', price: '$2,361.50', change: '+0.86%', up: true, points: '8,12,11,14,13,18,20,18,22,26' },
  { symbol: 'USDT', name: 'Tether', price: '$1.00', change: '+0.01%', up: true, points: '12,12,12,13,12,13,12,13,12,13' },
  { symbol: 'TRX', name: 'Tron', price: '$0.1012', change: '-0.45%', up: false, points: '22,21,18,19,17,15,16,14,13,12' },
]

function sparkline(points) {
  const arr = points.split(',').map(Number)
  const max = Math.max(...arr)
  const min = Math.min(...arr)
  const range = max - min || 1
  return arr
    .map((n, i) => {
      const x = (i / (arr.length - 1)) * 100
      const y = 100 - ((n - min) / range) * 80 - 10
      return `${x},${y}`
    })
    .join(' ')
}
</script>

<template>
  <aside class="market-widget panel-surface">
    <div class="panel-header-lite">
      <div>
        <span class="kicker">نبض بازار</span>
        <h3>قیمت‌های لحظه‌ای</h3>
      </div>
      <button type="button" class="ghost-link">نمایش همه</button>
    </div>

    <div class="market-list">
      <div v-for="item in markets" :key="item.symbol" class="market-row">
        <div class="coin-wrap">
          <div class="coin-badge" :class="item.up ? 'up' : 'down'">{{ item.symbol.slice(0, 1) }}</div>
          <div class="coin-copy">
            <strong>{{ item.symbol }}</strong>
            <small>{{ item.name }}</small>
          </div>
        </div>

        <div class="sparkline-wrap">
          <svg viewBox="0 0 100 30" preserveAspectRatio="none" aria-hidden="true">
            <polyline :points="sparkline(item.points)" :class="item.up ? 'line-up' : 'line-down'" />
          </svg>
        </div>

        <div class="market-side">
          <strong>{{ item.price }}</strong>
          <span :class="item.up ? 'positive' : 'negative'">{{ item.change }}</span>
        </div>
      </div>
    </div>
  </aside>
</template>

<style scoped>
.market-widget {
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

.ghost-link {
  border: 1px solid rgba(255,255,255,0.06);
  background: transparent;
  color: rgba(169,176,195,0.8);
  border-radius: 10px;
  padding: 7px 10px;
  font-size: 0.7rem;
  font-weight: 700;
}

.market-list {
  display: grid;
  gap: 10px;
}

.market-row {
  display: grid;
  grid-template-columns: 1.4fr 1fr 0.9fr;
  align-items: center;
  gap: 8px;
  padding: 10px 8px;
  border-radius: 12px;
  background: rgba(255,255,255,0.01);
  border: 1px solid rgba(255,255,255,0.04);
}

.coin-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.coin-badge {
  width: 28px;
  height: 28px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  font-size: 0.75rem;
  font-weight: 800;
  color: #07111d;
}

.coin-badge.up {
  background: linear-gradient(135deg, #c9f4db, #67d8a7);
}

.coin-badge.down {
  background: linear-gradient(135deg, #f9b7bc, #ef6d77);
}

.coin-copy {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
}

.coin-copy strong,
.market-side strong {
  font-size: 0.9rem;
  color: #edf3ff;
  font-weight: 800;
}

.coin-copy small {
  color: rgba(169,176,195,0.8);
  font-size: 0.62rem;
}

.sparkline-wrap {
  width: 100%;
  height: 30px;
}

.sparkline-wrap svg {
  width: 100%;
  height: 100%;
}

.market-side {
  text-align: left;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.market-side strong {
  letter-spacing: -0.02em;
}

.market-side span {
  font-size: 0.66rem;
  font-weight: 700;
}

.line-up {
  fill: none;
  stroke: #16c784;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.line-down {
  fill: none;
  stroke: #ea3943;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}
</style>
