<script setup>
defineProps({ title: String, amount: String, change: String, direction: { type: String, default: 'up' } })
</script>

<template>
  <div class="panel">
    <div class="wallet-row">
      <div>
        <div class="muted-small">{{ title }}</div>
        <div class="bold" style="font-size:1.2rem; margin-top:4px;">{{ amount }}</div>
      </div>
      <span :class="['inline-tag', direction === 'up' ? 'success' : 'danger']">{{ change }}</span>
    </div>
  </div>
</template>
