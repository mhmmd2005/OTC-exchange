<script setup>
import BaseButton from './BaseButton.vue'
const props = defineProps({ wallet: { type: Object, required: true } })
</script>

<template>
  <div class="card wallet-card">
    <div class="wallet-row">
      <div>
        <div class="muted-small">{{ wallet.name }}</div>
        <div class="wallet-balance">{{ Number(wallet.balance).toLocaleString('fa-IR') }}</div>
      </div>
      <span class="inline-tag info">{{ wallet.symbol }}</span>
    </div>
    <div class="wallet-row">
      <span class="muted-small">قابل برداشت</span>
      <strong>{{ Number(wallet.available).toLocaleString('fa-IR') }}</strong>
    </div>
    <div class="wallet-row">
      <span class="muted-small">در انتظار</span>
      <strong>{{ Number(wallet.pending).toLocaleString('fa-IR') }}</strong>
    </div>
    <div class="wallet-address">{{ wallet.address }}</div>
    <div class="wallet-actions">
      <BaseButton variant="secondary">واریز</BaseButton>
      <BaseButton variant="secondary">برداشت</BaseButton>
      <BaseButton variant="ghost">انتقال</BaseButton>
    </div>
  </div>
</template>
