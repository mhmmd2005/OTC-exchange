<script setup>
const props = defineProps({ pair: String, buy: Number, sell: Number, change: Number, pct: Number, trend: String, status: String })
</script>

<template>
  <div class="card price-card">
    <div class="price-header">
      <div class="pair-title">{{ pair }}</div>
      <span :class="['market-status', trend]">{{ status }}</span>
    </div>
    <div class="price-body">
      <div>
        <div class="muted-small">خرید</div>
        <div class="price-main">{{ Number(buy).toLocaleString('fa-IR') }}</div>
      </div>
      <div>
        <div class="muted-small">فروش</div>
        <div class="price-main">{{ Number(sell).toLocaleString('fa-IR') }}</div>
      </div>
      <div class="change-box">
        <div class="change-label">تغییر 24h</div>
        <div :class="['price-main', trend === 'up' ? 'success' : 'danger']" style="font-size: 1rem;">{{ Number(change).toLocaleString('fa-IR') }}</div>
        <div :class="['market-status', trend]">{{ pct }}%</div>
      </div>
    </div>
  </div>
</template>
