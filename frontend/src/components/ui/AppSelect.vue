<script lang="ts">
export interface AppSelectOption {
  value: string
  label: string
  description?: string
  keywords?: string
  disabled?: boolean
  raw?: unknown
}
</script>

<script setup lang="ts">
import {
  Comment,
  Fragment,
  Text,
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
  useId,
  useSlots,
  watch,
} from 'vue'
import type { CSSProperties, VNode } from 'vue'
import AppIcon from './AppIcon.vue'

const props = withDefaults(defineProps<{
  modelValue?: string
  options?: AppSelectOption[]
  label?: string
  ariaLabel?: string
  hint?: string
  error?: string
  loadError?: string
  disabled?: boolean
  required?: boolean
  name?: string
  placeholder?: string
  searchable?: boolean
  searchPlaceholder?: string
  loading?: boolean
  emptyText?: string
}>(), {
  modelValue: '',
  options: () => [],
  disabled: false,
  required: false,
  placeholder: 'انتخاب کنید',
  searchable: false,
  searchPlaceholder: 'جست‌وجو…',
  loading: false,
  emptyText: 'گزینه‌ای پیدا نشد.',
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  change: [value: string]
  retry: []
  open: []
  close: []
}>()

const slots = useSlots()
const uid = useId().replace(/:/g, '')
const controlId = `select-${uid}`
const listboxId = `${controlId}-listbox`
const messageId = `${controlId}-message`
const trigger = ref<HTMLButtonElement | null>(null)
const panel = ref<HTMLElement | null>(null)
const searchInput = ref<HTMLInputElement | null>(null)
const listbox = ref<HTMLElement | null>(null)
const retryButton = ref<HTMLButtonElement | null>(null)
const open = ref(false)
const search = ref('')
const activeIndex = ref(-1)
const mobile = ref(false)
const panelStyle = ref<CSSProperties>({})
let mediaQuery: MediaQueryList | undefined
let bodyOverflowBeforeSelect = ''
let scrollLocked = false
const inertedBackground: Array<{ element: HTMLElement; inert: boolean }> = []

function nodeText(children: unknown): string {
  if (typeof children === 'string' || typeof children === 'number') return String(children)
  if (Array.isArray(children)) return children.map(nodeText).join('')
  if (children && typeof children === 'object' && 'children' in children) {
    return nodeText((children as VNode).children)
  }
  return ''
}

function collectLegacyOptions(nodes: VNode[], result: AppSelectOption[] = []): AppSelectOption[] {
  for (const node of nodes) {
    if (node.type === Comment || node.type === Text) continue
    if (node.type === Fragment && Array.isArray(node.children)) {
      collectLegacyOptions(node.children as VNode[], result)
      continue
    }
    if (typeof node.type === 'string' && node.type.toLowerCase() === 'option') {
      const value = String(node.props?.value ?? '')
      result.push({
        value,
        label: nodeText(node.children).trim() || value,
        disabled: Boolean(node.props?.disabled),
      })
    }
  }
  return result
}

const normalizedOptions = computed(() => {
  if (props.options.length) return props.options
  return collectLegacyOptions(slots.default?.() || [])
})

const normalizeSearch = (value: string) => value
  .trim()
  .toLocaleLowerCase('fa-IR')
  .replace(/ي/g, 'ی')
  .replace(/ك/g, 'ک')

const filteredOptions = computed(() => {
  const query = normalizeSearch(search.value)
  if (!query) return normalizedOptions.value
  return normalizedOptions.value.filter((option) => normalizeSearch([
    option.label,
    option.description,
    option.keywords,
    option.value,
  ].filter(Boolean).join(' ')).includes(query))
})

const selectedOption = computed(() => normalizedOptions.value.find((option) => option.value === props.modelValue))
const accessibleName = computed(() => props.ariaLabel || props.label || 'انتخاب گزینه')
const optionsUnavailable = computed(() => props.loading || Boolean(props.loadError))
const hasSelectableOptions = computed(() => !optionsUnavailable.value && filteredOptions.value.some((option) => !option.disabled))
const activeOptionId = computed(() => (
  open.value
  && hasSelectableOptions.value
  && activeIndex.value >= 0
  && filteredOptions.value[activeIndex.value]
  && !filteredOptions.value[activeIndex.value]?.disabled
    ? `${controlId}-option-${activeIndex.value}`
    : undefined
))

function firstEnabledIndex(options = filteredOptions.value): number {
  return options.findIndex((option) => !option.disabled)
}

function lastEnabledIndex(options = filteredOptions.value): number {
  for (let index = options.length - 1; index >= 0; index -= 1) {
    if (!options[index]?.disabled) return index
  }
  return -1
}

function selectedIndex(options = filteredOptions.value): number {
  return options.findIndex((option) => option.value === props.modelValue && !option.disabled)
}

function setMobileState(): void {
  mobile.value = mediaQuery?.matches ?? window.innerWidth <= 767
}

function syncScrollLock(): void {
  const shouldLock = open.value && mobile.value
  if (shouldLock && !scrollLocked) {
    bodyOverflowBeforeSelect = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    scrollLocked = true
  } else if (!shouldLock && scrollLocked) {
    document.body.style.overflow = bodyOverflowBeforeSelect
    bodyOverflowBeforeSelect = ''
    scrollLocked = false
  }
}

function restoreBackgroundInert(): void {
  while (inertedBackground.length) {
    const entry = inertedBackground.pop()
    if (entry) entry.element.inert = entry.inert
  }
}

function syncBackgroundInert(): void {
  restoreBackgroundInert()
  if (!open.value || !mobile.value || !panel.value) return
  const layer = panel.value.closest<HTMLElement>('.select-popover-layer')
  if (!layer) return
  for (const child of [...document.body.children]) {
    if (!(child instanceof HTMLElement) || child === layer || child.contains(layer)) continue
    inertedBackground.push({ element: child, inert: child.inert })
    child.inert = true
  }
}

function updatePosition(): void {
  if (!open.value || !trigger.value) {
    panelStyle.value = {}
    return
  }
  if (mobile.value) {
    const viewport = window.visualViewport
    const offsetLeft = viewport?.offsetLeft || 0
    const offsetTop = viewport?.offsetTop || 0
    const viewportWidth = viewport?.width || document.documentElement.clientWidth
    const viewportHeight = viewport?.height || window.innerHeight
    const bottom = Math.max(0, window.innerHeight - offsetTop - viewportHeight)
    panelStyle.value = {
      right: 'auto',
      bottom: `${bottom}px`,
      left: `${offsetLeft}px`,
      width: `${viewportWidth}px`,
      maxHeight: `${Math.max(0, Math.min(640, viewportHeight * .78, viewportHeight - 16))}px`,
    }
    return
  }
  const rect = trigger.value.getBoundingClientRect()
  const edge = 12
  const gap = 8
  const viewportWidth = document.documentElement.clientWidth
  const viewportHeight = window.visualViewport?.height || window.innerHeight
  if (rect.bottom < edge || rect.top > viewportHeight - edge) {
    closeSelect(false)
    return
  }
  const width = Math.min(Math.max(rect.width, 260), viewportWidth - edge * 2)
  const left = Math.min(Math.max(edge, rect.right - width), viewportWidth - edge - width)
  const availableBelow = viewportHeight - rect.bottom - gap - edge
  const availableAbove = rect.top - gap - edge
  const contentHeight = Math.min(360, panel.value?.scrollHeight || 360)
  const placeAbove = availableBelow < Math.min(190, contentHeight) && availableAbove > availableBelow
  const maxHeight = Math.max(0, Math.min(contentHeight, placeAbove ? availableAbove : availableBelow))
  const top = placeAbove ? Math.max(edge, rect.top - gap - maxHeight) : rect.bottom + gap
  panelStyle.value = {
    top: `${Math.round(top)}px`,
    left: `${Math.round(left)}px`,
    width: `${Math.round(width)}px`,
    maxHeight: `${Math.round(maxHeight)}px`,
  }
}

function scrollActiveIntoView(): void {
  void nextTick(() => {
    panel.value
      ?.querySelector<HTMLElement>(`[data-option-index="${activeIndex.value}"]`)
      ?.scrollIntoView({ block: 'nearest' })
  })
}

function moveActive(step: 1 | -1): void {
  if (!hasSelectableOptions.value) return
  const options = filteredOptions.value
  if (!options.length) return
  let index = activeIndex.value
  for (let attempts = 0; attempts < options.length; attempts += 1) {
    index = (index + step + options.length) % options.length
    if (!options[index]?.disabled) {
      activeIndex.value = index
      scrollActiveIntoView()
      return
    }
  }
}

function closeSelect(restoreFocus = true): void {
  if (!open.value) return
  open.value = false
  search.value = ''
  activeIndex.value = -1
  syncScrollLock()
  restoreBackgroundInert()
  emit('close')
  if (restoreFocus) void nextTick(() => trigger.value?.focus({ preventScroll: true }))
}

async function openSelect(preferred: 'selected' | 'first' | 'last' = 'selected'): Promise<void> {
  if (props.disabled || open.value) return
  open.value = true
  syncScrollLock()
  search.value = ''
  const preferredIndex = preferred === 'last'
    ? lastEnabledIndex()
    : preferred === 'first'
      ? firstEnabledIndex()
      : selectedIndex()
  activeIndex.value = preferredIndex >= 0 ? preferredIndex : firstEnabledIndex()
  emit('open')
  await nextTick()
  updatePosition()
  syncBackgroundInert()
  if (props.loadError) retryButton.value?.focus({ preventScroll: true })
  else if (props.loading) listbox.value?.focus({ preventScroll: true })
  else if (props.searchable) searchInput.value?.focus({ preventScroll: true })
  else if (mobile.value) listbox.value?.focus({ preventScroll: true })
  scrollActiveIntoView()
}

function selectOption(option: AppSelectOption): void {
  if (optionsUnavailable.value || option.disabled) return
  if (option.value !== props.modelValue) {
    emit('update:modelValue', option.value)
    emit('change', option.value)
  }
  closeSelect()
}

function selectActive(): void {
  if (!hasSelectableOptions.value) return
  const option = filteredOptions.value[activeIndex.value]
  if (option && !option.disabled) selectOption(option)
}

function onTriggerKeydown(event: KeyboardEvent): void {
  if (props.disabled) return
  if (event.key === 'Escape' && open.value) {
    event.preventDefault()
    closeSelect()
    return
  }
  if (event.key === 'Tab' && open.value) {
    closeSelect(false)
    return
  }
  if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
    event.preventDefault()
    if (!open.value) void openSelect(event.key === 'ArrowDown' ? 'first' : 'last')
    else moveActive(event.key === 'ArrowDown' ? 1 : -1)
    return
  }
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    if (open.value) selectActive()
    else void openSelect()
  }
}

