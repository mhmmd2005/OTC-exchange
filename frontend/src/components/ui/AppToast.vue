<script setup lang="ts">
import {onBeforeUnmount, onMounted, ref} from 'vue'
import AppIcon from '@/components/ui/AppIcon.vue'

const visible = ref(false)
const message = ref('')

let timeoutId: ReturnType<typeof setTimeout> | null = null

function showToast(text: string): void {
  message.value = text
  visible.value = true

  if (timeoutId) {
    clearTimeout(timeoutId)
  }

  timeoutId = setTimeout(() => {
    visible.value = false
    timeoutId = null
  }, 3000)
}

function hideToast(): void {
  visible.value = false

  if (timeoutId) {
    clearTimeout(timeoutId)
    timeoutId = null
  }
}

function handleToast(event: Event): void {
  const customEvent =
      event as CustomEvent<{ message?: string }>

  const text =
      customEvent.detail?.message?.trim()

  if (!text) return

  showToast(text)
}

onMounted(() => {
  window.addEventListener(
      'rosha:toast',
      handleToast,
  )
})

onBeforeUnmount(() => {
  window.removeEventListener(
      'rosha:toast',
      handleToast,
  )

  if (timeoutId) {
    clearTimeout(timeoutId)
  }
})
</script>

<template>
  <Teleport to="body">
    <Transition name="toast">
      <div
          v-if="visible"
          class="app-toast"
          role="status"
          aria-live="polite"
      >
        <div class="app-toast__accent"></div>

        <div class="app-toast__icon">
          <AppIcon
              name="lock"
              :size="20"
          />
        </div>

        <div class="app-toast__content">
          <strong class="app-toast__title">
            دسترسی محدود است
          </strong>

          <p class="app-toast__message">
            {{ message }}
          </p>
        </div>

        <button
            type="button"
            class="app-toast__close"
            aria-label="بستن"
            @click="hideToast"
        >
          <AppIcon
              name="close"
              :size="17"
          />
        </button>

        <span class="app-toast__progress"></span>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.app-toast {
  position: fixed;
  top: 1.25rem;
  inset-inline-end: 1.25rem;
  z-index: 99999;

  display: flex;
  align-items: flex-start;
  gap: var(--space-3);

  width: min(25rem, calc(100vw - 2rem));
  min-height: 4.6rem;

  padding: var(--space-3) var(--space-3) var(--space-3) var(--space-4);

  overflow: hidden;

  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);

  background: linear-gradient(
      135deg,
      color-mix(
          in srgb,
          var(--color-surface-1) 94%,
          var(--color-primary) 6%
      ),
      var(--color-surface-2)
  );

  color: var(--color-text-primary);

  box-shadow: 0 1rem 2.5rem rgb(0 0 0 / 0.18),
  0 0 0 1px rgb(255 255 255 / 0.025);

  backdrop-filter: blur(1rem);
  -webkit-backdrop-filter: blur(1rem);
}

.app-toast__accent {
  position: absolute;
  inset-block: 0;
  inset-inline-start: 0;

  width: 3px;

  background: var(--color-primary);
}

.app-toast__icon {
  display: grid;
  place-items: center;

  width: 2.5rem;
  height: 2.5rem;
  flex: 0 0 auto;

  margin-top: 1px;

  border: 1px solid color-mix(
      in srgb,
      var(--color-primary) 22%,
      transparent
  );

  border-radius: 0.8rem;

  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.app-toast__content {
  min-width: 0;
  padding-top: 1px;
  padding-inline-end: 1.4rem;
}

.app-toast__title {
  display: block;

  margin-bottom: 0.15rem;

  color: var(--color-text-primary);

  font-size: var(--font-size-sm);
  font-weight: 700;
  line-height: 1.5;
}

.app-toast__message {
  margin: 0;

  color: var(--color-text-secondary);

  font-size: var(--font-size-xs);
  line-height: 1.7;
}

.app-toast__close {
  position: absolute;
  top: 0.65rem;
  inset-inline-end: 0.65rem;

  display: grid;
  place-items: center;

  width: 1.8rem;
  height: 1.8rem;

  padding: 0;

  border: 0;
  border-radius: 0.55rem;

  background: transparent;
  color: var(--color-text-muted);

  cursor: pointer;

  transition: background var(--transition-fast),
  color var(--transition-fast);
}

.app-toast__close:hover {
  background: var(--color-surface-2);
  color: var(--color-text-primary);
}

.app-toast__progress {
  position: absolute;
  inset-inline: 0;
  inset-block-end: 0;

  height: 2px;

  background: var(--color-primary);

  transform-origin: right center;

  animation: toast-progress 3s linear forwards;
}

/* ---------- Toast transition ---------- */

.toast-enter-active {
  transition: opacity 2000ms ease-out,
  transform 200ms ease-out;
}

.toast-leave-active {
  transition: opacity 300ms ease-in,
  transform 300ms ease-in;
}

.toast-enter-from {
  opacity: 0;
  transform: translateY(-8px);
}

.toast-enter-to {
  opacity: 1;
  transform: translateY(0);
}

.toast-leave-from {
  opacity: 1;
  transform: translateY(0);
}

.toast-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

@keyframes toast-progress {
  from {
    transform: scaleX(1);
  }

  to {
    transform: scaleX(0);
  }
}

@media (max-width: 640px) {
  .app-toast {
    top: 0.8rem;
    inset-inline: 0.8rem;

    width: auto;
  }
}
</style>