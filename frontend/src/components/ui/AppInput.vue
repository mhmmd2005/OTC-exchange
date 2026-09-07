<script setup lang="ts">
import { computed, ref, useId } from 'vue'
import AppIcon from './AppIcon.vue'

const props = withDefaults(defineProps<{
  modelValue?: string
  label?: string
  placeholder?: string
  hint?: string
  error?: string
  type?: string
  inputmode?: 'text' | 'numeric' | 'decimal' | 'tel' | 'email' | 'search' | 'url'
  autocomplete?: string
  disabled?: boolean
  readonly?: boolean
  ltr?: boolean
  icon?: string
  suffix?: string
  ariaLabel?: string
  name?: string
  required?: boolean
  maxlength?: number | string
  minlength?: number | string
}>(), { modelValue: '', type: 'text', inputmode: 'text', disabled: false, readonly: false, ltr: false })

const emit = defineEmits<{ 'update:modelValue': [value: string]; blur: [event: FocusEvent]; focus: [event: FocusEvent] }>()
const reveal = ref(false)
const inputType = computed(() => props.type === 'password' && reveal.value ? 'text' : props.type)
const controlId = `input-${useId()}`
const accessibleName = computed(() => props.ariaLabel || (!props.label ? props.placeholder : undefined))
</script>

<template>
  <div class="field">
    <label v-if="label" class="field__label" :for="controlId">{{ label }}<i v-if="required" aria-hidden="true">*</i></label>
    <div class="field__control" :class="{ 'field__control--error': error, 'is-disabled': disabled, 'is-readonly': readonly }">
      <AppIcon v-if="icon" class="field__icon" :name="icon" :size="20" />
      <input
        :id="controlId"
        :value="modelValue"
        :type="inputType"
        :inputmode="inputmode"
        :placeholder="placeholder"
        :autocomplete="autocomplete"
        :disabled="disabled"
        :readonly="readonly"
        :name="name"
        :required="required"
        :maxlength="maxlength"
        :minlength="minlength"
        :dir="ltr ? 'ltr' : undefined"
        :aria-label="accessibleName"
        :aria-invalid="!!error"
        :aria-describedby="hint || error ? `${controlId}-message` : undefined"
        @input="emit('update:modelValue', ($event.target as HTMLInputElement).value)"
        @focus="emit('focus', $event)"
        @blur="emit('blur', $event)"
      />
      <button v-if="type === 'password'" class="field__action" type="button" :aria-label="reveal ? 'مخفی کردن رمز عبور' : 'نمایش رمز عبور'" @click.prevent="reveal = !reveal">
        <AppIcon :name="reveal ? 'eye-off' : 'eye'" :size="20" />
      </button>
      <span v-else-if="suffix" class="field__suffix">{{ suffix }}</span>
      <slot name="action" />
    </div>
    <span v-if="error || hint" :id="`${controlId}-message`" class="field__message" :class="{ 'field__message--error': error }">{{ error || hint }}</span>
  </div>
</template>

<style scoped>
.field { display: grid; gap: .45rem; min-width: 0; }
.field__label { color: var(--text-secondary); font-size: var(--font-size-sm); font-weight: 500; }
.field__label i { margin-inline-start: .25rem; color: var(--color-danger); font-style: normal; }
.field__control { display: flex; align-items: center; gap: var(--space-2); min-height: var(--control-height); padding-inline: var(--space-4); border: 1px solid var(--control-border); border-radius: var(--radius-md); background: var(--surface-secondary); box-shadow: 0 1px 0 rgba(255,255,255,.018) inset; transition: border-color var(--transition-fast), box-shadow var(--transition-fast), background var(--transition-fast); }
.field__control:focus-within { border-color: var(--color-border-focus); background: var(--surface-primary); box-shadow: var(--shadow-focus); }
.field__control--error { border-color: var(--color-danger); }
.field__control.is-disabled { opacity: .55; }
.field__control.is-readonly { background: color-mix(in srgb, var(--surface-secondary) 72%, transparent); }
.field__icon { flex: 0 0 auto; color: var(--text-muted); }
input { width: 100%; min-width: 0; height: 2.75rem; padding: 0; border: 0; outline: 0; background: transparent; color: var(--color-text-primary); caret-color: var(--color-primary); }
input::placeholder { color: var(--color-text-muted); opacity: .85; }
.field__suffix { flex: 0 0 auto; color: var(--color-text-secondary); font-size: var(--font-size-sm); }
.field__action { display: grid; flex: 0 0 2.75rem; width: 2.75rem; height: 2.75rem; border: 0; border-radius: var(--radius-sm); background: transparent; color: var(--color-text-muted); place-items: center; }
.field__action:hover { background: var(--color-surface-3); color: var(--color-text-primary); }
.field__action:focus-visible { outline-offset: -2px; }
.field__message { min-height: 1.2em; color: var(--text-muted); font-size: var(--font-size-xs); line-height: 1.55; }
.field__message--error { color: var(--color-danger); }
</style>