function focusablePanelControls(): HTMLElement[] {
  if (!panel.value) return []
  return [...panel.value.querySelectorAll<HTMLElement>('button:not([disabled]), input:not([disabled]), [tabindex]:not([tabindex="-1"])')]
    .filter((item) => item.offsetParent !== null)
}

function focusRelativeToTrigger(backwards: boolean): void {
  const currentTrigger = trigger.value
  if (!currentTrigger) return
  const controls = [...document.querySelectorAll<HTMLElement>('a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])')]
    .filter((item) => !item.closest('.select-popover') && item.offsetParent !== null)
  const index = controls.indexOf(currentTrigger)
  if (index < 0) return
  controls[index + (backwards ? -1 : 1)]?.focus({ preventScroll: true })
}

function onPanelKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape') {
    event.preventDefault()
    event.stopPropagation()
    closeSelect()
    return
  }
  if (event.key === 'Tab') {
    if (!mobile.value) {
      event.preventDefault()
      closeSelect(false)
      void nextTick(() => focusRelativeToTrigger(event.shiftKey))
      return
    }
    const controls = focusablePanelControls()
    if (!controls.length) {
      event.preventDefault()
      panel.value?.focus()
      return
    }
    const first = controls[0]!
    const last = controls[controls.length - 1]!
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault()
      last.focus()
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault()
      first.focus()
    }
    return
  }
  if (event.target instanceof HTMLElement && event.target.closest('button')) return
  if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
    event.preventDefault()
    moveActive(event.key === 'ArrowDown' ? 1 : -1)
    return
  }
  if (event.key === 'Enter' && !optionsUnavailable.value && activeIndex.value >= 0) {
    event.preventDefault()
    selectActive()
  }
}

