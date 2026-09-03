<script setup>
const items = [
  { title: 'واریز USDT', time: '۲ ساعت قبل', amount: '+۵۰٬۰۰۰ USDT', positive: true },
  { title: 'معامله OTC', time: '۴ ساعت قبل', amount: '-1.25 BTC', positive: false },
  { title: 'برداشت تومان', time: 'امروز', amount: '-۲۰٬۰۰۰٬۰۰۰ تومان', positive: false },
  { title: 'معامله موفق', time: 'دیروز', amount: '+۱۰٬۰۰۰ USDT', positive: true },
  { title: 'واریز USDT', time: '۳ روز قبل', amount: '+۵٬۰۰۰ USDT', positive: true },
]
</script>

<template>
  <aside class="activity-timeline panel-surface">
    <div class="panel-header-lite">
      <div>
        <span class="kicker">فعالیت</span>
        <h3>فعالیت‌های اخیر</h3>
      </div>
      <button type="button" class="ghost-link">بیشتر</button>
    </div>

    <div class="timeline-list">
      <div v-for="(item, index) in items" :key="`${item.title}-${index}`" class="timeline-item">
        <div class="timeline-track">
          <span class="timeline-dot" :class="item.positive ? 'positive' : 'negative'" />
          <span v-if="index < items.length - 1" class="timeline-line" />
        </div>

        <div class="timeline-copy">
          <div class="time-row">
            <span>{{ item.time }}</span>
          </div>
          <strong>{{ item.title }}</strong>
          <div :class="['amount', item.positive ? 'positive' : 'negative']">{{ item.amount }}</div>
        </div>
      </div>
    </div>
  </aside>
</template>

<style scoped>
.activity-timeline {
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

.timeline-list {
  display: grid;
  gap: 16px;
}

.timeline-item {
  display: grid;
  grid-template-columns: 18px 1fr;
  gap: 12px;
  align-items: flex-start;
}

.timeline-track {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 18px;
  padding-top: 4px;
}

.timeline-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: block;
  position: relative;
  z-index: 1;
}

.timeline-dot.positive {
  background: #16c784;
  box-shadow: 0 0 0 4px rgba(22,199,132,0.12);
}

.timeline-dot.negative {
  background: #ea3943;
  box-shadow: 0 0 0 4px rgba(234,57,67,0.12);
}

.timeline-line {
  display: block;
  width: 1px;
  flex: 1;
  margin-top: 4px;
  background: linear-gradient(180deg, rgba(212,169,90,0.8), rgba(255,255,255,0.06));
}

.timeline-copy {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.time-row {
  color: rgba(169,176,195,0.8);
  font-size: 0.62rem;
}

.timeline-copy strong {
  color: #edf3ff;
  font-size: 0.82rem;
  font-weight: 700;
}

.amount {
  font-size: 0.72rem;
  font-weight: 800;
}

.amount.positive {
  color: #7cf2c0;
}

.amount.negative {
  color: #ff7f86;
}
</style>
