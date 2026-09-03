<script setup>
import { computed } from 'vue'

const props = withDefaults(
  defineProps({
    position: {
      type: Object,
      default: () => ({
        pair: 'BTC/USDT',
        side: 'Long',
        leverage: '20x Cross',
        entryPrice: 68240,
        markPrice: 69520,
        liquidationPrice: 52180,
        pnlUsd: 28420,
        pnlPct: 5.4,
        riskPercent: 62,
      }),
    },
  }),
  {}
)

const formatMoney = (value) =>
  new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 2,
  }).format(value)

const sidePositive = computed(() => props.position.side === 'Long')
const pnlPositive = computed(() => props.position.pnlUsd >= 0)

const riskLevel = computed(() => {
  const value = props.position.riskPercent
  if (value < 35) return 'low'
  if (value < 70) return 'medium'
  return 'high'
})

const riskStyles = computed(() => {
  const level = riskLevel.value
  if (level === 'low') return { gradient: 'linear-gradient(90deg, #10B981 0%, #34D399 100%)', glow: 'rgba(16,185,129,0.34)' }
  if (level === 'medium') return { gradient: 'linear-gradient(90deg, #FBBF24 0%, #F59E0B 100%)', glow: 'rgba(245,158,11,0.32)' }
  return { gradient: 'linear-gradient(90deg, #EF4444 0%, #F97316 100%)', glow: 'rgba(239,68,68,0.34)' }
})
</script>

<template>
  <article class="futures-card">
    <header class="card-head">
      <div class="pair-block">
        <div class="pair-name">{{ props.position.pair }}</div>
        <div class="meta-row">
          <span :class="['side-pill', sidePositive ? 'long' : 'short']">{{ props.position.side }}</span>
          <span class="leverage-pill">{{ props.position.leverage }}</span>
        </div>
      </div>

      <button type="button" class="ghost-button">Manage</button>
    </header>

    <div class="stats-grid">
      <div class="stats-item">
        <span>Entry</span>
        <strong>{{ formatMoney(props.position.entryPrice) }}</strong>
      </div>
      <div class="stats-item">
        <span>Mark</span>
        <strong>{{ formatMoney(props.position.markPrice) }}</strong>
      </div>
      <div class="stats-item">
        <span>Liquidation</span>
        <strong>{{ formatMoney(props.position.liquidationPrice) }}</strong>
      </div>
    </div>

    <div class="pnl-box" :class="pnlPositive ? 'positive' : 'negative'">
      <div>
        <span>Unrealized PnL</span>
        <strong>{{ pnlPositive ? '+' : '' }}{{ formatMoney(props.position.pnlUsd) }}</strong>
      </div>
      <div class="pnl-percent">{{ pnlPositive ? '+' : '' }}{{ props.position.pnlPct.toFixed(2) }}%</div>
    </div>

    <div class="risk-wrap">
      <div class="risk-head">
        <span>Liquidation Risk</span>
        <strong>{{ props.position.riskPercent }}%</strong>
      </div>
      <div class="risk-bar">
        <span :style="{ width: `${props.position.riskPercent}%`, background: riskStyles.gradient, boxShadow: `0 0 18px ${riskStyles.glow}` }" />
      </div>
      <div class="risk-legend">
        <span>Low</span>
        <span>Watch</span>
        <span>Critical</span>
      </div>
    </div>

    <div class="action-row">
      <button type="button" class="action-btn danger">Market Close</button>
      <button type="button" class="action-btn secondary">Add Margin</button>
      <button type="button" class="action-btn success">TP/SL</button>
    </div>
  </article>
</template>

<style scoped>
.futures-card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 20px 18px 18px;
  border-radius: 20px;
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.8), rgba(15, 23, 42, 0.94));
  border: 1px solid rgba(148, 163, 184, 0.12);
  box-shadow: 0 16px 30px rgba(3, 7, 18, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.04);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.futures-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 18px 36px rgba(59, 130, 246, 0.1), 0 16px 30px rgba(3, 7, 18, 0.28);
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.pair-block {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.pair-name {
  font-size: 1.05rem;
  color: #f8fafc;
  font-weight: 800;
}

.meta-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.side-pill,
.leverage-pill,
.ghost-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  padding: 6px 10px;
  font-size: 0.66rem;
  font-weight: 700;
}

.side-pill.long {
  background: rgba(16, 185, 129, 0.12);
  color: #a7f3d0;
}

.side-pill.short {
  background: rgba(239, 68, 68, 0.12);
  color: #fecaca;
}

.leverage-pill {
  background: rgba(59, 130, 246, 0.12);
  color: #bfdbfe;
}

.ghost-button {
  background: rgba(148, 163, 184, 0.08);
  border: 1px solid rgba(148, 163, 184, 0.12);
  color: #e2e8f0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.stats-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px 8px;
  border-radius: 12px;
  background: rgba(15, 23, 42, 0.48);
  border: 1px solid rgba(148, 163, 184, 0.08);
}

.stats-item span {
  color: rgba(148, 163, 184, 0.82);
  font-size: 0.66rem;
}

.stats-item strong {
  color: #f8fafc;
  font-size: 0.82rem;
  font-weight: 700;
}

.pnl-box {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  border-radius: 14px;
  padding: 14px 12px;
}

.pnl-box.positive {
  background: rgba(16, 185, 129, 0.12);
}

.pnl-box.negative {
  background: rgba(239, 68, 68, 0.12);
}

.pnl-box span {
  display: block;
  color: rgba(148, 163, 184, 0.82);
  font-size: 0.68rem;
}

.pnl-box strong {
  display: block;
  margin-top: 4px;
  font-size: 1.12rem;
  color: #f8fafc;
}

.pnl-percent {
  font-size: 0.8rem;
  font-weight: 800;
}

.risk-wrap {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.risk-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: rgba(148, 163, 184, 0.8);
  font-size: 0.67rem;
  font-weight: 700;
}

.risk-head strong {
  color: #f8fafc;
  font-size: 0.72rem;
}

.risk-bar {
  width: 100%;
  height: 10px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.12);
  overflow: hidden;
  position: relative;
}

.risk-bar span {
  display: block;
  height: 100%;
  border-radius: inherit;
}

.risk-legend {
  display: flex;
  justify-content: space-between;
  color: rgba(148, 163, 184, 0.74);
  font-size: 0.62rem;
}

.action-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.action-btn {
  flex: 1 1 0;
  min-height: 36px;
  border: none;
  border-radius: 8px;
  font-size: 0.72rem;
  font-weight: 700;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.action-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 18px rgba(15, 23, 42, 0.18);
}

.action-btn.danger {
  background: rgba(239, 68, 68, 0.12);
  color: #fecaca;
}

.action-btn.secondary {
  background: rgba(148, 163, 184, 0.08);
  color: #e2e8f0;
}

.action-btn.success {
  background: rgba(16, 185, 129, 0.12);
  color: #a7f3d0;
}
</style>