function onDocumentKeydown(event: KeyboardEvent): void {
  if (!open.value || event.key !== 'Escape') return
  event.preventDefault()
  event.stopPropagation()
  closeSelect()
}

function onDocumentPointerDown(event: PointerEvent): void {
  const target = event.target as Node
  if (trigger.value?.contains(target) || panel.value?.contains(target)) return
  // The mobile backdrop closes on its click handler after the complete pointer
  // sequence. Closing it here would expose the page before pointerup/click and
  // could both steal focus from the trigger and click through to the page.
  if (target instanceof Element && target.closest('.select-popover-layer')) return
  closeSelect(false)
}

function onViewportChange(): void {
  setMobileState()
  syncScrollLock()
  updatePosition()
  void nextTick(syncBackgroundInert)
}

watch(search, () => {
  activeIndex.value = selectedIndex()
  if (activeIndex.value < 0) activeIndex.value = firstEnabledIndex()
  scrollActiveIntoView()
})

watch(() => props.modelValue, () => {
  if (!open.value) return
  activeIndex.value = selectedIndex()
})

watch([filteredOptions, optionsUnavailable], () => {
  if (!open.value || optionsUnavailable.value) {
    activeIndex.value = -1
    return
  }
  activeIndex.value = selectedIndex()
  if (activeIndex.value < 0) activeIndex.value = firstEnabledIndex()
  scrollActiveIntoView()
})

