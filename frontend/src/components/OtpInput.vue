<script setup>
import { computed, nextTick, ref, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: '',
  },
  length: {
    type: Number,
    default: 6,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue', 'complete'])
const inputRefs = ref([])
const digits = ref(Array.from({ length: props.length }, () => ''))

const normalizedValue = computed(() => {
  return (props.modelValue || '').slice(0, props.length)
})

watch(
  () => normalizedValue.value,
  (value) => {
    const nextDigits = Array.from({ length: props.length }, (_, index) => value[index] || '')
    digits.value = nextDigits
  },
  { immediate: true }
)

function focusInput(index) {
  if (!inputRefs.value[index]) return
  nextTick(() => {
    inputRefs.value[index]?.focus()
    inputRefs.value[index]?.select()
  })
}

function emitValue(nextDigits) {
  const joined = nextDigits.join('').slice(0, props.length)
  emit('update:modelValue', joined)
  if (joined.length === props.length) {
    emit('complete', joined)
  }
}

function handleInput(event, index) {
  const rawValue = event.target.value.replace(/\D/g, '').slice(-1)
  const nextDigits = [...digits.value]
  nextDigits[index] = rawValue
  digits.value = nextDigits
  emitValue(nextDigits)

  if (rawValue && index < props.length - 1) {
    focusInput(index + 1)
  }
}

function handleKeydown(event, index) {
  if (event.key === 'Backspace' && !digits.value[index] && index > 0) {
    focusInput(index - 1)
    return
  }

  if (event.key === 'ArrowLeft' && index > 0) {
    event.preventDefault()
    focusInput(index - 1)
  }

  if (event.key === 'ArrowRight' && index < props.length - 1) {
    event.preventDefault()
    focusInput(index + 1)
  }

  if (event.key === 'Enter' && digits.value.join('').length === props.length) {
    emit('complete', digits.value.join(''))
  }
}

function handlePaste(event) {
  event.preventDefault()
  const pasted = (event.clipboardData.getData('text') || '').replace(/\D/g, '').slice(0, props.length)
  if (!pasted) return

  const nextDigits = Array.from({ length: props.length }, (_, index) => pasted[index] || '')
  digits.value = nextDigits
  emitValue(nextDigits)

  const lastFilledIndex = nextDigits.findLastIndex((digit) => digit)
  const targetIndex = lastFilledIndex >= 0 ? lastFilledIndex : 0
  focusInput(Math.min(targetIndex, props.length - 1))
}
</script>

<template>
  <div class="otp-input-wrap" role="group" :aria-label="'کد تأیید'">
    <input
      v-for="(_, index) in props.length"
      :key="index"
      :ref="(el) => {
        inputRefs[index] = el
      }"
      v-model="digits[index]"
      type="text"
      :inputmode="'numeric'"
      pattern="[0-9]*"
      maxlength="1"
      :disabled="disabled"
      class="otp-input-box"
      :aria-label="`رقم ${index + 1} کد تایید`"
      @input="handleInput($event, index)"
      @keydown="handleKeydown($event, index)"
      @paste="handlePaste"
      @focus="($event.target).select()"
    />
  </div>
</template>
