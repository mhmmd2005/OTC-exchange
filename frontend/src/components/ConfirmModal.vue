<script setup>
import BaseModal from './BaseModal.vue'
const emit = defineEmits(['confirm', 'close'])
const props = defineProps({ open: { type: Boolean, default: false }, title: { type: String, default: 'تأیید عملیات' }, message: { type: String, default: 'آیا مطمئن هستید؟' } })
</script>

<template>
  <BaseModal :open="open" @close="emit('close')">
    <div class="modal-header">
      <h3>{{ title }}</h3>
      <button class="icon-btn" @click="emit('close')">✕</button>
    </div>
    <p class="muted">{{ message }}</p>
    <div class="modal-actions">
      <button class="ghost-btn" @click="emit('close')">انصراف</button>
      <button class="primary-btn" @click="emit('confirm')">تأیید</button>
    </div>
  </BaseModal>
</template>