watch(() => props.loadError, async (loadError) => {
  if (!open.value || !loadError) return
  activeIndex.value = -1
  await nextTick()
  retryButton.value?.focus({ preventScroll: true })
})

watch(() => props.disabled, (disabled) => {
  if (disabled) closeSelect(false)
})

onMounted(() => {
  mediaQuery = window.matchMedia('(max-width: 767px)')
  setMobileState()
  mediaQuery.addEventListener('change', onViewportChange)
  document.addEventListener('pointerdown', onDocumentPointerDown, true)
  document.addEventListener('keydown', onDocumentKeydown, true)
  window.addEventListener('resize', onViewportChange)
  window.addEventListener('scroll', updatePosition, true)
  window.visualViewport?.addEventListener('resize', onViewportChange)
  window.visualViewport?.addEventListener('scroll', updatePosition)
})

onBeforeUnmount(() => {
  mediaQuery?.removeEventListener('change', onViewportChange)
  document.removeEventListener('pointerdown', onDocumentPointerDown, true)
  document.removeEventListener('keydown', onDocumentKeydown, true)
  window.removeEventListener('resize', onViewportChange)
  window.removeEventListener('scroll', updatePosition, true)
  window.visualViewport?.removeEventListener('resize', onViewportChange)
  window.visualViewport?.removeEventListener('scroll', updatePosition)
  if (scrollLocked) {
    document.body.style.overflow = bodyOverflowBeforeSelect
    scrollLocked = false
  }
  restoreBackgroundInert()
})
</script>

