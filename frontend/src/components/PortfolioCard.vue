<script setup>
import {computed} from 'vue'

const props = withDefaults(
    defineProps({
      portfolio: {
        type: Object,
        default: () => ({
          totalUsd: 1842600,
          pnl24h: 9340,
          pnlPct24h: 2.8,
          holdings: 4,
          sparkline: [42, 46, 44, 52, 58, 61, 64, 68, 72, 75, 79, 82],
          primaryAsset: 'BTC',
          secondaryAsset: 'USDT',
        }),
      },
    }),
    {}
)

const pnlPositive = computed(() => props.portfolio.pnl24h >= 0)

const formatMoney = (value) =>
    new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0,
    }).format(value)

const formatCompact = (value) =>
    new Intl.NumberFormat('en-US', {
      notation: 'compact',
      maximumFractionDigits: 1,
    }).format(value)

const sparkPoints = computed(() => {
  const values = props.portfolio.sparkline
  const width = 300
  const height = 90
  const max = Math.max(...values)
  const min = Math.min(...values)
  const range = max - min || 1

  return values
      .map((value, index) => {
        const x = (index / (values.length - 1)) * width
        const y = height - ((value - min) / range) * (height - 16) - 8
        return `${x},${y}`
      })
      .join(' ')
})
</script>

<template>
  <article class="portfolio-card">
    <header class="card-head">
      <div>
        <div class="eyebrow">Portfolio</div>
        <h3>Total Balance</h3>
      </div>

      <div :class="['pnl-pill', pnlPositive ? 'positive' : 'negative']">
        <span class="icon-dot">↗</span>
        {{ pnlPositive ? '+' : '' }}{{ props.portfolio.pnlPct24h.toFixed(2) }}% / {{
          formatMoney(props.portfolio.pnl24h)
        }}
      </div>
    </header>

    <div class="balance-section">
      <div>
        <div class="label">Net Asset Value</div>
        <div class="balance">{{ formatMoney(props.portfolio.totalUsd) }}</div>
      </div>
      <div class="asset-count">{{ props.portfolio.holdings }} assets</div>
    </div>

    <div class="mini-meta">
      <span>{{ props.portfolio.primaryAsset }} 0.82</span>
      <span>{{ props.portfolio.secondaryAsset }} 12,500</span>
    </div>

    <svg class="sparkline" viewBox="0 0 300 90" preserveAspectRatio="none" aria-label="Portfolio equity growth">
      <defs>
        <linearGradient id="portfolioGlow" x1="0" x2="1">
          <stop offset="0%" stop-color="#10B981" stop-opacity="0.3"/>
          <stop offset="100%" stop-color="#10B981" stop-opacity="0.02"/>
        </linearGradient>
      </defs>
      <polyline
          :points="sparkPoints"
          fill="none"
          stroke="#10B981"
          stroke-width="3"
          stroke-linecap="round"
          stroke-linejoin="round"
      />
      <polygon :points="`0,90 ${sparkPoints} 300,90`" fill="url(#portfolioGlow)" opacity="0.9"/>
    </svg>

    <div class="stats-mini">
      <div>
        <span>24h PnL</span>
        <strong class="positive">+{{ formatCompact(props.portfolio.pnl24h) }}</strong>
      </div>
      <div>
        <span>Volume</span>
        <strong>$2.4M</strong>
      </div>
      <div>
        <span>Win rate</span>
        <strong>68%</strong>
      </div>
    </div>

    <div class="action-row">
      <button type="button" class="mini-action ok">Deposit</button>
      <button type="button" class="mini-action neutral">Withdraw</button>
      <button type="button" class="mini-action info">Transfer</button>
    </div>
  </article>
</template>

<style scoped>
.portfolio-card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 20px 18px 18px;
  border-radius: 20px;
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.82), rgba(15, 23, 42, 0.94));
  border: 1px solid rgba(148, 163, 184, 0.14);
  box-shadow: 0 16px 28px rgba(3, 7, 18, 0.28), inset 0 1px 0 rgba(255, 255, 255, 0.04);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.portfolio-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 18px 36px rgba(16, 185, 129, 0.08), 0 12px 28px rgba(15, 23, 42, 0.26);
}

.card-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.eyebrow {
  margin: 0 0 4px;
  color: rgba(148, 163, 184, 0.9);
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.card-head h3 {
  margin: 0;
  font-size: 1.04rem;
  font-weight: 700;
  color: #e2e8f0;
}

.pnl-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 0.68rem;
  font-weight: 700;
  white-space: nowrap;
}

.pnl-pill.positive {
  background: rgba(16, 185, 129, 0.12);
  color: #a7f3d0;
}

.pnl-pill.negative {
  background: rgba(239, 68, 68, 0.12);
  color: #fecaca;
}

.icon-dot {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.08);
  font-size: 0.6rem;
}

.balance-section {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 12px;
}

.label {
  color: rgba(148, 163, 184, 0.8);
  font-size: 0.68rem;
  margin-bottom: 8px;
}

.balance {
  font-size: clamp(1.9rem, 3vw, 2.5rem);
  letter-spacing: -0.06em;
  font-weight: 800;
  color: #f8fafc;
}

.asset-count {
  color: rgba(148, 163, 184, 0.85);
  font-size: 0.7rem;
  font-weight: 700;
}

.mini-meta {
  display: flex;
  justify-content: space-between;
  font-size: 0.72rem;
  color: rgba(148, 163, 184, 0.82);
}

.sparkline {
  width: 100%;
  height: 90px;
  display: block;
  background: linear-gradient(180deg, rgba(16, 185, 129, 0.05), transparent);
  border-radius: 12px;
  overflow: hidden;
}

.stats-mini {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  padding-top: 2px;
}

.stats-mini div {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stats-mini span {
  color: rgba(148, 163, 184, 0.8);
  font-size: 0.66rem;
}

.stats-mini strong {
  color: #f8fafc;
  font-size: 0.8rem;
}

.positive {
  color: #a7f3d0;
}

.action-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.mini-action {
  flex: 1 1 0;
  min-height: 34px;
  border: 1px solid rgba(148, 163, 184, 0.12);
  border-radius: 8px;
  background: rgba(15, 23, 42, 0.6);
  color: #e2e8f0;
  font-size: 0.72rem;
  font-weight: 700;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.mini-action:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 18px rgba(15, 23, 42, 0.18);
}

.mini-action.ok {
  background: rgba(16, 185, 129, 0.12);
  color: #a7f3d0;
}

.mini-action.neutral {
  background: rgba(148, 163, 184, 0.08);
}

.mini-action.info {
  background: rgba(59, 130, 246, 0.12);
  color: #bfdbfe;
}
</style>
