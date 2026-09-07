<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, useId, watch, type ComponentPublicInstance } from 'vue'
import AppIcon from './AppIcon.vue'

const props = withDefaults(defineProps<{
  modelValue?: string
  length?: number
  label?: string
  error?: string
  loading?: boolean
  resendLoading?: boolean
  autofocus?: boolean
  countdownSeconds?: number
  disabled?: boolean
}>(), {
  modelValue: '',
  length: 6,
  label: 'کد تأیید پیامک‌شده را وارد کنید',
  error: '',
  loading: false,
  resendLoading: false,
  autofocus: true,
  countdownSeconds: 120,
  disabled: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  complete: [value: string]
  resend: []
}>()

const controlId = `otp-${useId()}`
const digits = ref<string[]>(Array.from({ length: props.length }, () => ''))
const inputs = ref<Array<HTMLInputElement | null>>([])
const remaining = ref(Math.max(0, props.countdownSeconds))
let countdownTimer: number | undefined
let deadline = 0
let lastCompletedCode = ''

function normalizeDigits(value: string): string {
  return value
    .replace(/[۰-۹]/g, digit => String('۰۱۲۳۴۵۶۷۸۹'.indexOf(digit)))
    .replace(/[٠-٩]/g, digit => String('٠١٢٣٤٥٦٧٨٩'.indexOf(digit)))
}

function numericValue(value: string): string {
  return normalizeDigits(value).replace(/\D/g, '')
}

function setInputRef(element: Element | ComponentPublicInstance | null, index: number) {
  inputs.value[index] = element instanceof HTMLInputElement ? element : null
}

function focusInput(index: number, select = true) {
  const boundedIndex = Math.max(0, Math.min(index, props.length - 1))
  nextTick(() => {
    const input = inputs.value[boundedIndex]
    input?.focus()
    if (select) input?.select()
  })
}

function publishValue() {
  const value = digits.value.join('')
  emit('update:modelValue', value)

  if (value.length === props.length) {
    if (value !== lastCompletedCode) {
      lastCompletedCode = value
      emit('complete', value)
    }
  } else {
    lastCompletedCode = ''
  }
}

function fillDigits(value: string, startIndex = 0) {
  const cleanValue = numericValue(value)
  if (!cleanValue) return

  const targetStart = cleanValue.length >= props.length ? 0 : startIndex
  const available = props.length - targetStart
  cleanValue.slice(0, available).split('').forEach((digit, offset) => {
    digits.value[targetStart + offset] = digit
  })

  publishValue()
  const nextIndex = Math.min(targetStart + cleanValue.length, props.length - 1)
  focusInput(nextIndex)
}

function handleInput(event: Event, index: number) {
  const input = event.target as HTMLInputElement
  const cleanValue = numericValue(input.value)

  if (cleanValue.length > 1) {
    fillDigits(cleanValue, index)
    return
  }

  digits.value[index] = cleanValue.slice(-1)
  input.value = digits.value[index]
  publishValue()

  if (digits.value[index] && index < props.length - 1) focusInput(index + 1)
}

function handleKeydown(event: KeyboardEvent, index: number) {
  if (event.key === 'Backspace') {
    event.preventDefault()
    if (digits.value[index]) {
      digits.value[index] = ''
      publishValue()
      return
    }

    if (index > 0) {
      digits.value[index - 1] = ''
      publishValue()
      focusInput(index - 1)
    }
    return
  }

  if (event.key === 'Delete') {
    event.preventDefault()
    digits.value[index] = ''
    publishValue()
    return
  }

  if (event.key === 'ArrowLeft') {
    event.preventDefault()
    focusInput(index - 1)
  } else if (event.key === 'ArrowRight') {
    event.preventDefault()
    focusInput(index + 1)
  } else if (event.key === 'Home') {
    event.preventDefault()
    focusInput(0)
  } else if (event.key === 'End') {
    event.preventDefault()
    focusInput(props.length - 1)
  }
}

function handlePaste(event: ClipboardEvent) {
  const clipboardValue = event.clipboardData?.getData('text') ?? ''
  const cleanValue = numericValue(clipboardValue)
  if (!cleanValue) return

  event.preventDefault()
  digits.value = Array.from({ length: props.length }, (_, index) => cleanValue[index] ?? '')
  publishValue()
  focusInput(Math.min(cleanValue.length, props.length) - 1)
}

function clearTimer() {
  if (countdownTimer !== undefined) window.clearInterval(countdownTimer)
  countdownTimer = undefined
}

function updateCountdown() {
  remaining.value = Math.max(0, Math.ceil((deadline - Date.now()) / 1000))
  if (remaining.value === 0) clearTimer()
}

function restartCountdown(seconds = props.countdownSeconds) {
  clearTimer()
  remaining.value = Math.max(0, seconds)
  if (remaining.value === 0) return

  deadline = Date.now() + remaining.value * 1000
  countdownTimer = window.setInterval(updateCountdown, 1000)
}

function handleResend() {
  if (remaining.value > 0 || props.resendLoading || props.disabled) return
  emit('resend')
}

function clear() {
  digits.value = Array.from({ length: props.length }, () => '')
  lastCompletedCode = ''
  publishValue()
  focusInput(0)
}

const timerLabel = computed(() => {
  const minutes = Math.floor(remaining.value / 60)
  const seconds = remaining.value % 60
  const formatted = `${minutes}:${seconds.toString().padStart(2, '0')}`
  return new Intl.NumberFormat('fa-IR', { useGrouping: false }).format(Number(minutes))
    + ':'
    + new Intl.NumberFormat('fa-IR', { minimumIntegerDigits: 2, useGrouping: false }).format(seconds)
    || formatted
})

watch(() => props.modelValue, (value) => {
  const cleanValue = numericValue(value).slice(0, props.length)
  if (cleanValue === digits.value.join('')) return
  digits.value = Array.from({ length: props.length }, (_, index) => cleanValue[index] ?? '')
  if (cleanValue.length < props.length) lastCompletedCode = ''
}, { immediate: true })

watch(() => props.countdownSeconds, seconds => restartCountdown(seconds))

watch(() => props.length, (length) => {
  const currentValue = digits.value.join('').slice(0, length)
  digits.value = Array.from({ length }, (_, index) => currentValue[index] ?? '')
})

onMounted(() => {
  restartCountdown()
  if (props.autofocus) focusInput(0, false)
})

onBeforeUnmount(clearTimer)

defineExpose({ focus: () => focusInput(0), clear, restartCountdown })
</script>

<template>
  <div
    class="otp"
    :class="{ 'otp--error': error, 'otp--loading': loading }"
    :aria-busy="loading || undefined"
  >
    <fieldset class="otp__fieldset" :disabled="disabled || loading">
      <legend class="otp__label">{{ label }}</legend>

      <div
        class="otp__inputs"
        dir="ltr"
        role="group"
        :aria-label="label"
        :aria-describedby="error ? `${controlId}-error` : `${controlId}-status`"
        :aria-invalid="!!error"
        @paste="handlePaste"
      >
        <input
          v-for="(_, index) in digits"
          :key="index"
          :ref="element => setInputRef(element, index)"
          :value="digits[index]"
          class="otp__input"
          type="text"
          inputmode="numeric"
          pattern="[0-9۰-۹٠-٩]*"
          maxlength="6"
          :autocomplete="index === 0 ? 'one-time-code' : 'off'"
          autocapitalize="off"
          autocorrect="off"
          spellcheck="false"
          :aria-label="`رقم ${index + 1} از ${length}`"
          :aria-invalid="!!error"
          @focus="($event.target as HTMLInputElement).select()"
          @input="handleInput($event, index)"
          @keydown="handleKeydown($event, index)"
        >
      </div>
    </fieldset>

    <div class="otp__meta">
      <p v-if="error" :id="`${controlId}-error`" class="otp__error" role="alert">
        <AppIcon name="warning" :size="16" />
        <span>{{ error }}</span>
      </p>
      <p v-else-if="loading" :id="`${controlId}-status`" class="otp__status" role="status">
        <span class="otp__spinner" aria-hidden="true" />
        در حال بررسی کد…
      </p>
      <p v-else :id="`${controlId}-status`" class="otp__status">
        <template v-if="remaining > 0">
          <AppIcon name="clock" :size="16" />
          ارسال مجدد تا <bdi dir="ltr">{{ timerLabel }}</bdi>
        </template>
        <template v-else>کدی دریافت نکردید؟</template>
      </p>
      <span v-if="!error && !loading && remaining === 0" class="sr-only" role="status">اکنون می‌توانید کد را دوباره ارسال کنید.</span>

      <button
        class="otp__resend"
        type="button"
        :disabled="remaining > 0 || resendLoading || disabled"
        :aria-busy="resendLoading || undefined"
        @click="handleResend"
      >
        <span v-if="resendLoading" class="otp__spinner" aria-hidden="true" />
        <AppIcon v-else name="refresh" :size="16" />
        {{ resendLoading ? 'در حال ارسال' : 'ارسال مجدد کد' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.otp { display: grid; gap: var(--space-3); }
.otp__fieldset { min-width: 0; margin: 0; padding: 0; border: 0; }

.otp__label {
  width: 100%;
  margin-bottom: var(--space-3);
  padding: 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 500;
}

.otp__inputs {
  display: grid;
  grid-template-columns: repeat(v-bind(length), minmax(0, 1fr));
  gap: clamp(.35rem, 1.4vw, .65rem);
}

.otp__input {
  width: 100%;
  min-width: 0;
  height: clamp(3.15rem, 8vw, 3.8rem);
  padding: 0;
  border: 1px solid var(--control-border);
  border-radius: var(--radius-md);
  outline: 0;
  background: var(--color-surface-2);
  color: var(--color-text-primary);
  caret-color: var(--color-primary);
  font-family: var(--font-family);
  font-size: clamp(1.15rem, 3vw, 1.45rem);
  font-variant-numeric: tabular-nums;
  font-weight: 600;
  text-align: center;
  transition: border-color var(--transition-fast), background var(--transition-fast), box-shadow var(--transition-fast), transform var(--transition-fast);
}

.otp__input:hover:not(:disabled) { border-color: var(--color-border-hover); }

.otp__input:focus {
  border-color: var(--color-border-focus);
  background: var(--color-surface-1);
  box-shadow: var(--shadow-focus);
  transform: translateY(-1px);
}

.otp__input:disabled { cursor: not-allowed; opacity: .58; }
.otp--error .otp__input { border-color: var(--color-danger); }

.otp__meta {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  min-height: 2.5rem;
  align-items: center;
  gap: var(--space-3);
}

.otp__status,
.otp__error {
  display: inline-flex;
  min-width: 0;
  align-items: center;
  gap: var(--space-2);
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.otp__error { color: var(--color-danger); }
.otp__status bdi { color: var(--color-text-secondary); font-weight: 600; }

.otp__resend {
  display: inline-flex;
  min-height: 2.75rem;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding-inline: var(--space-2);
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-primary);
  font-size: var(--font-size-xs);
  font-weight: 600;
  white-space: nowrap;
}

.otp__resend:hover:not(:disabled) { background: var(--color-primary-soft); color: var(--color-primary-hover); }
.otp__resend:disabled { cursor: default; color: var(--color-text-muted); opacity: .7; }

.otp__spinner {
  width: 1rem;
  height: 1rem;
  flex: 0 0 auto;
  border: 2px solid currentColor;
  border-inline-end-color: transparent;
  border-radius: 50%;
  animation: otp-spin .7s linear infinite;
}

@keyframes otp-spin { to { transform: rotate(360deg); } }

@media (max-width: 420px) {
  .otp__inputs { gap: .32rem; }
  .otp__input { height: 3.05rem; border-radius: .72rem; font-size: 1.1rem; }
  .otp__meta { grid-template-columns: 1fr; align-items: flex-start; gap: var(--space-1); }
  .otp__resend { justify-self: start; }
}
</style>