<template>
  <div class="select-field" :class="{ 'is-open': open, 'is-disabled': disabled }">
    <label v-if="label" class="select-field__label" :for="controlId">
      {{ label }}<i v-if="required" aria-hidden="true">*</i>
    </label>
    <button
      :id="controlId"
      ref="trigger"
      type="button"
      class="select-field__control"
      :class="{ 'has-error': error }"
      :role="searchable || (open && mobile) ? undefined : 'combobox'"
      aria-haspopup="listbox"
      :aria-label="accessibleName"
      :aria-expanded="open"
      :aria-controls="open ? listboxId : undefined"
      :aria-activedescendant="!searchable && !(open && mobile) ? activeOptionId : undefined"
      :aria-invalid="!!error"
      :aria-required="required || undefined"
      :aria-describedby="error || hint ? messageId : undefined"
      :disabled="disabled"
      @click="open ? closeSelect() : openSelect()"
      @keydown="onTriggerKeydown"
    >
      <span v-if="selectedOption" class="select-field__value">
        <slot name="selected" :option="selectedOption">
          <span class="select-field__value-label">{{ selectedOption.label }}</span>
        </slot>
      </span>
      <span v-else class="select-field__placeholder">{{ placeholder }}</span>
      <AppIcon class="select-field__chevron" :name="open ? 'chevronUp' : 'chevronDown'" :size="18" aria-hidden="true" />
    </button>
    <input v-if="name" type="hidden" :name="name" :value="modelValue" />
    <span v-if="error || hint" :id="messageId" class="select-field__message" :class="{ error: error }">{{ error || hint }}</span>
  </div>

  <Teleport to="body">
    <Transition name="select-popover">
      <div v-if="open" class="select-popover-layer" :class="{ 'is-mobile': mobile }" @click.self="closeSelect()">
        <section
          ref="panel"
          class="select-popover"
          :class="{ 'is-mobile': mobile }"
          :style="panelStyle"
          :aria-label="mobile ? accessibleName : undefined"
          :role="mobile ? 'dialog' : 'presentation'"
          :aria-modal="mobile || undefined"
          tabindex="-1"
          dir="rtl"
          @keydown="onPanelKeydown"
        >
          <div v-if="mobile" class="select-popover__mobile-header">
            <span class="select-popover__handle" aria-hidden="true" />
            <strong>{{ accessibleName }}</strong>
            <button type="button" aria-label="بستن فهرست" @click="closeSelect()"><AppIcon name="close" :size="19" /></button>
          </div>

          <label v-if="searchable" class="select-popover__search">
            <AppIcon name="search" :size="18" aria-hidden="true" />
            <input
              ref="searchInput"
              v-model="search"
              type="search"
              inputmode="search"
              autocomplete="off"
              :placeholder="searchPlaceholder"
              :aria-label="searchPlaceholder"
              role="combobox"
              aria-autocomplete="list"
              aria-expanded="true"
              aria-haspopup="listbox"
              :aria-controls="listboxId"
              :aria-activedescendant="activeOptionId"
            />
          </label>

          <div
            :id="listboxId"
            ref="listbox"
            class="select-popover__list"
            role="listbox"
            :aria-label="accessibleName"
            :aria-busy="loading || undefined"
            :aria-activedescendant="activeOptionId"
            :tabindex="mobile || !searchable ? 0 : -1"
          >
            <div v-if="loading" class="select-popover__state" role="status">
              <span class="select-popover__spinner" aria-hidden="true" />
              <span>در حال دریافت گزینه‌ها…</span>
            </div>
            <div v-else-if="loadError" class="select-popover__state is-error" role="alert">
              <AppIcon name="warning" :size="21" />
              <span>{{ loadError }}</span>
              <button ref="retryButton" type="button" @click="$emit('retry')">تلاش دوباره</button>
            </div>
            <div v-else-if="!filteredOptions.length" class="select-popover__state" role="status">
              <AppIcon name="search" :size="21" />
              <span>{{ emptyText }}</span>
              <slot name="empty" />
            </div>
            <div
              v-for="(option, index) in filteredOptions"
              v-else
              :id="`${controlId}-option-${index}`"
              :key="option.value"
              class="select-option"
              :class="{ 'is-active': activeIndex === index, 'is-selected': option.value === modelValue, 'is-disabled': option.disabled }"
              role="option"
              :aria-selected="option.value === modelValue"
              :aria-disabled="option.disabled || undefined"
              :data-option-index="index"
              @pointermove="!option.disabled && (activeIndex = index)"
              @click="selectOption(option)"
            >
              <span class="select-option__content">
                <slot name="option" :option="option" :selected="option.value === modelValue" :active="activeIndex === index">
                  <strong>{{ option.label }}</strong>
                  <small v-if="option.description">{{ option.description }}</small>
                </slot>
              </span>
              <AppIcon v-if="option.value === modelValue" class="select-option__check" name="check" :size="18" aria-hidden="true" />
            </div>
          </div>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.select-field { display: grid; min-width: 0; gap: .45rem; }
