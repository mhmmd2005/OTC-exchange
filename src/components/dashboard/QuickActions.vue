<script setup>
const actions = [
  { title: 'انتقال', icon: '⇄', description: 'بین دارایی‌ها', tone: 'neutral' },
  { title: 'برداشت', icon: '↓', description: 'به حساب بانکی', tone: 'danger' },
  { title: 'واریز', icon: '↑', description: 'افزایش موجودی', tone: 'success' },
  { title: 'معامله OTC', icon: '◌', description: 'ثبت سفارش', tone: 'gold' },
]
</script>

<template>
  <section class="quick-actions panel-surface">
    <div class="panel-header-lite">
      <div>
        <span class="kicker">عملیات سریع</span>
        <h3>دسترسی سریع</h3>
      </div>
    </div>

    <div class="action-grid">
      <button v-for="action in actions" :key="action.title" type="button" class="action-tile" :class="action.tone">
        <span class="action-icon">{{ action.icon }}</span>
        <span class="action-copy">
          <strong>{{ action.title }}</strong>
          <small>{{ action.description }}</small>
        </span>
      </button>
    </div>
  </section>
</template>

<style scoped>
.quick-actions {
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

.action-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.action-tile {
  width: 100%;
  border: 1px solid rgba(255,255,255,0.06);
  background: rgba(255,255,255,0.02);
  border-radius: 14px;
  padding: 14px 12px;
  text-align: right;
  color: #edf3ff;
  display: flex;
  align-items: center;
  gap: 10px;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.action-tile:hover {
  transform: translateY(-3px);
  border-color: rgba(212,169,90,0.18);
  box-shadow: 0 14px 26px rgba(0,0,0,0.18);
}

.action-icon {
  width: 36px;
  height: 36px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  font-size: 1.2rem;
  font-weight: 700;
  background: rgba(212,169,90,0.12);
  color: #f1d089;
}

.action-copy {
  display: flex;
  flex-direction: column;
  gap: 3px;
  align-items: flex-start;
  flex: 1;
}

.action-copy strong {
  font-size: 0.9rem;
}

.action-copy small {
  color: rgba(169,176,195,0.8);
  font-size: 0.62rem;
}
</style>
