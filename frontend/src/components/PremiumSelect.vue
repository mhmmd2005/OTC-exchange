<script setup>
import {ChevronDown} from 'lucide-vue-next'
import {computed, nextTick, onBeforeUnmount, onMounted, ref, watchEffect} from 'vue'

const model = defineModel()

const props = defineProps({
  options: {type: Array, default: () => []},
  placeholder: {type: String, default: 'انتخاب کنید'},
  label: String,
  disabled: Boolean,
  searchable: Boolean,
  emptyText: {type: String, default: 'گزینه‌ای پیدا نشد'},
})

const rootRef = ref(null)
const triggerRef = ref(null)
const isOpen = ref(false)
const query = ref('')
const activeIndex = ref(0)

const normalizedOptions = computed(() =>
    (props.options || []).map((option, index) => ({
      value: option.value ?? option.id ?? index,
      label: option.label ?? option.name ?? option.value ?? `گزینه ${index + 1}`,
      subtitle: option.subtitle ?? option.meta ?? option.description ?? '',
      icon: option.icon ?? '',
      disabled: Boolean(option.disabled),
    })))


const selectedOption = computed(() =>
    normalizedOptions.value.find((option) => option.value === model.value) || null,
)

const filteredOptions = computed(() => {
  const text = query.value.trim().toLowerCase()
  if (!text) return normalizedOptions.value
  return normalizedOptions.value.filter((option) => {
    const haystack = `${option.label} ${option.subtitle}`.toLowerCase()
    return haystack.includes(text)
  })
})

function closeDropdown() {
  isOpen.value = false
  query.value = ''
}

function toggleDropdown() {
  if (props.disabled) return
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    activeIndex.value = Math.max(
        0,
        normalizedOptions.value.findIndex((option) => option.value === model.value),
    )
  }
}

function selectOption(optionValue) {
  model.value = optionValue
  closeDropdown()
}

function handleDocumentClick(event) {
  if (!rootRef.value) return
  if (!rootRef.value.contains(event.target)) closeDropdown()
}

function moveSelection(step) {
  const options = filteredOptions.value.filter((option) => !option.disabled)
  if (!options.length) return

  const currentIndex = options.findIndex((option) => option.value === model.value)
  const safeIndex = currentIndex >= 0 ? currentIndex : 0
  const nextIndex = (safeIndex + step + options.length) % options.length
  activeIndex.value = normalizedOptions.value.findIndex((option) => option.value === options[nextIndex].value)
}

function handleKeydown(event) {
  if (props.disabled) return

  if (!isOpen.value && ['ArrowDown', 'ArrowUp', 'Enter', ' '].includes(event.key)) {
    event.preventDefault()
    isOpen.value = true
    return
  }

  if (!isOpen.value) return

  if (event.key === 'Escape') {
    event.preventDefault()
    closeDropdown()
    return
  }

  if (event.key === 'ArrowDown') {
    event.preventDefault()
    const options = filteredOptions.value.filter((option) => !option.disabled)
    if (!options.length) return
    const currentValue = options[activeIndex.value % options.length]?.value ?? options[0].value
    const currentPosition = options.findIndex((option) => option.value === currentValue)
    const next = options[(currentPosition + 1) % options.length]
    activeIndex.value = normalizedOptions.value.findIndex((option) => option.value === next.value)
  }

  if (event.key === 'ArrowUp') {
    event.preventDefault()
    const options = filteredOptions.value.filter((option) => !option.disabled)
    if (!options.length) return
    const currentValue = options[activeIndex.value % options.length]?.value ?? options[0].value
    const currentPosition = options.findIndex((option) => option.value === currentValue)
    const prev = options[(currentPosition - 1 + options.length) % options.length]
    activeIndex.value = normalizedOptions.value.findIndex((option) => option.value === prev.value)
  }

  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    const option = filteredOptions.value[activeIndex.value]
    if (option && !option.disabled) selectOption(option.value)
  }
}

onMounted(() => {
  document.addEventListener('click', handleDocumentClick)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleDocumentClick)
})

watchEffect(() => {
  if (isOpen.value) {
    nextTick(() => {
      const idx = Math.max(0, filteredOptions.value.findIndex((option) => option.value === model.value))
      activeIndex.value = idx >= 0 ? idx : 0
    })
  }
})
</script>

