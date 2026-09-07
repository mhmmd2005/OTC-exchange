<script lang="ts">
let openModalCount = 0
let originalBodyOverflow = ''
let originalAppInert = false
let inertRoot: HTMLElement | null = null

function lockModalLayer(): void {
  if (openModalCount === 0) {
    originalBodyOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    inertRoot = document.getElementById('app')
    if (inertRoot) {
      originalAppInert = inertRoot.inert
      inertRoot.inert = true
    }
  }
  openModalCount += 1
}

function unlockModalLayer(): void {
  openModalCount = Math.max(0, openModalCount - 1)
  if (openModalCount === 0) {
    document.body.style.overflow = originalBodyOverflow
    if (inertRoot) inertRoot.inert = originalAppInert
    inertRoot = null
  }
}
</script>

<script setup lang="ts">
import { nextTick, onBeforeUnmount, ref, useId, watch } from 'vue'
import AppIcon from './AppIcon.vue'

const props = withDefaults(defineProps<{ modelValue: boolean; title?: string; description?: string; size?: 'sm' | 'md' | 'lg'; dismissible?: boolean }>(), { size: 'md', dismissible: true })
const emit = defineEmits<{ 'update:modelValue': [value: boolean] }>()

const panel = ref<HTMLElement | null>(null)
const titleId = `modal-title-${useId()}`
const descriptionId = `${titleId}-description`
let returnFocus: HTMLElement | null = null
let pendingReturnFocus: HTMLElement | null = null
let locallyOpen = false
let watchVersion = 0
const close = () => { if (props.dismissible) emit('update:modelValue', false) }
const onKeydown = (event: KeyboardEvent) => {
  if (event.target instanceof Element && event.target.closest('.select-popover-layer')) return
  const activePanel = panel.value
  const panels = document.querySelectorAll<HTMLElement>('[data-modal-panel]')
  if (!activePanel || panels[panels.length - 1] !== activePanel) return
  if (event.key === 'Escape') {
    event.preventDefault()
    close()
    return
  }
  if (event.key !== 'Tab') return
  const controls = [...activePanel.querySelectorAll<HTMLElement>('a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])')]
    .filter((item) => item.offsetParent !== null)
  if (!controls.length) {
    event.preventDefault()
    activePanel.focus()
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
}

watch(() => props.modelValue, async (open) => {
  const version = ++watchVersion
  if (open) {
    if (!locallyOpen) {
      returnFocus = pendingReturnFocus || (document.activeElement instanceof HTMLElement ? document.activeElement : null)
      pendingReturnFocus = null
      locallyOpen = true
      lockModalLayer()
    }
    document.addEventListener('keydown', onKeydown)
    await nextTick()
    if (version !== watchVersion || !locallyOpen || !props.modelValue) return
    const firstControl = panel.value?.querySelector<HTMLElement>('input:not([disabled]), select:not([disabled]), textarea:not([disabled]), button:not([disabled]), a[href]')
    ;(firstControl || panel.value)?.focus()
  } else {
    document.removeEventListener('keydown', onKeydown)
    if (locallyOpen) {
      locallyOpen = false
      unlockModalLayer()
    }
    pendingReturnFocus = returnFocus
    returnFocus = null
    await nextTick()
    if (version !== watchVersion) return
    if (pendingReturnFocus?.isConnected) pendingReturnFocus.focus({ preventScroll: true })
    pendingReturnFocus = null
  }
}, { immediate: true })

onBeforeUnmount(() => {
  watchVersion += 1
  document.removeEventListener('keydown', onKeydown)
  if (locallyOpen) {
    locallyOpen = false
    unlockModalLayer()
  }
  const focusTarget = returnFocus || pendingReturnFocus
  returnFocus = null
  pendingReturnFocus = null
  if (focusTarget?.isConnected) focusTarget.focus({ preventScroll: true })
})
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="modelValue" data-modal-layer class="modal-layer" role="presentation" @mousedown.self="close">
        <section
          ref="panel"
          data-modal-panel
          class="modal-panel"
          :class="`modal-panel--${size}`"
          role="dialog"
          aria-modal="true"
          :aria-label="title ? undefined : 'گفت‌وگو'"
          :aria-labelledby="title ? titleId : undefined"
          :aria-describedby="description ? descriptionId : undefined"
          tabindex="-1"
        >
          <div class="sheet-handle mobile-only" aria-hidden="true" />
          <header v-if="title || description || dismissible" class="modal-header">
            <div>
              <h2 v-if="title" :id="titleId">{{ title }}</h2>
              <p v-if="description" :id="descriptionId">{{ description }}</p>
            </div>
            <button v-if="dismissible" type="button" aria-label="بستن" @click="close"><AppIcon name="close" :size="20" /></button>
          </header>
          <div class="modal-body"><slot /></div>
          <footer v-if="$slots.footer" class="modal-footer"><slot name="footer" /></footer>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-layer { position: fixed; z-index: var(--z-modal); inset: 0; display: grid; align-items: center; justify-items: center; padding-top: calc(var(--space-5) + var(--safe-top)); padding-right: calc(var(--space-5) + var(--safe-right)); padding-bottom: calc(var(--space-5) + var(--safe-bottom)); padding-left: calc(var(--space-5) + var(--safe-left)); background: rgba(1, 7, 14, .72); backdrop-filter: blur(7px); }
.modal-panel { width: min(100%, 34rem); max-height: min(90dvh, 50rem); overflow: auto; border: 1px solid var(--color-border); border-radius: var(--radius-xl); background: var(--color-surface-1); box-shadow: var(--shadow-md); }
.modal-panel--sm { width: min(100%, 27rem); }
.modal-panel--lg { width: min(100%, 46rem); }
.modal-header { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-4); padding: var(--space-5) var(--space-6); border-block-end: 1px solid var(--color-border-soft); }
.modal-header h2 { margin: 0; font-size: var(--font-size-xl); }
.modal-header p { margin: var(--space-1) 0 0; color: var(--color-text-muted); font-size: var(--font-size-sm); }
.modal-header button { display: grid; width: 2.5rem; height: 2.5rem; flex: 0 0 auto; border: 1px solid var(--control-border); border-radius: var(--radius-sm); background: var(--color-surface-2); color: var(--color-text-secondary); place-items: center; }
.modal-body { padding: var(--space-6); }
.modal-footer { display: flex; gap: var(--space-3); padding: 0 var(--space-6) var(--space-6); }
.modal-enter-active, .modal-leave-active { transition: opacity var(--transition-base); }
.modal-enter-active .modal-panel, .modal-leave-active .modal-panel { transition: transform var(--transition-base), opacity var(--transition-base); }
.modal-enter-from, .modal-leave-to { opacity: 0; }
.modal-enter-from .modal-panel, .modal-leave-to .modal-panel { opacity: 0; transform: translateY(1rem) scale(.98); }
.sheet-handle { width: 2.5rem; height: .25rem; margin: .6rem auto 0; border-radius: var(--radius-pill); background: var(--color-border-hover); }
@media (max-width: 767px) {
  .modal-layer { align-items: end; padding: 0; }
  .modal-panel { width: 100% !important; max-height: 92dvh; padding-bottom: var(--safe-bottom); border-width: 1px 0 0; border-radius: var(--radius-xl) var(--radius-xl) 0 0; }
  .modal-header { padding-block: var(--space-4); padding-right: calc(var(--space-4) + var(--safe-right)); padding-left: calc(var(--space-4) + var(--safe-left)); }
  .modal-body { padding-block: var(--space-4); padding-right: calc(var(--space-4) + var(--safe-right)); padding-left: calc(var(--space-4) + var(--safe-left)); }
  .modal-footer { position: sticky; bottom: 0; padding-block: var(--space-3) var(--space-4); padding-right: calc(var(--space-4) + var(--safe-right)); padding-left: calc(var(--space-4) + var(--safe-left)); background: linear-gradient(transparent, var(--color-surface-1) 22%); }
  .modal-enter-from .modal-panel, .modal-leave-to .modal-panel { transform: translateY(100%); }
}
</style>
