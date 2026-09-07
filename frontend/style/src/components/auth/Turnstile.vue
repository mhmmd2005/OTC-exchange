<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, defineExpose } from 'vue';

const props = defineProps<{
  siteKey: string
  theme?: 'auto' | 'light' | 'dark'
}>();

const emit = defineEmits<{ (e: 'update:token', v: string | null): void }>();

const el = ref<HTMLElement | null>(null);
let widgetId: any = null;

function renderWidget() {
  const w = (window as any);
  if (!el.value || !w.turnstile || widgetId !== null) return;
  widgetId = w.turnstile.render(el.value, {
    sitekey: props.siteKey,
    theme: props.theme || 'auto',
    callback: (token: string) => emit('update:token', token),
    'error-callback': () => emit('update:token', null),
    'expired-callback': () => emit('update:token', null),
    'timeout-callback': () => emit('update:token', null),
  });
}

onMounted(() => {
  const w = (window as any);
  if (w.turnstile) renderWidget();
  else {
    const t = setInterval(() => {
      if ((window as any).turnstile) {
        clearInterval(t);
        renderWidget();
      }
    }, 100);
  }
});

onBeforeUnmount(() => {
  try {
    if (widgetId !== null && (window as any).turnstile) {
      (window as any).turnstile.reset(widgetId);
    }
  } catch {}
});

function reset() {
  try {
    if (widgetId !== null && (window as any).turnstile) {
      (window as any).turnstile.reset(widgetId);
    }
  } catch {}
}
defineExpose({ reset });
</script>

<template>
  <div ref="el" style="min-height: 65px;"></div>
</template>
