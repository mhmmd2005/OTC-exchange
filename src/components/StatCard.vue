<script setup>
defineProps({ label: String, value: [String, Number], suffix: String, trend: String, change: [Number, String] })
</script>

<template>
  <div class="card stat-card">
    <div class="stat-top">
      <div class="stat-label">{{ label }}</div>
      <div class="stat-icon">◈</div>
    </div>
    <div class="stat-value">{{ value }} <span class="muted-small">{{ suffix }}</span></div>
    <div class="stat-meta">
      <span :class="['stat-change', trend]">{{ change }}</span>
      <span>در ۲۴ ساعت</span>
    </div>
  </div>
</template>
