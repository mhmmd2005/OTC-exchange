<script setup>
const emit = defineEmits(['close'])
const props = defineProps({ open: { type: Boolean, default: false } })
</script>

<template>
  <div v-if="open" class="modal-backdrop" @click.self="emit('close')">
    <div class="modal-card">
      <slot />
    </div>
  </div>
</template>