<template>
  <div ref="rootRef" class="premium-select-root" @keydown="handleKeydown">
    <button
        ref="triggerRef"
        type="button"
        class="premium-select-trigger"
        :class="{ open: isOpen, disabled: disabled }"
        :disabled="disabled"
        @click="toggleDropdown"
        @keydown="handleKeydown"
    >
      <span v-if="selectedOption" class="premium-select-selected">
        <span v-if="selectedOption.icon" class="premium-select-icon">{{ selectedOption.icon }}</span>
        <span class="premium-select-copy">
          <span class="premium-select-label">{{ selectedOption.label }}</span>
          <span v-if="selectedOption.subtitle" class="premium-select-subtitle">{{ selectedOption.subtitle }}</span>
        </span>
      </span>
      <span v-else class="premium-select-placeholder">{{ placeholder }}</span>
      <ChevronDown class="premium-select-chevron" :size="16"/>
    </button>

    <div v-if="isOpen" class="premium-select-menu" role="listbox" aria-label="انتخاب مقدار">
      <div v-if="searchable" class="premium-select-search">
        <input v-model="query" type="text" placeholder="جستجو..."/>
      </div>

      <div v-if="filteredOptions.length === 0" class="premium-select-empty">
        {{ emptyText }}
      </div>

      <button
          v-for="(option, index) in filteredOptions"
          :key="`${option.value}-${index}`"
          type="button"
          class="premium-select-option"
          :class="{ active: activeIndex === index, selected: model === option.value }"
          @click="selectOption(option.value)"
          @mouseenter="activeIndex = index"
      >
        <span v-if="option.icon" class="premium-select-option-icon">{{ option.icon }}</span>
        <span class="premium-select-option-copy">
          <span class="premium-select-option-label">{{ option.label }}</span>
          <span v-if="option.subtitle" class="premium-select-option-subtitle">{{ option.subtitle }}</span>
        </span>
        <span v-if="model === option.value" class="premium-select-check">✓</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.premium-select-root {
  position: relative;
  width: 100%;
  direction: rtl;
}

.premium-select-trigger {
  width: 100%;
  height: 48px;
  padding: 0 14px 0 12px;
  background: var(--surface-input);
  border: 1px solid var(--border-default);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  color: var(--text-primary);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.02);
  transition: border-color 0.2s ease, box-shadow 0.2s ease, background-color 0.2s ease;
}

.premium-select-trigger:hover {
  border-color: var(--border-strong);
}

.premium-select-trigger:focus,
.premium-select-trigger.open {
  outline: none;
  border-color: var(--gold);
  box-shadow: 0 0 0 4px var(--focus-ring);
}

.premium-select-trigger.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.premium-select-selected,
.premium-select-placeholder {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  flex: 1;
}

.premium-select-placeholder {
  color: var(--text-secondary);
}

.premium-select-copy,
.premium-select-option-copy {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.premium-select-label,
.premium-select-option-label {
  font-weight: 700;
  color: var(--text-primary);
}

.premium-select-subtitle,
.premium-select-option-subtitle {
  color: var(--text-secondary);
  font-size: 0.74rem;
}

.premium-select-icon,
.premium-select-option-icon {
  width: 26px;
  height: 26px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.7rem;
  font-weight: 800;
  background: rgba(212, 169, 90, 0.12);
  color: var(--gold);
}

.premium-select-chevron {
  color: var(--text-secondary);
  transition: transform 0.2s ease;
}

.premium-select-trigger.open .premium-select-chevron {
  transform: rotate(180deg);
}

.premium-select-menu {
  position: absolute;
  z-index: var(--z-dropdown);
  top: calc(100% + 10px);
  left: 0;
  right: 0;
  background: var(--surface-dropdown);
  border: 1px solid var(--border-default);
  border-radius: 16px;
  box-shadow: var(--shadow-dropdown);
  backdrop-filter: blur(18px);
  overflow: hidden;
  animation: selectFade 0.18s ease;
}

.premium-select-search {
  padding: 10px 10px 8px;
  border-bottom: 1px solid var(--border-subtle);
}

.premium-select-search input {
  width: 100%;
  height: 38px;
  border: 1px solid var(--border-default);
  border-radius: 10px;
  background: var(--surface-input);
  color: var(--text-primary);
  padding: 0 12px;
  outline: none;
}

.premium-select-search input:focus {
  border-color: var(--gold);
  box-shadow: 0 0 0 3px var(--focus-ring);
}

.premium-select-empty {
  padding: 18px 14px;
  color: var(--text-secondary);
  text-align: center;
}

.premium-select-option {
  width: 100%;
  border: 0;
  background: transparent;
  padding: 10px 12px;
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--text-primary);
  text-align: right;
  cursor: pointer;
  transition: background-color 0.18s ease, color 0.18s ease;
}

.premium-select-option:hover,
.premium-select-option.active {
  background: rgba(212, 169, 90, 0.06);
}

.premium-select-option.selected {
  background: rgba(212, 169, 90, 0.1);
}

.premium-select-option-copy {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.premium-select-check {
  color: var(--gold);
  font-weight: 800;
}

@keyframes selectFade {
  from {
    opacity: 0;
    transform: translateY(-6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
