<script setup>
import PremiumSelect from './PremiumSelect.vue'

const model = defineModel()

defineProps({
  label: String,
  options: { type: Array, default: () => [] },
  placeholder: { type: String, default: 'انتخاب کنید' },
  searchable: Boolean,
  disabled: Boolean,
})
</script>

<template>
  <div class="base-select-field">
    <label v-if="label" class="base-select-label">{{ label }}</label>
    <PremiumSelect
      v-model="model"
      :options="options"
      :placeholder="placeholder"
      :searchable="searchable"
      :disabled="disabled"
    />
  </div>
</template>

<style scoped>
.base-select-field {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.base-select-label {
  color: var(--text-secondary);
  font-size: 0.82rem;
  font-weight: 700;
}
</style>