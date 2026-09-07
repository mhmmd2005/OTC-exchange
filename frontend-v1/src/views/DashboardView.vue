<script setup>
import ActivityTimeline from '../components/dashboard/ActivityTimeline.vue'
import AllocationChart from '../components/dashboard/AllocationChart.vue'
import MarketWidget from '../components/dashboard/MarketWidget.vue'
import PortfolioChart from '../components/dashboard/PortfolioChart.vue'
import PortfolioHero from '../components/dashboard/PortfolioHero.vue'
import QuickActions from '../components/dashboard/QuickActions.vue'
</script>

<template>
  <div class="dashboard-view">
    <div class="dashboard-grid">
      <aside class="left-column">
        <MarketWidget />

        <div class="promo-otc panel-surface">
          <div class="promo-topline">
            <span class="promo-tag">فرصت‌های ویژه</span>
            <span class="promo-live">باز</span>
          </div>
          <h3>فرصت‌های ویژه OTC</h3>
          <p>دسترسی به بهترین قیمت‌ها و نقدینگی</p>
          <button type="button">مشاهده فرصت‌ها</button>
          <div class="promo-symbol" aria-hidden="true">₿</div>
        </div>

        <ActivityTimeline />
      </aside>

      <main class="main-column">
        <PortfolioHero />

        <div class="lower-grid">
          <AllocationChart />
          <PortfolioChart />
        </div>

        <QuickActions />
      </main>
    </div>
  </div>
</template>

<style scoped>
.dashboard-view {
  width: 100%;
  min-height: 100%;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 18px;
  align-items: start;
}

.left-column,
.main-column {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.promo-otc {
  position: relative;
  overflow: hidden;
  padding: 18px 18px 16px;
  min-height: 190px;
  background: linear-gradient(135deg, rgba(18, 22, 32, 0.86), rgba(22, 31, 46, 0.96));
}

.promo-topline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 18px;
}

.promo-tag {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(212, 169, 90, 0.12);
  border: 1px solid rgba(212, 169, 90, 0.2);
  color: #f1d089;
  font-size: 0.66rem;
  font-weight: 800;
}

.promo-live {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 34px;
  height: 24px;
  border-radius: 999px;
  background: rgba(22, 199, 132, 0.12);
  color: #7cf2c0;
  font-size: 0.62rem;
  font-weight: 800;
}

.promo-otc h3 {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 800;
  color: #f8fbff;
}

.promo-otc p {
  margin: 10px 0 18px;
  color: rgba(169, 176, 195, 0.92);
  font-size: 0.8rem;
  line-height: 1.8;
}

.promo-otc button {
  position: relative;
  z-index: 1;
  border: 1px solid rgba(212, 169, 90, 0.22);
  background: linear-gradient(135deg, rgba(212, 169, 90, 0.18), rgba(212, 169, 90, 0.08));
  color: #f7d592;
  border-radius: 12px;
  padding: 10px 16px;
  font-weight: 800;
  min-width: 150px;
}

.promo-symbol {
  position: absolute;
  left: 18px;
  bottom: 12px;
  width: 88px;
  height: 88px;
  display: grid;
  place-items: center;
  border-radius: 22px;
  background: linear-gradient(135deg, rgba(212, 169, 90, 0.14), rgba(255, 255, 255, 0.02));
  border: 1px solid rgba(212, 169, 90, 0.18);
  color: rgba(241, 208, 137, 0.9);
  font-size: 2.8rem;
  font-weight: 800;
  box-shadow: inset 0 0 20px rgba(212, 169, 90, 0.08);
}

.lower-grid {
  display: grid;
  grid-template-columns: minmax(240px, 0.9fr) minmax(0, 1.6fr);
  gap: 18px;
}

@media (max-width: 1100px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }

  .left-column {
    order: 2;
  }

  .main-column {
    order: 1;
  }
}

@media (max-width: 768px) {
  .lower-grid {
    grid-template-columns: 1fr;
  }

  .dashboard-grid {
    gap: 14px;
  }
}
</style>
