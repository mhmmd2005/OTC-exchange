<!-- src/components/accounts/billing/AmountPicker.vue -->
<script setup lang="ts">
import { computed, ref, onMounted, watch } from 'vue'

const props = defineProps<{
  modelValue: number
  min?: number
  max?: number
  currency?: string
  presets?: number[]
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', v: number): void
}>()

// Safe defaults (min/max should also be enforced on backend)
const min = computed(() => props.min ?? 15)
const max = computed(() => props.max ?? 1000)
const currency = computed(() => props.currency ?? 'USD')

function loadPresets(): number[] {
  // 1) from prop
  if (props.presets && props.presets.length) return props.presets

  // 2) from env (e.g. VITE_BILLING_PRESETS="15,25,50,100,250")
  const env = import.meta.env.VITE_BILLING_PRESETS as string | undefined
  if (env) {
    const arr = env.split(',').map(s => Number(s.trim())).filter(n => !Number.isNaN(n))
    if (arr.length) return arr
  }

  // 3) fallback
  return [15, 25, 50, 100, 250]
}

const presets = ref<number[]>([])
const selected = ref<'preset' | 'other'>('preset')
const other = ref<string>('')

// Initialize presets and sync initial value
onMounted(() => {
  presets.value = loadPresets().filter(v => v >= min.value && v <= max.value)
  if (!presets.value.includes(props.modelValue)) {
    selected.value = 'other'
    other.value = props.modelValue ? String(props.modelValue) : ''
  }
})

// If parent changes the amount to non-preset, switch to "other"
watch(() => props.modelValue, (v) => {
  if (selected.value === 'preset' && !presets.value.includes(v)) {
    selected.value = 'other'
    other.value = v ? String(v) : ''
  }
})

function pick(v: number) {
  selected.value = 'preset'
  other.value = ''
  emit('update:modelValue', v)
}

const errorMsg = computed(() => {
  const val = selected.value === 'preset' ? props.modelValue : Number(other.value || 0)
  if (!val) return ''
  if (val < min.value) return `Minimum is ${currency.value} ${min.value}`
  if (val > max.value) return `Maximum is ${currency.value} ${max.value}`
  return ''
})

function commitOther() {
  const val = Number(other.value || 0)
  if (!val || val < min.value || val > max.value) return
  emit('update:modelValue', val)
}
</script>

<template>
  <div>
    <div class="mb-2 text-subtitle-2">Choose Payment Amount</div>

    <div class="d-flex flex-wrap ga-2">
      <v-btn
        v-for="p in presets"
        :key="p"
        size="small"
        variant="tonal"
        class="rounded-pill"
        :color="modelValue === p && selected==='preset' ? 'primary' : undefined"
        @click="pick(p)"
      >
        {{ currency }} {{ p }}
      </v-btn>

      <v-btn
        size="small"
        variant="outlined"
        class="rounded-pill"
        :color="selected==='other' ? 'primary' : undefined"
        @click="selected='other'"
      >
        Other
      </v-btn>
    </div>

    <div v-if="selected==='other'" class="mt-3" style="max-width:320px;">
      <v-text-field
        v-model="other"
        type="number"
        :min="min"
        :max="max"
        :step="1"
        :label="`Other amount (${currency})`"
        variant="outlined"
        density="comfortable"
        class="rounded-xl"
        @change="commitOther"
        @blur="commitOther"
      />
    </div>

    <v-alert v-if="errorMsg" type="warning" variant="tonal" class="mt-2 rounded-lg">
      {{ errorMsg }}
    </v-alert>
  </div>
</template>
