<script setup>
import { computed } from 'vue'

const tabs = ['روز', 'هفته', 'ماه', 'سال']
const activeTab = 'هفته'

const points = computed(() => {
  const values = [18, 24, 20, 28, 32, 30, 35, 38, 35, 42, 48, 46]
  const width = 520
  const height = 170
  const max = Math.max(...values)
  const min = Math.min(...values)
  const stepX = width / (values.length - 1)

  return values
    .map((value, index) => {
      const x = index * stepX
      const y = height - ((value - min) / (max - min || 1)) * 100 - 18
      return `${x},${y}`
    })
    .join(' ')
})
</script>

<template>
  <section class="portfolio-chart panel-surface">
    <div class="panel-header-lite">
      <div>
        <span class="kicker">عملکرد</span>
        <h3>نمودار عملکرد</h3>
      </div>
      <div class="tab-group">
        <button v-for="tab in tabs" :key="tab" type="button" :class="['tab-item', { active: tab === activeTab }]">
          {{ tab }}
        </button>
      </div>
    </div>

    <div class="chart-wrap">
      <svg viewBox="0 0 520 170" preserveAspectRatio="none" aria-label="نمودار عملکرد">
        <defs>
          <linearGradient id="lineFill" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stop-color="rgba(58,111,248,0.32)" />
            <stop offset="100%" stop-color="rgba(58,111,248,0.02)" />
          </linearGradient>
        </defs>

        <g class="grid-gridlines">
          <line x1="0" y1="20" x2="520" y2="20" />
          <line x1="0" y1="60" x2="520" y2="60" />
          <line x1="0" y1="100" x2="520" y2="100" />
          <line x1="0" y1="140" x2="520" y2="140" />
        </g>

        <polyline class="area-shade" :points="`${points} 520,170 0,170`" />
        <polyline class="line-graph" :points="points" />
      </svg>
    </div>
  </section>
</template>

<style scoped>
.portfolio-chart {
  padding: 18px 16px;
}

.panel-header-lite {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
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

.tab-group {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px;
  border-radius: 10px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.04);
}

.tab-item {
  border: 1px solid transparent;
  background: transparent;
  color: rgba(169,176,195,0.8);
  border-radius: 8px;
  padding: 6px 10px;
  font-size: 0.68rem;
  font-weight: 700;
}

.tab-item.active {
  background: rgba(212,169,90,0.08);
  border-color: rgba(212,169,90,0.18);
  color: #f1d089;
}

.chart-wrap {
  height: 210px;
}

svg {
  width: 100%;
  height: 100%;
  display: block;
}

.grid-gridlines line {
  stroke: rgba(255,255,255,0.06);
  stroke-width: 1;
}

.area-shade {
  fill: url(#lineFill);
  stroke: none;
}

.line-graph {
  fill: none;
  stroke: #3a6ff8;
  stroke-width: 3;
  stroke-linecap: round;
  stroke-linejoin: round;
  filter: drop-shadow(0 0 10px rgba(58,111,248,0.32));
}
</style>
