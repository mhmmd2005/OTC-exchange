<script setup>
const model = defineModel()
const props = defineProps({
  label: String,
  placeholder: String,
  type: { type: String, default: 'text' },
})
</script>

<template>
  <div class="field">
    <label v-if="label">{{ label }}</label>
    <input v-model="model" :type="type" :placeholder="placeholder" class="input" />
  </div>
</template>
