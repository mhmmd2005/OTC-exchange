<script setup>
const props = defineProps({ status: { type: String, default: 'neutral' } })
const mapping = {
  success: 'success',
  completed: 'success',
  active: 'info',
  pending: 'warning',
  waiting: 'warning',
  rejected: 'danger',
  failed: 'danger',
  cancelled: 'neutral',
  processing: 'info',
  neutral: 'neutral',
}
</script>

<template>
  <span :class="['status-badge', mapping[status] || 'neutral']">{{ status }}</span>
</template>