.select-field__label { color: var(--text-secondary); font-size: var(--font-size-sm); font-weight: 500; }
.select-field__label i { margin-inline-start: .25rem; color: var(--color-danger); font-style: normal; }
.select-field__control {
  display: flex;
  width: 100%;
  min-width: 0;
  min-height: var(--control-height);
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  background: var(--surface-secondary);
  color: var(--text-primary);
  box-shadow: 0 1px 0 rgba(255, 255, 255, .018) inset;
  text-align: start;
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast), background var(--transition-fast);
}
.select-field__control:hover:not(:disabled) { border-color: var(--color-border-hover); background: var(--surface-tertiary); }
.select-field__control:focus-visible,
.select-field.is-open .select-field__control { border-color: var(--color-border-focus); outline: 0; background: var(--surface-primary); box-shadow: var(--shadow-focus); }
.select-field__control.has-error { border-color: var(--color-danger); }
.select-field__control:disabled { cursor: not-allowed; opacity: .55; }
.select-field__value { display: block; min-width: 0; flex: 1; }
.select-field__value-label { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.select-field__placeholder { min-width: 0; flex: 1; overflow: hidden; color: var(--text-muted); text-overflow: ellipsis; white-space: nowrap; }
.select-field__chevron { flex: 0 0 auto; color: var(--color-text-muted); transition: color var(--transition-fast); }
.select-field.is-open .select-field__chevron { color: var(--color-primary); }
.select-field__message { min-height: 1.2em; color: var(--text-muted); font-size: var(--font-size-xs); line-height: 1.55; overflow-wrap: anywhere; }
.select-field__message.error { color: var(--color-danger); }

.select-popover-layer { position: fixed; z-index: calc(var(--z-modal) + 2); inset: 0; pointer-events: none; }
.select-popover-layer.is-mobile { padding-top: var(--safe-top); background: rgba(1, 7, 14, .66); pointer-events: auto; backdrop-filter: blur(5px); }
.select-popover {
  position: fixed;
  display: flex;
  overflow: hidden;
  flex-direction: column;
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-lg);
  background: var(--surface-overlay);
  box-shadow: var(--shadow-md);
  color: var(--text-primary);
  pointer-events: auto;
}
.select-popover.is-mobile { inset: auto 0 0; width: 100%; max-height: min(78dvh, 40rem); padding-right: var(--safe-right); padding-bottom: var(--safe-bottom); padding-left: var(--safe-left); border-width: 1px 0 0; border-radius: var(--radius-xl) var(--radius-xl) 0 0; }
.select-popover__mobile-header { position: relative; display: grid; grid-template-columns: 2.75rem 1fr 2.75rem; align-items: center; min-height: 4.25rem; padding: var(--space-3) var(--space-4); border-block-end: 1px solid var(--color-border-soft); text-align: center; }
.select-popover__mobile-header strong { grid-column: 2; min-width: 0; overflow-wrap: anywhere; }
.select-popover__mobile-header button { grid-column: 3; display: grid; width: 2.75rem; height: 2.75rem; border: 1px solid var(--control-border); border-radius: var(--radius-sm); background: var(--surface-secondary); color: var(--text-secondary); place-items: center; }
.select-popover__handle { position: absolute; inset-block-start: .45rem; inset-inline-start: 50%; width: 2.6rem; height: .23rem; border-radius: var(--radius-pill); background: var(--color-border-hover); transform: translateX(-50%); }
.select-popover__search { display: flex; min-height: 2.85rem; align-items: center; gap: var(--space-2); margin: var(--space-3); padding-inline: var(--space-3); border: 1px solid var(--control-border); border-radius: var(--radius-md); background: var(--surface-secondary); color: var(--text-muted); }
.select-popover__search:focus-within { border-color: var(--color-border-focus); box-shadow: var(--shadow-focus); }
.select-popover__search input { width: 100%; min-width: 0; border: 0; outline: 0; background: transparent; color: var(--text-primary); }
.select-popover__search input::placeholder { color: var(--text-muted); }
.select-popover__list { min-height: 0; overflow: auto; padding: var(--space-2); overscroll-behavior: contain; scrollbar-gutter: stable; }
.select-option { display: flex; min-height: 3rem; align-items: center; gap: var(--space-3); padding: var(--space-2) var(--space-3); border: 1px solid transparent; border-radius: var(--radius-md); color: var(--text-secondary); cursor: pointer; transition: border-color var(--transition-fast), background var(--transition-fast), color var(--transition-fast); }
.select-option.is-active { border-color: var(--color-primary-border); background: var(--color-primary-soft); color: var(--text-primary); }
.select-option.is-selected { color: var(--color-primary); }
.select-option.is-disabled { cursor: not-allowed; opacity: .48; }
.select-option__content { display: grid; min-width: 0; flex: 1; gap: .1rem; overflow-wrap: anywhere; }
.select-option__content strong { font-size: var(--font-size-sm); font-weight: 600; }
.select-option__content small { color: var(--text-muted); font-size: var(--font-size-xs); }
.select-option__check { flex: 0 0 auto; color: var(--color-primary); }
.select-popover__state { display: grid; min-height: 8rem; align-content: center; justify-items: center; gap: var(--space-2); padding: var(--space-5); color: var(--text-muted); font-size: var(--font-size-sm); text-align: center; }
.select-popover__state.is-error { color: var(--color-danger); }
.select-popover__state button { min-height: 2.5rem; padding-inline: var(--space-4); border: 1px solid currentColor; border-radius: var(--radius-sm); color: currentColor; }
.select-popover__spinner { width: 1.4rem; height: 1.4rem; border: 2px solid var(--color-primary-soft); border-block-start-color: var(--color-primary); border-radius: 50%; animation: select-spin .72s linear infinite; }
.select-popover-enter-active,
.select-popover-leave-active { transition: opacity var(--transition-fast); }
.select-popover-enter-active .select-popover,
.select-popover-leave-active .select-popover { transition: opacity var(--transition-fast), transform var(--transition-fast); }
.select-popover-enter-from,
.select-popover-leave-to { opacity: 0; }
.select-popover-enter-from .select-popover,
.select-popover-leave-to .select-popover { opacity: 0; transform: translateY(-.35rem) scale(.985); }
@keyframes select-spin { to { transform: rotate(360deg); } }

@media (max-width: 767px) {
  .select-field__control { min-height: 3.25rem; }
  .select-popover__list { padding-bottom: var(--space-4); }
  .select-option { min-height: 3.5rem; padding: var(--space-3); }
  .select-popover-enter-from .select-popover,
  .select-popover-leave-to .select-popover { transform: translateY(100%); }
}

@media (prefers-reduced-motion: reduce) {
  .select-popover-enter-active,
  .select-popover-leave-active,
  .select-popover-enter-active .select-popover,
  .select-popover-leave-active .select-popover,
  .select-field__chevron { transition-duration: .01ms; }
}
</style>
